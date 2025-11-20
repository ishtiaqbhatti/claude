"""
SSE (Server-Sent Events) Manager for real-time progress updates.

This module provides a singleton SSEManager that handles:
- Connection management for multiple concurrent scraping runs
- Progress updates and heartbeats
- Automatic cleanup of stale connections
- State replay for reconnections
"""
import asyncio
import logging
import json
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, AsyncIterator
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SSEConnection:
    """Represents an active SSE connection."""
    run_id: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed: bool = False
    final_results: Optional[Dict[str, Any]] = None


class SSEManager:
    """
    Singleton manager for Server-Sent Events connections.

    Manages multiple concurrent SSE connections for different scraping runs,
    handles message queuing, heartbeats, and automatic cleanup.
    """

    _instance: Optional["SSEManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize SSE manager (only once due to singleton)."""
        if self._initialized:
            return

        self._connections: Dict[str, SSEConnection] = {}
        self._status_history: Dict[str, list] = defaultdict(list)
        self._heartbeat_interval: int = 30  # seconds
        self._max_history_age: int = 3600  # 1 hour
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = True

        logger.info("SSEManager initialized")

    async def start_cleanup_task(self):
        """Start background task to cleanup stale connections."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Started SSE cleanup task")

    async def _periodic_cleanup(self):
        """Periodically clean up stale connections and old history."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_stale_connections(max_age_seconds=self._max_history_age)
            except asyncio.CancelledError:
                logger.info("SSE cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in SSE cleanup task: {e}", exc_info=True)

    async def connect(self, run_id: str) -> SSEConnection:
        """
        Establish a new SSE connection for a run.

        Args:
            run_id: Unique identifier for the scraping run

        Returns:
            SSEConnection object
        """
        async with self._lock:
            if run_id in self._connections:
                logger.debug(f"Reconnection for run_id={run_id}")
                connection = self._connections[run_id]
                connection.last_activity = datetime.now(UTC)
            else:
                logger.info(f"New SSE connection established: run_id={run_id}")
                connection = SSEConnection(run_id=run_id)
                self._connections[run_id] = connection

            return connection

    async def disconnect(self, run_id: str):
        """
        Disconnect and clean up a connection.

        Args:
            run_id: Unique identifier for the scraping run
        """
        async with self._lock:
            if run_id in self._connections:
                logger.info(f"SSE connection disconnected: run_id={run_id}")
                del self._connections[run_id]

    async def send_update(self, run_id: str, data: Dict[str, Any], event: str = "message"):
        """
        Send a generic update to a connection.

        Args:
            run_id: Unique identifier for the scraping run
            data: Data to send
            event: Event type (default: "message")
        """
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Store in history
        self._status_history[run_id].append(message)

        # Send to active connection if exists
        if run_id in self._connections:
            connection = self._connections[run_id]
            connection.last_activity = datetime.now(UTC)
            await connection.queue.put(message)
            logger.debug(f"Sent {event} to run_id={run_id}")

    async def send_scraping_progress(
        self,
        run_id: str,
        progress_percentage: float,
        current_item: str,
        total_items: int,
        processed_items: int,
        status_message: str,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Send scraping progress update.

        Args:
            run_id: Unique identifier for the scraping run
            progress_percentage: Progress as percentage (0-100)
            current_item: Current item being processed
            total_items: Total number of items
            processed_items: Number of items processed so far
            status_message: Human-readable status message
            additional_data: Optional additional data
        """
        data = {
            "progress_percentage": progress_percentage,
            "current_item": current_item,
            "total_items": total_items,
            "processed_items": processed_items,
            "status_message": status_message,
        }

        if additional_data:
            data.update(additional_data)

        await self.send_update(run_id, data, event="progress")

    async def send_completion(
        self,
        run_id: str,
        results: Dict[str, Any],
        status: str = "completed"
    ):
        """
        Send completion notification.

        Args:
            run_id: Unique identifier for the scraping run
            results: Final results data
            status: Completion status (completed, failed, etc.)
        """
        data = {
            "status": status,
            "results": results,
        }

        await self.send_update(run_id, data, event="complete")

        # Mark as completed
        if run_id in self._connections:
            connection = self._connections[run_id]
            connection.completed = True
            connection.final_results = results

        logger.info(f"Scraping run completed: run_id={run_id}, status={status}")

    async def send_error(
        self,
        run_id: str,
        error: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send error notification.

        Args:
            run_id: Unique identifier for the scraping run
            error: Error message
            status_code: HTTP status code
            details: Optional error details
        """
        data = {
            "error": error,
            "status_code": status_code,
        }

        if details:
            data["details"] = details

        await self.send_update(run_id, data, event="error")
        logger.error(f"Error sent to run_id={run_id}: {error}")

    async def stream_events(
        self,
        run_id: str,
        include_heartbeat: bool = True
    ) -> AsyncIterator[str]:
        """
        Stream SSE events for a specific run.

        Args:
            run_id: Unique identifier for the scraping run
            include_heartbeat: Whether to send periodic heartbeats

        Yields:
            SSE-formatted event strings
        """
        connection = await self.connect(run_id)

        # Send replay of any historical events
        if run_id in self._status_history:
            for message in self._status_history[run_id]:
                yield self._format_sse_message(message)

        try:
            last_heartbeat = datetime.now(UTC)

            while True:
                # Check for heartbeat
                if include_heartbeat:
                    now = datetime.now(UTC)
                    if (now - last_heartbeat).total_seconds() >= self._heartbeat_interval:
                        yield self._format_sse_message({
                            "event": "heartbeat",
                            "data": {"timestamp": now.isoformat()},
                            "timestamp": now.isoformat()
                        })
                        last_heartbeat = now

                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(
                        connection.queue.get(),
                        timeout=min(5.0, self._heartbeat_interval / 2)
                    )
                    yield self._format_sse_message(message)

                    # Check if completed
                    if message.get("event") == "complete":
                        logger.info(f"Stream completed for run_id={run_id}")
                        break

                except asyncio.TimeoutError:
                    # No message, continue to next heartbeat check
                    continue

        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for run_id={run_id}")
        except Exception as e:
            logger.error(f"Error streaming events for run_id={run_id}: {e}", exc_info=True)
            yield self._format_sse_message({
                "event": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now(UTC).isoformat()
            })
        finally:
            await self.disconnect(run_id)

    def _format_sse_message(self, message: Dict[str, Any]) -> str:
        """
        Format a message as SSE event.

        Args:
            message: Message dictionary with 'event', 'data', 'timestamp'

        Returns:
            SSE-formatted string
        """
        event = message.get("event", "message")
        data = message.get("data", {})

        # Build SSE message
        lines = []
        lines.append(f"event: {event}")
        lines.append(f"data: {json.dumps(data)}")
        lines.append("")  # Empty line to signal end of event

        return "\n".join(lines) + "\n"

    async def cleanup_stale_connections(self, max_age_seconds: int = 3600):
        """
        Clean up stale connections and old history.

        Args:
            max_age_seconds: Maximum age for connections/history in seconds
        """
        async with self._lock:
            now = datetime.now(UTC)
            cutoff = now - timedelta(seconds=max_age_seconds)

            # Clean up old connections
            stale_runs = [
                run_id for run_id, conn in self._connections.items()
                if conn.last_activity < cutoff or conn.completed
            ]

            for run_id in stale_runs:
                logger.info(f"Cleaning up stale connection: run_id={run_id}")
                del self._connections[run_id]

            # Clean up old history
            old_history = [
                run_id for run_id in self._status_history.keys()
                if run_id not in self._connections
            ]

            for run_id in old_history:
                # Keep only recent history
                if run_id in self._status_history:
                    messages = self._status_history[run_id]
                    recent_messages = [
                        msg for msg in messages
                        if datetime.fromisoformat(msg["timestamp"]) > cutoff
                    ]

                    if recent_messages:
                        self._status_history[run_id] = recent_messages
                    else:
                        del self._status_history[run_id]

            if stale_runs or old_history:
                logger.info(
                    f"Cleaned up {len(stale_runs)} stale connections "
                    f"and {len(old_history)} old histories"
                )

    def get_active_connections_count(self) -> int:
        """Get count of active SSE connections."""
        return len(self._connections)

    def get_connection_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.

        Args:
            run_id: Unique identifier for the scraping run

        Returns:
            Connection info dict or None if not found
        """
        if run_id not in self._connections:
            return None

        conn = self._connections[run_id]
        return {
            "run_id": conn.run_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_activity": conn.last_activity.isoformat(),
            "completed": conn.completed,
            "queue_size": conn.queue.qsize(),
        }

    async def has_active_run(self, run_id: str) -> bool:
        """
        Check if a run has an active SSE connection.

        Args:
            run_id: Unique identifier for the scraping run

        Returns:
            True if connection exists and is active
        """
        return run_id in self._connections


# Global singleton instance
sse_manager = SSEManager()
