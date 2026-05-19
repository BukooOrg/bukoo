import { Users, Plus, Pencil, Trash2, Loader2, AlertCircle } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { Button } from '@/components/ui/forms/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/overlays/dialog';
import { authorApi } from '@/lib/apiClient';

export default function AuthorsPage() {
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [biography, setBiography] = useState('');
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchAuthors = async () => {
    setLoading(true);
    try {
      const res = await authorApi.findAuthors({});
      setAuthors(res.data?.items || []);
    } catch {
      setError('Failed to load authors');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuthors();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError('');
    try {
      await authorApi.createAuthor({
        createAuthorRequest: {
          name: name.trim(),
          biography: biography.trim() || undefined,
        },
      });
      toast.success(`Author "${name}" created`);
      setShowCreate(false);
      setName('');
      setBiography('');
      fetchAuthors();
    } catch (err) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to create');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await authorApi.softDeleteAuthor({ authorId: deleteTarget.id });
      toast.success(`"${deleteTarget.name}" deleted`);
      setDeleteTarget(null);
      fetchAuthors();
    } catch (err) {
      toast.error(err?.response?.data?.error?.message || 'Delete failed');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Authors
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>{authors.length} authors</p>
      </div>

      <div className='flex justify-end'>
        <Button
          onClick={() => setShowCreate(true)}
          className='gap-2 font-sans font-bold uppercase tracking-[0.1em] bg-primary text-secondary rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
          <Plus className='w-4 h-4' />
          New Author
        </Button>
      </div>

      {error && (
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
        </div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className='max-w-lg mx-auto space-y-4 p-6 bg-white border rounded-2xl border-primary/5'>
          <h2 className='font-serif text-xl font-black tracking-tighter text-primary'>
            New Author
          </h2>
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Name
            </label>
            <input
              type='text'
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder='Jane Austen'
              className='w-full px-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 font-sans font-bold'
            />
          </div>
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Biography
            </label>
            <textarea
              value={biography}
              onChange={(e) => setBiography(e.target.value)}
              placeholder='Optional biography...'
              rows={3}
              className='w-full px-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 font-sans font-bold resize-none'
            />
          </div>
          <div className='flex gap-3'>
            <Button
              type='button'
              variant='outline'
              onClick={() => setShowCreate(false)}
              className='flex-1 rounded-xl font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              Cancel
            </Button>
            <Button
              type='submit'
              disabled={creating}
              className='flex-1 rounded-xl bg-primary text-secondary font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              {creating ? <Loader2 className='w-4 h-4 animate-spin mx-auto' /> : 'Create'}
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div className='animate-pulse space-y-3'>
          {[...Array(6)].map((_, i) => (
            <div key={i} className='h-14 bg-primary/5 rounded-xl' />
          ))}
        </div>
      ) : (
        <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Biography</TableHead>
                <TableHead className='w-24 text-right'>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {authors.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className='py-16 text-center'>
                    <Users className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                    <p className='font-serif text-lg italic text-primary/30'>No authors yet</p>
                  </TableCell>
                </TableRow>
              ) : (
                authors.map((author) => (
                  <TableRow key={author.id}>
                    <TableCell className='font-sans font-bold text-primary'>
                      <Link to={`/admin/authors/${author.id}`} className='hover:text-primary/70'>
                        {author.name}
                      </Link>
                    </TableCell>
                    <TableCell className='text-sm text-primary/40 truncate max-w-xs'>
                      {author.biography || '—'}
                    </TableCell>
                    <TableCell className='text-right'>
                      <div className='flex items-center justify-end gap-1'>
                        <Link to={`/admin/authors/${author.id}`}>
                          <Button
                            variant='ghost'
                            size='icon'
                            className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                            <Pencil className='w-4 h-4' />
                          </Button>
                        </Link>
                        <Button
                          variant='ghost'
                          size='icon'
                          onClick={() => setDeleteTarget(author)}
                          className='w-8 h-8 rounded-lg text-primary/40 hover:text-destructive hover:bg-destructive/5'>
                          <Trash2 className='w-4 h-4' />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent className='sm:max-w-md'>
          <DialogHeader>
            <DialogTitle className='font-serif text-xl font-black tracking-tighter text-destructive'>
              Delete Author
            </DialogTitle>
            <DialogDescription className='font-sans text-sm text-primary/60'>
              Delete &ldquo;{deleteTarget?.name}&rdquo;?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className='gap-2'>
            <Button
              variant='outline'
              onClick={() => setDeleteTarget(null)}
              className='rounded-xl font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              Cancel
            </Button>
            <Button
              variant='destructive'
              onClick={handleDelete}
              disabled={deleteLoading}
              className='gap-2 rounded-xl font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              {deleteLoading ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Trash2 className='w-4 h-4' />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
