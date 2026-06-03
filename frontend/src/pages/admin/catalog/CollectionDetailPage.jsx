import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Type,
  Link2,
  Trash2,
  Pencil,
  Library,
} from 'lucide-react';
import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/feedback/alert-dialog';
import { DetailSkeleton } from '@/components/ui/feedback/page-skeleton';
import { Button } from '@/components/ui/forms/button';
import { BreadcrumbNav } from '@/components/ui/navigation/breadcrumb-nav';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/overlays/dialog';
import { collectionApi } from '@/lib/apiClient';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-MY', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function generateSlug(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .substring(0, 60);
}

export default function CollectionDetailPage() {
  const { collectionId } = useParams();
  const navigate = useNavigate();

  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [editDialog, setEditDialog] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editName, setEditName] = useState('');
  const [editSlug, setEditSlug] = useState('');
  const [autoSlug, setAutoSlug] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await collectionApi.viewCollectionDetailApiAppV1CollectionsCollectionIdGet({
        collectionId,
      });
      setCollection(res.data);
    } catch (err) {
      console.error('Failed to load collection:', err);
      setError('Failed to load collection');
    } finally {
      setLoading(false);
    }
  }, [collectionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openEditDialog = () => {
    if (!collection) return;
    setEditName(collection.name);
    setEditSlug(collection.urlSlug);
    setAutoSlug(false);
    setEditDialog(true);
  };

  const handleEditNameChange = (e) => {
    const val = e.target.value;
    setEditName(val);
    if (autoSlug) {
      setEditSlug(generateSlug(val));
    }
  };

  const handleEditSubmit = async () => {
    if (!editName.trim()) {
      toast.error('Name is required');
      return;
    }
    if (!editSlug.trim()) {
      toast.error('URL slug is required');
      return;
    }
    setEditLoading(true);
    try {
      await collectionApi.updateCollectionApiAppV1CollectionsCollectionIdPatch({
        collectionId,
        updateCollectionRequest: {
          name: editName.trim(),
          urlSlug: editSlug.trim(),
        },
      });
      toast.success('Collection updated');
      setEditDialog(false);
      loadData();
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Update failed';
      toast.error(msg);
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await collectionApi.softDeleteCollection({ collectionId });
      toast.success(`"${collection?.name}" deleted`);
      setDeleteDialog(false);
      navigate('/admin/collections');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return <DetailSkeleton sections={2} />;
  }

  if (error || !collection) {
    return (
      <div className='space-y-8'>
        <Link
          to='/admin/collections'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Collections
        </Link>
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>
            {error || 'Collection not found'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-8 '>
      <BreadcrumbNav />

      <Link
        to='/admin/collections'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Collections
      </Link>

      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          {collection.name}
        </h1>
        <p className='text-primary/40 font-bold italic text-sm font-mono'>{collection.urlSlug}</p>
      </div>

      {/* Details */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Collection Info
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Type className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Name</p>
                  <p className='text-sm font-sans font-bold text-primary'>{collection.name}</p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Link2 className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>URL Slug</p>
                  <p className='text-sm font-mono font-bold text-primary'>{collection.urlSlug}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Activity
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Library className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Categories</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {collection.categories?.length || 0}
                  </p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Library className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Created</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(collection.createdAt)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Categories List */}
      {collection.categories && collection.categories.length > 0 && (
        <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
          <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
            Categories
          </h3>
          <div className='space-y-2'>
            {collection.categories.map((cat) => (
              <div
                key={cat.id}
                className='flex items-center justify-between p-3 bg-white/60 rounded-2xl'>
                <div>
                  <p className='text-sm font-sans font-bold text-primary'>{cat.name}</p>
                  <p className='text-xs font-mono text-primary/40'>{cat.urlSlug}</p>
                </div>
                <Link
                  to={`/admin/categories/${cat.id}`}
                  className='text-xs font-bold text-primary/40 hover:text-primary transition-colors'>
                  View →
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
        <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
          Actions
        </h3>
        <div className='flex flex-wrap gap-3'>
          <Button
            variant='outline'
            onClick={openEditDialog}
            className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest'>
            <Pencil className='w-4 h-4' />
            Edit Collection
          </Button>
          <Button
            variant='outline'
            onClick={() => setDeleteDialog(true)}
            className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest border-destructive/20 text-destructive hover:bg-destructive/5'>
            <Trash2 className='w-4 h-4' />
            Delete Collection
          </Button>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onOpenChange={setEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Collection</DialogTitle>
          </DialogHeader>
          <div className='space-y-4 py-4'>
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Name
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Type className='w-5 h-5 text-primary/30' />
                </div>
                <input
                  type='text'
                  value={editName}
                  onChange={handleEditNameChange}
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
                />
              </div>
            </div>
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                URL Slug
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Link2 className='w-5 h-5 text-primary/30' />
                </div>
                <input
                  type='text'
                  value={editSlug}
                  onChange={(e) => {
                    setEditSlug(e.target.value);
                    setAutoSlug(false);
                  }}
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm font-mono'
                />
              </div>
              <p className='text-xs text-primary/30 pl-1'>
                Auto-generated from name. Edit if needed.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant='outline' onClick={() => setEditDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleEditSubmit}
              disabled={editLoading}
              className='bg-primary text-secondary'>
              {editLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className='text-destructive'>Delete Collection?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{collection.name}&quot; and all its categories.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className='bg-destructive text-white'>
              {deleteLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Delete Collection'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
