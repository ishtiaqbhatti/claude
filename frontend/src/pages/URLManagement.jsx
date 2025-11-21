import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Power, PowerOff } from 'lucide-react';
import { useStore } from '../store/useStore';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { toast } from '../hooks/use-toast';
import { format } from 'date-fns';

export function URLManagement() {
  const { urls, urlsLoading, urlStats, fetchUrls, fetchUrlStats, createUrl, updateUrl, deleteUrl, toggleUrl } = useStore();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingUrl, setEditingUrl] = useState(null);
  const [formData, setFormData] = useState({
    url: '',
    name: '',
    enabled: true,
  });

  useEffect(() => {
    fetchUrls();
    fetchUrlStats();
  }, [fetchUrls, fetchUrlStats]);

  const handleCreate = async (e) => {
    e.preventDefault();
    const result = await createUrl(formData);
    if (result.success) {
      toast({
        title: 'Success',
        description: 'URL created successfully',
      });
      setIsCreateDialogOpen(false);
      setFormData({ url: '', name: '', enabled: true });
    } else {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: result.error || 'Failed to create URL',
      });
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    const result = await updateUrl(editingUrl.id, {
      name: formData.name,
      enabled: formData.enabled,
    });
    if (result.success) {
      toast({
        title: 'Success',
        description: 'URL updated successfully',
      });
      setIsEditDialogOpen(false);
      setEditingUrl(null);
      setFormData({ url: '', name: '', enabled: true });
    } else {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: result.error || 'Failed to update URL',
      });
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this URL?')) return;

    const result = await deleteUrl(id);
    if (result.success) {
      toast({
        title: 'Success',
        description: 'URL deleted successfully',
      });
    } else {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: result.error || 'Failed to delete URL',
      });
    }
  };

  const handleToggle = async (id) => {
    const result = await toggleUrl(id);
    if (result.success) {
      toast({
        title: 'Success',
        description: 'URL status updated',
      });
    } else {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: result.error || 'Failed to toggle URL',
      });
    }
  };

  const openEditDialog = (url) => {
    setEditingUrl(url);
    setFormData({
      url: url.url,
      name: url.name,
      enabled: url.enabled,
    });
    setIsEditDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">URL Management</h1>
          <p className="text-muted-foreground">Manage your Upwork search URLs</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add URL
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Search URL</DialogTitle>
              <DialogDescription>
                Add a new Upwork search page URL to scrape jobs from.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate}>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="url">URL</Label>
                  <Input
                    id="url"
                    placeholder="https://www.upwork.com/nx/search/jobs/?q=..."
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., React Developer Jobs"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="enabled"
                    checked={formData.enabled}
                    onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
                  />
                  <Label htmlFor="enabled">Enabled</Label>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Create URL</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      {urlStats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total URLs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{urlStats.total_urls}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Enabled URLs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{urlStats.enabled_urls}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs Found</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{urlStats.total_jobs_found}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* URLs List */}
      <Card>
        <CardHeader>
          <CardTitle>Search URLs</CardTitle>
          <CardDescription>
            Your configured Upwork search URLs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {urlsLoading ? (
            <div className="text-center py-8">Loading...</div>
          ) : urls.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No URLs configured. Add your first search URL to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {urls.map((url) => (
                <div
                  key={url.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">{url.name}</h3>
                      <Badge variant={url.enabled ? 'default' : 'secondary'}>
                        {url.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{url.url}</p>
                    <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                      <span>Jobs found: {url.total_jobs_found}</span>
                      {url.last_scraped_at && (
                        <span>Last scraped: {format(new Date(url.last_scraped_at), 'PPp')}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleToggle(url.id)}
                      title={url.enabled ? 'Disable' : 'Enable'}
                    >
                      {url.enabled ? (
                        <Power className="h-4 w-4 text-green-600" />
                      ) : (
                        <PowerOff className="h-4 w-4 text-gray-400" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => openEditDialog(url)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(url.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Search URL</DialogTitle>
            <DialogDescription>
              Update the details of this search URL.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEdit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-url">URL</Label>
                <Input
                  id="edit-url"
                  value={formData.url}
                  disabled
                  className="bg-muted"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-enabled"
                  checked={formData.enabled}
                  onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
                />
                <Label htmlFor="edit-enabled">Enabled</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="submit">Update URL</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
