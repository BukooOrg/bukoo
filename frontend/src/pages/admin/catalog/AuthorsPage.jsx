import {
  Plus,
  AlertCircle,
  Loader2,
  Users,
  Eye,
  Trash2,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import React, { useState, useCallback, useRef, useEffect } from 'react';
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
import { Button } from '@/components/ui/forms/button';
import { authorApi } from '@/lib/apiClient';

export default function AuthorsPage() {
  const [authors, setAuthors] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [targetAuthor, setTargetAuthor] = useState(null);
  const searchTimeout = useRef(null);
  const searchTerm = useRef('');

  const fetchData = useCallback(async (searchTerm, pageNum) => {
    setLoading(true);
    setError('');
    try {
      const res = await authorApi.findAuthors({
        search: searchTerm || undefined,
        page: pageNum,
        pageSize: 20,
        sort: 'name:asc',
      });
      setAuthors(res.data?.items || []);
      setPagination(res.data?.pagination || null);
    } catch (err) {
      console.error('Failed to load authors:', err);
      setError('Failed to load authors');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(searchTerm.current, page);
  }, [page, fetchData]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    searchTerm.current = val;
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchData(val, 1);
    }, 400);
  };

  const handleDeleteClick = (author) => {
    setTargetAuthor(author);
    setDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!targetAuthor) return;
    setDeletingId(targetAuthor.id);
    try {
      await authorApi.softDeleteAuthor({ authorId: targetAuthor.id });
      toast.success(`"${targetAuthor.name}" deleted`);
      setDeleteDialog(false);
      setTargetAuthor(null);
      fetchData(searchTerm.current, page);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeletingId(null);
    }
  };

  const pageCount = pagination?.totalPages || 1;
  const hasPrev = page > 1;
  const hasNext = page < pageCount;

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Authors
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          {pagination ? `${pagination.totalItems} authors total` : 'Manage authors'}
        </p>
      </div>

      {/* Top bar — search + create */}
      <div className='flex flex-wrap items-center justify-end gap-3'>
        <div className='relative w-full max-w-sm'>
          <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
            <Search className='w-4 h-4 text-primary/30' />
          </div>
          <input
            type='text'
            value={search}
            onChange={handleSearchChange}
            placeholder='Search authors...'
            className='w-full pl-10 pr-4 py-2.5 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
          />
        </div>
        <Link to='/admin/authors/new'>
          <Button className='gap-2 font-sans font-bold uppercase tracking-[0.1em] bg-primary text-secondary rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
            <Plus className='w-4 h-4' />
            New Author
          </Button>
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className='animate-pulse space-y-3'>
          {[...Array(6)].map((_, i) => (
            <div key={i} className='h-14 bg-primary/5 rounded-xl' />
          ))}
        </div>
      ) : (
        <>
          <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className='w-28 text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {authors.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className='py-16 text-center'>
                      <Users className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                      <p className='font-serif text-lg italic text-primary/30'>No authors found</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  authors.map((author) => (
                    <TableRow key={author.id}>
                      <TableCell>
                        <Link
                          to={`/admin/authors/${author.id}`}
                          className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                          {author.name}
                        </Link>
                      </TableCell>
                      <TableCell className='text-primary/60 text-sm'>
                        {author.createdAt
                          ? new Date(author.createdAt).toLocaleDateString('en-MY', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })
                          : '—'}
                      </TableCell>
                      <TableCell className='text-right'>
                        <div className='flex items-center justify-end gap-1'>
                          <Link to={`/admin/authors/${author.id}`}>
                            <Button
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                              <Eye className='w-4 h-4' />
                            </Button>
                          </Link>
                          <Button
                            variant='ghost'
                            size='icon'
                            onClick={() => handleDeleteClick(author)}
                            disabled={deletingId === author.id}
                            className='w-8 h-8 rounded-lg text-primary/40 hover:text-destructive hover:bg-destructive/5'>
                            {deletingId === author.id ? (
                              <Loader2 className='w-4 h-4 animate-spin' />
                            ) : (
                              <Trash2 className='w-4 h-4' />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {pagination && pageCount > 1 && (
            <div className='flex items-center justify-between'>
              <p className='text-xs font-bold text-primary/40'>
                Page {page} of {pageCount}
              </p>
              <div className='flex gap-1'>
                <Button
                  variant='outline'
                  size='sm'
                  disabled={!hasPrev}
                  onClick={() => setPage(page - 1)}
                  className='gap-1 rounded-xl'>
                  <ChevronLeft className='w-4 h-4' />
                  Previous
                </Button>
                <Button
                  variant='outline'
                  size='sm'
                  disabled={!hasNext}
                  onClick={() => setPage(page + 1)}
                  className='gap-1 rounded-xl'>
                  Next
                  <ChevronRight className='w-4 h-4' />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className='text-destructive'>Delete Author?</AlertDialogTitle>
            <AlertDialogDescription>
              This will delete &quot;{targetAuthor?.name}&quot;. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deletingId !== null}
              className='bg-destructive text-white'>
              {deletingId !== null ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Delete Author'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
