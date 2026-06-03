import {
  Search,
  Plus,
  Pencil,
  Trash2,
  Power,
  AlertCircle,
  Loader2,
  BookOpen,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/data-display/badge';
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
import { bookApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

function formatBookPrice(price) {
  if (!price) return '—';
  const num = parseFloat(price);
  if (isNaN(num)) return price;
  return new Intl.NumberFormat('ms-MY', { style: 'currency', currency: 'MYR' }).format(num);
}

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'activate', label: 'Active' },
  { value: 'deactivate', label: 'Inactive' },
];

export default function BooksPage() {
  const [books, setBooks] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('all');
  const [actionLoading, setActionLoading] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const searchTimeout = useRef(null);
  const searchTerm = useRef('');

  const fetchBooks = useCallback(async (searchVal, pageNum, statusVal) => {
    setLoading(true);
    setError('');
    try {
      const res = await bookApi.findBooks({
        status: statusVal,
        page: pageNum,
        pageSize: 20,
        search: searchVal || undefined,
      });
      setBooks(res.data?.items || []);
      setPagination(res.data?.pagination || null);
    } catch (err) {
      console.error('Failed to load books:', err);
      setError('Failed to load books');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBooks(searchTerm.current, page, status);
  }, [page, status, fetchBooks]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    searchTerm.current = val;
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchBooks(val, 1, status);
    }, 400);
  };

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleToggleActive = async (book) => {
    setActionLoading(book.id);
    try {
      if (book.isActive) {
        await bookApi.deactivateBook({ bookId: book.id });
        toast.success(`"${book.title}" deactivated`);
      } else {
        await bookApi.activateBook({ bookId: book.id });
        toast.success(`"${book.title}" activated`);
      }
      fetchBooks(searchTerm.current, page, status);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Action failed';
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await bookApi.softDeleteBook({ bookId: deleteTarget.id });
      toast.success(`"${deleteTarget.title}" deleted`);
      setDeleteTarget(null);
      fetchBooks(searchTerm.current, page, status);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  const pageCount = pagination?.totalPages || 1;
  const hasPrev = page > 1;
  const hasNext = page < pageCount;

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>Books</h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          {pagination ? `${pagination.totalItems} books total` : 'Manage the book catalog'}
        </p>
      </div>

      {/* Top bar — filters + actions */}
      <div className='flex flex-wrap items-center justify-end gap-3'>
        <div className='flex p-1 bg-primary/5 rounded-2xl'>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleStatusChange(opt.value)}
              className={cn(
                'px-4 py-2 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all',
                status === opt.value
                  ? 'bg-white shadow-sm text-primary'
                  : 'text-primary/40 hover:text-primary/60'
              )}>
              {opt.label}
            </button>
          ))}
        </div>
        <Link to='/admin/books/new'>
          <Button className='gap-2 font-sans font-bold uppercase tracking-[0.1em] bg-primary text-secondary rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
            <Plus className='w-4 h-4' />
            New Book
          </Button>
        </Link>
      </div>

      {/* Search bar */}
      <div className='relative group'>
        <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
          <Search className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
        </div>
        <input
          type='text'
          value={search}
          onChange={handleSearchChange}
          placeholder='Search books by title, author, or ISBN...'
          className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
        />
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
          {[...Array(8)].map((_, i) => (
            <div key={i} className='h-16 bg-primary/5 rounded-xl' />
          ))}
        </div>
      ) : (
        <>
          <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className='w-20'>Cover</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className='w-28'>Price</TableHead>
                  <TableHead className='w-20'>Stock</TableHead>
                  <TableHead className='w-24'>Status</TableHead>
                  <TableHead className='w-32 text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {books.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className='py-16 text-center'>
                      <BookOpen className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                      <p className='font-serif text-lg italic text-primary/30'>No books found</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  books.map((book) => (
                    <TableRow key={book.id}>
                      <TableCell>
                        {book.coverUrl ? (
                          <img
                            src={book.coverUrl}
                            alt={book.title}
                            className='object-cover w-14 h-20 rounded-2xl shadow-sm'
                          />
                        ) : (
                          <div className='flex items-center justify-center w-14 h-20 rounded-2xl bg-primary/5'>
                            <BookOpen className='w-5 h-5 text-primary/20' />
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/admin/books/${book.id}`}
                          className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                          {book.title}
                        </Link>
                        {book.authors?.length > 0 && (
                          <p className='text-xs font-medium text-primary/40'>
                            {book.authors.map((a) => a.name).join(', ')}
                          </p>
                        )}
                        {book.publisher && (
                          <p className='text-[10px] uppercase tracking-widest text-primary/20'>
                            {book.publisher.name}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className='font-sans font-bold text-primary'>
                        {formatBookPrice(book.price)}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            'font-sans font-bold text-sm',
                            book.stockQuantity === 0 && 'text-destructive',
                            book.stockQuantity > 0 && book.stockQuantity <= 5 && 'text-primary'
                          )}>
                          {book.stockQuantity}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={book.isActive ? 'default' : 'secondary'}
                          className={cn(
                            'text-[10px] font-black uppercase tracking-widest',
                            book.isActive && 'bg-primary/10 text-primary border-primary/20',
                            !book.isActive && 'bg-primary/5 text-primary/40 border-primary/10'
                          )}>
                          {book.isActive ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className='text-right'>
                        <div className='flex items-center justify-end gap-1'>
                          <Link to={`/admin/books/${book.id}`}>
                            <Button
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-2xl text-primary/40 hover:text-primary hover:bg-primary/5'>
                              <Pencil className='w-4 h-4' />
                            </Button>
                          </Link>
                          <Button
                            variant='ghost'
                            size='icon'
                            disabled={actionLoading === book.id}
                            onClick={() => handleToggleActive(book)}
                            className={cn(
                              'w-8 h-8 rounded-2xl',
                              book.isActive
                                ? 'text-primary/40 hover:text-primary hover:bg-primary/5'
                                : 'text-primary/40 hover:text-primary hover:bg-primary/5'
                            )}>
                            {actionLoading === book.id ? (
                              <Loader2 className='w-4 h-4 animate-spin' />
                            ) : (
                              <Power className='w-4 h-4' />
                            )}
                          </Button>
                          <Button
                            variant='ghost'
                            size='icon'
                            onClick={() => setDeleteTarget(book)}
                            className='w-8 h-8 rounded-2xl text-primary/40 hover:text-destructive hover:bg-destructive/5'>
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
                  className='gap-1 rounded-2xl'>
                  <ChevronLeft className='w-4 h-4' />
                  Previous
                </Button>
                <Button
                  variant='outline'
                  size='sm'
                  disabled={!hasNext}
                  onClick={() => setPage(page + 1)}
                  className='gap-1 rounded-2xl'>
                  Next
                  <ChevronRight className='w-4 h-4' />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent className='sm:max-w-md'>
          <DialogHeader>
            <DialogTitle className='font-serif text-xl font-black tracking-tighter text-destructive'>
              Delete Book
            </DialogTitle>
            <DialogDescription className='font-sans text-sm text-primary/60'>
              Are you sure you want to permanently delete &ldquo;{deleteTarget?.title}&rdquo;? This
              action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className='gap-2'>
            <Button
              variant='outline'
              onClick={() => setDeleteTarget(null)}
              className='rounded-2xl font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              Cancel
            </Button>
            <Button
              variant='destructive'
              onClick={handleDelete}
              disabled={deleteLoading}
              className='gap-2 rounded-2xl font-sans font-bold uppercase tracking-[0.1em] text-xs'>
              {deleteLoading ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                <Trash2 className='w-4 h-4' />
              )}
              Delete Forever
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
