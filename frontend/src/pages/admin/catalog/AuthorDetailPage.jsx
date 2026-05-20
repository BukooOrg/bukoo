import { ArrowLeft, Loader2, AlertCircle, Type, Trash2, Pencil, Users } from 'lucide-react';
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
import { authorApi } from '@/lib/apiClient';

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

export default function AuthorDetailPage() {
  const { authorId } = useParams();
  const navigate = useNavigate();

  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Delete dialog
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Edit dialog
  const [editDialog, setEditDialog] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editName, setEditName] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await authorApi.viewAuthorDetail({ authorId });
      setAuthor(res.data);
    } catch (err) {
      console.error('Failed to load author:', err);
      setError('Failed to load author');
    } finally {
      setLoading(false);
    }
  }, [authorId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openEditDialog = () => {
    if (!author) return;
    setEditName(author.name);
    setEditDialog(true);
  };

  const handleEditSubmit = async () => {
    if (!editName.trim()) {
      toast.error('Name is required');
      return;
    }
    setEditLoading(true);
    try {
      await authorApi.updateAuthor({
        authorId,
        updateAuthorRequest: {
          name: editName.trim(),
        },
      });
      toast.success('Author updated');
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
      await authorApi.softDeleteAuthor({ authorId });
      toast.success(`"${author?.name}" deleted`);
      setDeleteDialog(false);
      navigate('/admin/authors');
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

  if (error || !author) {
    return (
      <div className='space-y-8'>
        <Link
          to='/admin/authors'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Authors
        </Link>
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>
            {error || 'Author not found'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-8 max-w-4xl'>
      <BreadcrumbNav />

      <Link
        to='/admin/authors'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Authors
      </Link>

      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          {author.name}
        </h1>
      </div>

      {/* Details */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Author Info
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Type className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Name</p>
                  <p className='text-sm font-sans font-bold text-primary'>{author.name}</p>
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
                <Users className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Created</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(author.createdAt)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
        <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
          Actions
        </h3>
        <div className='flex flex-wrap gap-3'>
          <Button
            variant='outline'
            onClick={openEditDialog}
            className='gap-2 rounded-xl text-xs font-bold uppercase tracking-widest'>
            <Pencil className='w-4 h-4' />
            Edit Author
          </Button>
          <Button
            variant='outline'
            onClick={() => setDeleteDialog(true)}
            className='gap-2 rounded-xl text-xs font-bold uppercase tracking-widest border-destructive/20 text-destructive hover:bg-destructive/5'>
            <Trash2 className='w-4 h-4' />
            Delete Author
          </Button>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onOpenChange={setEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Author</DialogTitle>
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
                  onChange={(e) => setEditName(e.target.value)}
                  className='w-full pl-12 pr-4 py-3 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
                />
              </div>
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
            <AlertDialogTitle className='text-destructive'>Delete Author?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{author.name}&quot;. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className='bg-destructive text-white'>
              {deleteLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Delete Author'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
