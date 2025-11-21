import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Sparkles, Loader2 } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useDetailScrape } from '../hooks/useSSE';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from '../hooks/use-toast';
import { format } from 'date-fns';

export function JobDetail() {
  const { uid } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { selectedJob, fetchJobById, updateJob } = useStore();
  const { isRunning, startScrape, events } = useDetailScrape();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadJob = async () => {
      setIsLoading(true);
      await fetchJobById(uid);
      setIsLoading(false);
    };

    loadJob();
  }, [uid, fetchJobById]);

  // Auto-start scrape if scrape=true in URL (separate effect to avoid race condition)
  useEffect(() => {
    if (!isLoading && selectedJob && searchParams.get('scrape') === 'true' && selectedJob.status === 'discovered' && !isRunning) {
      const handleAutoScrape = async () => {
        await startScrape([uid]);
        toast({
          title: 'Auto-scraping started',
          description: 'Fetching job details...',
        });
      };
      handleAutoScrape();
    }
  }, [isLoading, selectedJob, searchParams, isRunning, uid, startScrape]);

  // Listen for scraping events
  useEffect(() => {
    events.forEach((event) => {
      if (event.type === 'job_completed' && event.data.job_uid === uid) {
        toast({
          title: 'Detail scraping completed',
          description: 'Job details have been enriched',
        });
        // Reload job data
        fetchJobById(uid);
      }
      if (event.type === 'run_failed') {
        toast({
          variant: 'destructive',
          title: 'Scraping failed',
          description: event.data.error || 'Failed to scrape job details',
        });
      }
    });
  }, [events]);

  const handleScrapeDetail = async () => {
    const result = await startScrape([uid], 1);
    if (result.success) {
      updateJob(uid, { status: 'scraping_detail' });
      toast({
        title: 'Scraping started',
        description: 'Fetching detailed job information...',
      });
    } else {
      toast({
        variant: 'destructive',
        title: 'Failed to start scraping',
        description: result.error,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!selectedJob) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-2">Job not found</h2>
        <p className="text-muted-foreground mb-4">
          The job you're looking for doesn't exist.
        </p>
        <Button onClick={() => navigate('/jobs')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Jobs
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/jobs')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Jobs
        </Button>
        <div className="flex gap-2">
          {selectedJob.url && (
            <Button variant="outline" asChild>
              <a href={selectedJob.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                View on Upwork
              </a>
            </Button>
          )}
          {selectedJob.status === 'discovered' && !isRunning && (
            <Button onClick={handleScrapeDetail}>
              <Sparkles className="mr-2 h-4 w-4" />
              Scrape Details
            </Button>
          )}
          {isRunning && (
            <Button disabled>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scraping...
            </Button>
          )}
        </div>
      </div>

      {/* Job Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl mb-2">{selectedJob.title}</CardTitle>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>UID: {selectedJob.uid}</span>
                <span>•</span>
                <span>Posted: {format(new Date(selectedJob.created_at), 'PPp')}</span>
              </div>
            </div>
            <Badge>{selectedJob.status}</Badge>
          </div>
        </CardHeader>
        {selectedJob.description && (
          <CardContent>
            <div className="prose max-w-none">
              <p className="whitespace-pre-wrap">{selectedJob.description}</p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Job Details Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Budget */}
        {selectedJob.budget && (
          <Card>
            <CardHeader>
              <CardTitle>Budget</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {selectedJob.budget.amount && (
                  <div>
                    <span className="text-2xl font-bold">${selectedJob.budget.amount}</span>
                  </div>
                )}
                {selectedJob.budget.min && selectedJob.budget.max && (
                  <div>
                    <span className="text-2xl font-bold">
                      ${selectedJob.budget.min} - ${selectedJob.budget.max}
                    </span>
                  </div>
                )}
                {selectedJob.budget.type && (
                  <div className="text-sm text-muted-foreground">
                    Type: {selectedJob.budget.type}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Skills */}
        {selectedJob.skills && selectedJob.skills.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Skills Required</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {selectedJob.skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary">
                    {skill.name || skill}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Client Information */}
        {selectedJob.client && (
          <Card>
            <CardHeader>
              <CardTitle>Client Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {selectedJob.client.name && (
                  <div>
                    <span className="font-medium">Name: </span>
                    <span>{selectedJob.client.name}</span>
                  </div>
                )}
                {selectedJob.client.location && (
                  <div>
                    <span className="font-medium">Location: </span>
                    <span>{selectedJob.client.location}</span>
                  </div>
                )}
                {selectedJob.client.rating && (
                  <div>
                    <span className="font-medium">Rating: </span>
                    <span>{selectedJob.client.rating} ⭐</span>
                  </div>
                )}
                {selectedJob.client.total_spent && (
                  <div>
                    <span className="font-medium">Total Spent: </span>
                    <span>${selectedJob.client.total_spent.toLocaleString()}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Additional Details */}
        <Card>
          <CardHeader>
            <CardTitle>Additional Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {selectedJob.category && (
                <div>
                  <span className="font-medium">Category: </span>
                  <span>{selectedJob.category}</span>
                </div>
              )}
              {selectedJob.subcategory && (
                <div>
                  <span className="font-medium">Subcategory: </span>
                  <span>{selectedJob.subcategory}</span>
                </div>
              )}
              {selectedJob.duration && (
                <div>
                  <span className="font-medium">Duration: </span>
                  <span>{selectedJob.duration}</span>
                </div>
              )}
              {selectedJob.experience_level && (
                <div>
                  <span className="font-medium">Experience Level: </span>
                  <Badge variant="outline">{selectedJob.experience_level}</Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
