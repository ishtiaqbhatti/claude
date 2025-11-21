import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table';
import { ArrowUpDown, Eye, Sparkles } from 'lucide-react';
import { useStore } from '../store/useStore';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { format } from 'date-fns';
import { toast } from '../hooks/use-toast';

export function Jobs() {
  const navigate = useNavigate();
  const { jobs, jobsLoading, jobStats, fetchJobs, fetchJobStats } = useStore();
  const [globalFilter, setGlobalFilter] = useState('');

  useEffect(() => {
    fetchJobs({ page: 1, page_size: 100 });
    fetchJobStats();
  }, [fetchJobs, fetchJobStats]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'title',
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            >
              Title
              <ArrowUpDown className="ml-2 h-4 w-4" />
            </Button>
          );
        },
        cell: ({ row }) => (
          <div className="max-w-md">
            <div className="font-medium truncate">{row.original.title}</div>
            <div className="text-xs text-muted-foreground truncate">
              {row.original.uid}
            </div>
          </div>
        ),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => {
          const status = row.original.status;
          const variants = {
            discovered: 'secondary',
            enriched: 'default',
            scraping_detail: 'outline',
            detail_failed: 'destructive',
          };
          return (
            <Badge variant={variants[status] || 'secondary'}>
              {status}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'budget',
        header: 'Budget',
        cell: ({ row }) => {
          const budget = row.original.budget;
          if (!budget) return '-';
          if (budget.amount) {
            return `$${budget.amount}`;
          }
          if (budget.min && budget.max) {
            return `$${budget.min} - $${budget.max}`;
          }
          return budget.type || '-';
        },
      },
      {
        accessorKey: 'skills',
        header: 'Skills',
        cell: ({ row }) => {
          const skills = row.original.skills || [];
          if (skills.length === 0) return '-';
          return (
            <div className="flex flex-wrap gap-1">
              {skills.slice(0, 3).map((skill, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {skill.name || skill}
                </Badge>
              ))}
              {skills.length > 3 && (
                <span className="text-xs text-muted-foreground">
                  +{skills.length - 3} more
                </span>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'created_at',
        header: ({ column }) => {
          return (
            <Button
              variant="ghost"
              onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            >
              Discovered
              <ArrowUpDown className="ml-2 h-4 w-4" />
            </Button>
          );
        },
        cell: ({ row }) => {
          return format(new Date(row.original.created_at), 'PPp');
        },
      },
      {
        id: 'actions',
        cell: ({ row }) => {
          return (
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/jobs/${row.original.uid}`)}
              >
                <Eye className="h-4 w-4 mr-1" />
                View
              </Button>
              {row.original.status === 'discovered' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleScrapeDetail(row.original.uid)}
                >
                  <Sparkles className="h-4 w-4 mr-1" />
                  Scrape
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [navigate]
  );

  const table = useReactTable({
    data: jobs,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  const handleScrapeDetail = async (uid) => {
    toast({
      title: 'Scraping job details...',
      description: `Starting detail scrape for job ${uid}`,
    });
    // This will be handled by the detail scraping functionality
    navigate(`/jobs/${uid}?scrape=true`);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Jobs</h1>
        <p className="text-muted-foreground">Browse and manage scraped Upwork jobs</p>
      </div>

      {/* Stats Cards */}
      {jobStats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{jobStats.total_jobs}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Discovered</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{jobStats.by_status?.discovered || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Enriched</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{jobStats.by_status?.enriched || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(jobStats.by_status?.detail_failed || 0) + (jobStats.by_status?.extraction_failed || 0)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Jobs</CardTitle>
              <CardDescription>
                {jobs.length} jobs found
              </CardDescription>
            </div>
            <div className="w-64">
              <Input
                placeholder="Search jobs..."
                value={globalFilter ?? ''}
                onChange={(e) => setGlobalFilter(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {jobsLoading ? (
            <div className="text-center py-8">Loading...</div>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>
                  <TableBody>
                    {table.getRowModel().rows?.length ? (
                      table.getRowModel().rows.map((row) => (
                        <TableRow
                          key={row.id}
                          data-state={row.getIsSelected() && 'selected'}
                        >
                          {row.getVisibleCells().map((cell) => (
                            <TableCell key={cell.id}>
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell
                          colSpan={columns.length}
                          className="h-24 text-center"
                        >
                          No jobs found.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between space-x-2 py-4">
                <div className="text-sm text-muted-foreground">
                  Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
                  {Math.min(
                    (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                    jobs.length
                  )}{' '}
                  of {jobs.length} jobs
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
