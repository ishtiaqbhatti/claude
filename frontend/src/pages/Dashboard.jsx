import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PlayCircle, Loader2, Database, Link as LinkIcon, Briefcase } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useSearchScrape, useDetailScrape } from '../hooks/useSSE';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from '../hooks/use-toast';

export function Dashboard() {
  const {
    urls,
    jobs,
    urlStats,
    jobStats,
    fetchUrls,
    fetchJobs,
    fetchUrlStats,
    fetchJobStats,
    addJob,
    updateJob,
  } = useStore();

  const searchScrape = useSearchScrape();
  const detailScrape = useDetailScrape();

  useEffect(() => {
    fetchUrlStats();
    fetchJobStats();
    fetchUrls({ enabled_only: true });
    fetchJobs({ page: 1, page_size: 10, sort_order: 'desc' });
  }, [fetchUrlStats, fetchJobStats, fetchUrls, fetchJobs]);

  // Handle search scrape events
  useEffect(() => {
    searchScrape.events.forEach((event) => {
      if (event.type === 'url_started') {
        toast({
          title: 'Scraping URL',
          description: `Processing: ${event.data.url_name || event.data.url}`,
        });
      }
      if (event.type === 'url_completed') {
        toast({
          title: 'URL Completed',
          description: `Found ${event.data.jobs_found || 0} jobs`,
        });
        // Refresh stats
        fetchJobStats();
      }
      if (event.type === 'run_completed') {
        toast({
          title: 'Scraping Complete',
          description: `Successfully scraped ${event.data.urls_scraped || 0} URLs`,
        });
        fetchJobs({ page: 1, page_size: 10, sort_order: 'desc' });
        fetchUrlStats();
      }
    });
  }, [searchScrape.events]);

  // Handle detail scrape events
  useEffect(() => {
    detailScrape.events.forEach((event) => {
      if (event.type === 'job_started') {
        const uid = event.data.job_uid;
        updateJob(uid, { status: 'scraping_detail' });
      }
      if (event.type === 'job_completed') {
        const uid = event.data.job_uid;
        updateJob(uid, { status: 'enriched' });
        toast({
          title: 'Job Enriched',
          description: `Job ${uid} has been enriched with details`,
        });
      }
      if (event.type === 'run_completed') {
        toast({
          title: 'Detail Scraping Complete',
          description: `Successfully enriched ${event.data.jobs_enriched || 0} jobs`,
        });
        fetchJobStats();
      }
    });
  }, [detailScrape.events]);

  const handleStartSearchScrape = async () => {
    if (urls.length === 0) {
      toast({
        variant: 'destructive',
        title: 'No URLs configured',
        description: 'Please add at least one search URL before scraping',
      });
      return;
    }

    const result = await searchScrape.startScrape();
    if (!result.success) {
      toast({
        variant: 'destructive',
        title: 'Failed to start scraping',
        description: result.error,
      });
    }
  };

  const handleStartDetailScrape = async () => {
    const result = await detailScrape.startScrape(null, 50);
    if (!result.success) {
      toast({
        variant: 'destructive',
        title: 'Failed to start detail scraping',
        description: result.error,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to Upwork Scraper - Monitor and manage your job scraping
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total URLs</CardTitle>
            <LinkIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{urlStats?.total_urls || 0}</div>
            <p className="text-xs text-muted-foreground">
              {urlStats?.enabled_urls || 0} enabled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobStats?.total_jobs || 0}</div>
            <p className="text-xs text-muted-foreground">
              {jobStats?.by_status?.discovered || 0} discovered
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enriched Jobs</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobStats?.by_status?.enriched || 0}</div>
            <p className="text-xs text-muted-foreground">
              With full details
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Scraping Controls */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Search Scraping</CardTitle>
            <CardDescription>
              Scrape jobs from configured search page URLs
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Enabled URLs</div>
                <div className="text-2xl font-bold">{urlStats?.enabled_urls || 0}</div>
              </div>
              <Button
                size="lg"
                onClick={handleStartSearchScrape}
                disabled={searchScrape.isRunning || (urlStats?.enabled_urls || 0) === 0}
              >
                {searchScrape.isRunning ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  <>
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Start Search Scrape
                  </>
                )}
              </Button>
            </div>

            {searchScrape.isRunning && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Progress</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          searchScrape.progress.total > 0
                            ? (searchScrape.progress.completed / searchScrape.progress.total) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {searchScrape.progress.completed} / {searchScrape.progress.total}
                  </span>
                </div>
                {searchScrape.progress.current && (
                  <div className="text-xs text-muted-foreground truncate">
                    Current: {searchScrape.progress.current}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Detail Scraping</CardTitle>
            <CardDescription>
              Enrich discovered jobs with detailed information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Jobs Pending Enrichment</div>
                <div className="text-2xl font-bold">{jobStats?.by_status?.discovered || 0}</div>
              </div>
              <Button
                size="lg"
                onClick={handleStartDetailScrape}
                disabled={detailScrape.isRunning || (jobStats?.by_status?.discovered || 0) === 0}
              >
                {detailScrape.isRunning ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  <>
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Start Detail Scrape
                  </>
                )}
              </Button>
            </div>

            {detailScrape.isRunning && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Progress</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          detailScrape.progress.total > 0
                            ? (detailScrape.progress.completed / detailScrape.progress.total) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {detailScrape.progress.completed} / {detailScrape.progress.total}
                  </span>
                </div>
                {detailScrape.progress.current && (
                  <div className="text-xs text-muted-foreground truncate">
                    Current: {detailScrape.progress.current}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Jobs</CardTitle>
              <CardDescription>Latest discovered jobs</CardDescription>
            </div>
            <Link to="/jobs">
              <Button variant="outline" size="sm">View All</Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No jobs yet. Start a search scrape to discover jobs.
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.slice(0, 5).map((job) => (
                <Link
                  key={job.uid}
                  to={`/jobs/${job.uid}`}
                  className="block p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{job.title}</div>
                      <div className="text-sm text-muted-foreground truncate">
                        {job.uid}
                      </div>
                    </div>
                    <Badge variant={job.status === 'enriched' ? 'default' : 'secondary'}>
                      {job.status}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
