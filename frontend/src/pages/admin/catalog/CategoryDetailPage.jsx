import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  FolderTree,
  Link2,
  Type,
  Trash2,
  Pencil,
  Search,
  ChevronLeft,
  ChevronRight,
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
import { categoryApi, bookApi, collectionApi } from '@/lib/apiClient';

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

export default function CategoryDetailPage() {
  const { categoryId } = useParams();
  const navigate = useNavigate();

  const [category, setCategory] = useState(null);
  const [collections, setCollections] = useState([]);
  const [relatedBooks, setRelatedBooks] = useState([]);
  const [bookSearch, setBookSearch] = useState('');
  const [bookPage, setBookPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Delete dialog
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Edit dialog
  const [editDialog, setEditDialog] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editName, setEditName] = useState('');
  const [editSlug, setEditSlug] = useState('');
  const [editCollectionId, setEditCollectionId] = useState('');

  const generateSlug = useCallback((value) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 60);
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [catRes, colRes, booksRes] = await Promise.all([
        categoryApi.viewCategoryDetail({ categoryId }),
        collectionApi.findCollections(),
        bookApi.findBooks({ categoryId, pageSize: 50, sort: 'title:asc' }),
      ]);
      setCategory(catRes.data);
      setCollections(colRes.data || []);
      setRelatedBooks(booksRes.data?.items || []);
    } catch (err) {
      console.error('Failed to load category:', err);
      setError('Failed to load category');
    } finally {
      setLoading(false);
    }
  }, [categoryId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openEditDialog = () => {
    if (!category) return;
    setEditName(category.name);
    setEditSlug(category.urlSlug);
    setEditCollectionId(category.collectionId);
    setEditDialog(true);
  };

  const handleEditNameChange = (e) => {
    const val = e.target.value;
    setEditName(val);
    setEditSlug(generateSlug(val));
  };

  const handleEditSubmit = async () => {
    if (!editName.trim() || !editSlug.trim() || !editCollectionId) {
      toast.error('All fields are required');
      return;
    }
    setEditLoading(true);
    try {
      await categoryApi.updateCategory({
        categoryId,
        createCategoryRequest: {
          name: editName.trim(),
          urlSlug: editSlug.trim(),
          collectionId: editCollectionId,
        },
      });
      toast.success('Category updated');
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
      await categoryApi.softDeleteCategory({ categoryId });
      toast.success(`"${category?.name}" deleted`);
      setDeleteDialog(false);
      navigate('/admin/categories');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  const collectionName = collections.find((c) => c.id === category?.collectionId)?.name || '—';

  if (loading) {
    return <DetailSkeleton sections={2} />;
  }

  if (error || !category) {
    return (
      <div className='space-y-8'>
        <Link
          to='/admin/categories'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Categories
        </Link>
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>
            {error || 'Category not found'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-8 '>
      <BreadcrumbNav />

      <Link
        to='/admin/categories'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Categories
      </Link>

      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          {category.name}
        </h1>
        <p className='text-primary/40 font-bold italic text-sm font-mono'>{category.urlSlug}</p>
      </div>

      {/* Details */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Category Info
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Type className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Name</p>
                  <p className='text-sm font-sans font-bold text-primary'>{category.name}</p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Link2 className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>URL Slug</p>
                  <p className='text-sm font-mono font-bold text-primary'>{category.urlSlug}</p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <FolderTree className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Collection</p>
                  {category.collectionId ? (
                    <Link
                      to={`/admin/collections/${category.collectionId}`}
                      className='text-sm font-sans font-bold text-primary hover:underline'>
                      {collectionName}
                    </Link>
                  ) : (
                    <p className='text-sm font-sans font-bold text-primary'>{collectionName}</p>
                  )}
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
                <FolderTree className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Created</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(category.createdAt)}
                  </p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <FolderTree className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Last Updated</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(category.updatedAt)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Related Books */}
      <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
        <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
          Related Books ({relatedBooks.length})
        </h3>

        {/* Search */}
        <div className='relative mb-4'>
          <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
            <Search className='w-4 h-4 text-primary/30' />
          </div>
          <input
            type='text'
            value={bookSearch}
            onChange={(e) => {
              setBookSearch(e.target.value);
              setBookPage(1);
            }}
            placeholder='Search books...'
            className='w-full pl-10 pr-4 py-2 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
          />
        </div>

        {(() => {
          const filtered = bookSearch
            ? relatedBooks.filter((b) => b.title.toLowerCase().includes(bookSearch.toLowerCase()))
            : relatedBooks;
          const pageSize = 10;
          const totalPages = Math.ceil(filtered.length / pageSize) || 1;
          const startIndex = (bookPage - 1) * pageSize;
          const pageBooks = filtered.slice(startIndex, startIndex + pageSize);
          const hasPrev = bookPage > 1;
          const hasNext = bookPage < totalPages;

          if (relatedBooks.length === 0) {
            return <p className='text-sm text-primary/30 italic'>No books in this category</p>;
          }

          return (
            <>
              <div className='space-y-2'>
                {pageBooks.length === 0 ? (
                  <p className='text-sm text-primary/30 italic py-4'>
                    No books matching &quot;{bookSearch}&quot;
                  </p>
                ) : (
                  pageBooks.map((book) => (
                    <div
                      key={book.id}
                      className='flex items-center justify-between p-3 bg-white/60 rounded-xl'>
                      <div>
                        <Link
                          to={`/admin/books/${book.id}`}
                          className='text-sm font-sans font-bold text-primary hover:underline'>
                          {book.title}
                        </Link>
                        {book.isbn && (
                          <p className='text-xs font-mono text-primary/40'>{book.isbn}</p>
                        )}
                      </div>
                      <Link
                        to={`/admin/books/${book.id}`}
                        className='text-xs font-bold text-primary/40 hover:text-primary transition-colors'>
                        View →
                      </Link>
                    </div>
                  ))
                )}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className='flex items-center justify-between mt-4 pt-4 border-t border-primary/5'>
                  <p className='text-xs font-bold text-primary/40'>
                    Page {bookPage} of {totalPages}
                  </p>
                  <div className='flex gap-1'>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!hasPrev}
                      onClick={() => setBookPage(bookPage - 1)}
                      className='gap-1 rounded-xl'>
                      <ChevronLeft className='w-4 h-4' />
                      Previous
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!hasNext}
                      onClick={() => setBookPage(bookPage + 1)}
                      className='gap-1 rounded-xl'>
                      Next
                      <ChevronRight className='w-4 h-4' />
                    </Button>
                  </div>
                </div>
              )}
            </>
          );
        })()}
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
            Edit Category
          </Button>
          <Button
            variant='outline'
            onClick={() => setDeleteDialog(true)}
            className='gap-2 rounded-xl text-xs font-bold uppercase tracking-widest border-destructive/20 text-destructive hover:bg-destructive/5'>
            <Trash2 className='w-4 h-4' />
            Delete Category
          </Button>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onOpenChange={setEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Category</DialogTitle>
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
                  className='w-full pl-12 pr-4 py-3 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
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
                  onChange={(e) => setEditSlug(e.target.value)}
                  className='w-full pl-12 pr-4 py-3 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm font-mono'
                />
              </div>
            </div>
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Collection
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <FolderTree className='w-5 h-5 text-primary/30' />
                </div>
                <select
                  value={editCollectionId}
                  onChange={(e) => setEditCollectionId(e.target.value)}
                  className='w-full pl-12 pr-4 py-3 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'>
                  {collections.map((col) => (
                    <option key={col.id} value={col.id}>
                      {col.name}
                    </option>
                  ))}
                </select>
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
            <AlertDialogTitle className='text-destructive'>Delete Category?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete &quot;{category.name}&quot;. Associated books will lose
              their category assignment. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className='bg-destructive text-white'>
              {deleteLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Delete Category'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
