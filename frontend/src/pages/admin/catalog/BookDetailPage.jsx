import {
  BookOpen,
  DollarSign,
  Package,
  Globe,
  Barcode,
  FileText,
  Calendar,
  Loader2,
  AlertCircle,
  Pencil,
  Trash2,
  Power,
  ArrowLeft,
  ImagePlus,
} from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/data-display/badge';
import { DetailSkeleton } from '@/components/ui/feedback/page-skeleton';
import { Button } from '@/components/ui/forms/button';
import { BreadcrumbNav } from '@/components/ui/navigation/breadcrumb-nav';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/overlays/dialog';
import { useApiMutation } from '@/hooks/useApiMutation';
import { bookApi, publisherApi, categoryApi, authorApi, uploadBookCover } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

function formatBookPrice(price) {
  if (!price) return '—';
  const num = parseFloat(price);
  if (isNaN(num)) return price;
  return new Intl.NumberFormat('ms-MY', { style: 'currency', currency: 'MYR' }).format(num);
}

export default function BookDetailPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();

  // Fetch state
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Edit mode toggle
  const [editing, setEditing] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState('');
  const [stockQuantity, setStockQuantity] = useState('');
  const [language, setLanguage] = useState('');
  const [isbn, setIsbn] = useState('');
  const [description, setDescription] = useState('');
  const [pageCount, setPageCount] = useState('');
  const [publishedDate, setPublishedDate] = useState('');
  const [publisherId, setPublisherId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [selectedAuthors, setSelectedAuthors] = useState([]);
  const initialized = useRef(false);

  // Reference data (for edit selects)
  const [publishers, setPublishers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [authors, setAuthors] = useState([]);

  // Action states
  const [saveLoading, setSaveLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [stockVal, setStockVal] = useState('');
  const [stockLoading, setStockLoading] = useState(false);

  const { mutate: uploadCover, loading: coverUploading } = useApiMutation(
    (file) => uploadBookCover(bookId, file),
    {
      onSuccess: (data) => {
        setBook({
          ...data,
          coverUrl: data.coverUrl ? `${data.coverUrl}?t=${Date.now()}` : data.coverUrl,
        });
        toast.success('Cover uploaded!');
      },
      onError: (err) => setError(err?.message || 'Failed to upload cover'),
    }
  );

  // Fetch book
  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const res = await bookApi.viewBookDetail({ bookId, status: 'all' });
        setBook(res.data);
      } catch (err) {
        console.error('Failed to load book:', err);
        setError('Book not found');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [bookId]);

  // Load reference data when entering edit mode
  useEffect(() => {
    async function loadRefs() {
      try {
        const [pubRes, catRes, authRes] = await Promise.all([
          publisherApi.findPublishers({}),
          categoryApi.findCategories({}),
          authorApi.findAuthors({}),
        ]);
        setPublishers(pubRes.data?.items || []);
        setCategories(catRes.data || []);
        setAuthors(authRes.data?.items || []);
      } catch (err) {
        console.error('Failed to load reference data', err);
      }
    }
    loadRefs();
  }, []);

  // Initialize form when book loads or entering edit mode
  useEffect(() => {
    if (book && editing && !initialized.current) {
      setTitle(book.title || '');
      setPrice(book.price || '');
      setStockQuantity(String(book.stockQuantity ?? ''));
      setLanguage(book.language || '');
      setIsbn(book.isbn || '');
      setDescription(book.description || '');
      setPageCount(book.pageCount ? String(book.pageCount) : '');
      if (book.publishedDate) {
        const d = new Date(book.publishedDate);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        setPublishedDate(`${year}-${month}-${day}`);
      } else {
        setPublishedDate('');
      }
      setPublisherId(book.publisher?.id || '');
      setCategoryId(book.category?.id || '');
      setSelectedAuthors((book.authors || []).map((a) => a.id));
      initialized.current = true;
    }
    if (!editing) {
      initialized.current = false;
    }
  }, [book, editing]);

  // Save changes
  const handleSave = async (e) => {
    e.preventDefault();
    setError('');
    setSaveLoading(true);
    try {
      const res = await bookApi.updateBook({
        bookId,
        updateBookRequest: {
          title: title.trim() || null,
          price: price || null,
          stockQuantity: stockQuantity ? parseInt(stockQuantity) : null,
          language: language.trim() || null,
          isbn: isbn.trim() || null,
          description: description.trim() || null,
          pageCount: pageCount ? parseInt(pageCount) : null,
          publishedDate: publishedDate ? new Date(publishedDate + 'T00:00:00') : null,
          publisherId: publisherId || null,
          categoryId: categoryId || null,
          authors:
            selectedAuthors.length > 0
              ? selectedAuthors.map((authorId, i) => ({
                  authorId,
                  displayOrder: i + 1,
                }))
              : null,
        },
      });
      setBook(res.data);
      setEditing(false);
      toast.success('Book updated!');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Failed to update book';
      setError(msg);
    } finally {
      setSaveLoading(false);
    }
  };

  // Toggle active/deactivated
  const handleToggleActive = async () => {
    setActionLoading(true);
    setError('');
    try {
      let res;
      if (book.isActive) {
        res = await bookApi.deactivateBook({ bookId });
        toast.success('Book deactivated');
      } else {
        res = await bookApi.activateBook({ bookId });
        toast.success('Book activated');
      }
      setBook(res.data);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Action failed';
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  // Delete
  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await bookApi.softDeleteBook({ bookId });
      toast.success('Book deleted');
      navigate('/admin/books');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
      setDeleteTarget(false);
    }
  };

  // Update stock
  const handleStockUpdate = async () => {
    const qty = parseInt(stockVal);
    if (isNaN(qty) || qty < 0) {
      setError('Stock must be 0 or greater');
      return;
    }
    setStockLoading(true);
    setError('');
    try {
      const res = await bookApi.updateBookStockQuantity({
        bookId,
        updateBookStockQuantityRequest: { stockQuantity: qty },
      });
      setBook(res.data);
      setStockVal('');
      toast.success('Stock updated!');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Failed to update stock';
      setError(msg);
    } finally {
      setStockLoading(false);
    }
  };

  const handleCoverUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadCover(file);
  };

  const inputClass =
    'w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm';

  if (loading) {
    return <DetailSkeleton sections={3} />;
  }

  if (!book) {
    return (
      <div className='py-16 text-center'>
        <BookOpen className='w-12 h-12 mx-auto mb-4 text-primary/20' />
        <h1 className='font-serif text-3xl font-black text-primary'>Book Not Found</h1>
        <p className='mt-2 text-sm text-primary/40'>
          {error || 'The requested book does not exist'}
        </p>
        <Link
          to='/admin/books'
          className='inline-block mt-6 text-xs font-black uppercase tracking-widest text-primary hover:underline'>
          Back to Books
        </Link>
      </div>
    );
  }

  return (
    <div className='space-y-8 '>
      <BreadcrumbNav />

      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          {book.title}
        </h1>
        <div className='flex flex-wrap items-center justify-center gap-3'>
          <Badge
            variant={book.isActive ? 'default' : 'secondary'}
            className={cn(
              'text-[10px] font-black uppercase tracking-widest',
              book.isActive && 'bg-primary/10 text-primary border-primary/20',
              !book.isActive && 'bg-primary/5 text-primary/40 border-primary/10'
            )}>
            {book.isActive ? 'Active' : 'Inactive'}
          </Badge>
          {book.category && (
            <span className='text-xs font-bold text-primary/40'>{book.category.name}</span>
          )}
          <span className='text-[10px] font-black uppercase tracking-widest text-primary/20'>
            {book.id}
          </span>
        </div>
      </div>

      {/* Top bar — back + actions */}
      <div className='flex items-center justify-between'>
        <Link
          to='/admin/books'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Books
        </Link>
        <div className='flex items-center gap-2'>
          {!editing && (
            <>
              <Button
                variant='outline'
                size='sm'
                onClick={handleToggleActive}
                disabled={actionLoading}
                className='gap-1 font-sans font-bold uppercase tracking-[0.1em] text-xs rounded-xl'>
                {actionLoading ? (
                  <Loader2 className='w-4 h-4 animate-spin' />
                ) : (
                  <Power className='w-4 h-4' />
                )}
                {book.isActive ? 'Deactivate' : 'Activate'}
              </Button>
              <Button
                variant='outline'
                size='sm'
                onClick={() => setEditing(true)}
                className='gap-1 font-sans font-bold uppercase tracking-[0.1em] text-xs rounded-xl'>
                <Pencil className='w-4 h-4' />
                Edit
              </Button>
              <Button
                variant='outline'
                size='sm'
                onClick={() => setDeleteTarget(true)}
                className='gap-1 font-sans font-bold uppercase tracking-[0.1em] text-xs rounded-xl text-destructive border-destructive/20 hover:bg-destructive/5'>
                <Trash2 className='w-4 h-4' />
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
        </div>
      )}

      {/* Cover Image */}
      <div className='flex items-start gap-6'>
        <div className='relative w-32 h-48 overflow-hidden rounded-xl border border-primary/5 bg-primary/5 shrink-0'>
          {book.coverUrl ? (
            <img src={book.coverUrl} alt={book.title} className='object-cover w-full h-full' />
          ) : (
            <div className='flex items-center justify-center w-full h-full'>
              <BookOpen className='w-8 h-8 text-primary/20' />
            </div>
          )}
          <label className='absolute bottom-0 left-0 right-0 p-1.5 bg-primary/40 flex items-center justify-center cursor-pointer transition-colors hover:bg-black/60'>
            <input type='file' accept='image/*' className='hidden' onChange={handleCoverUpload} />
            {coverUploading ? (
              <Loader2 className='w-4 h-4 text-secondary animate-spin' />
            ) : (
              <ImagePlus className='w-4 h-4 text-secondary' />
            )}
          </label>
        </div>

        {/* Quick info */}
        <div className='grid flex-1 grid-cols-2 gap-3 sm:grid-cols-4'>
          <div className='p-3 rounded-xl bg-primary/5'>
            <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
              Price
            </p>
            <p className='font-sans text-lg font-bold text-primary'>
              {formatBookPrice(book.price)}
            </p>
          </div>
          <div className='p-3 rounded-xl bg-primary/5'>
            <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
              Stock
            </p>
            <p
              className={cn(
                'font-sans text-lg font-bold',
                book.stockQuantity === 0 && 'text-destructive',
                book.stockQuantity > 0 && book.stockQuantity <= 5 && 'text-primary',
                book.stockQuantity > 5 && 'text-primary'
              )}>
              {book.stockQuantity}
            </p>
          </div>
          <div className='p-3 rounded-xl bg-primary/5'>
            <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
              Pages
            </p>
            <p className='font-sans text-lg font-bold text-primary'>{book.pageCount || '—'}</p>
          </div>
          <div className='p-3 rounded-xl bg-primary/5'>
            <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
              Language
            </p>
            <p className='font-sans text-lg font-bold text-primary'>{book.language || '—'}</p>
          </div>
        </div>
      </div>

      {/* Stock Quick Update */}
      {!editing && (
        <div className='flex items-end gap-3 p-4 bg-white border rounded-2xl border-primary/5'>
          <div className='flex-1 space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Set Stock Quantity
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <Package className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type='number'
                min='0'
                value={stockVal}
                onChange={(e) => setStockVal(e.target.value)}
                placeholder={String(book.stockQuantity)}
                className={inputClass}
              />
            </div>
          </div>
          <button
            type='button'
            onClick={handleStockUpdate}
            disabled={stockLoading || !stockVal}
            className='py-4 px-6 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.1em] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
            {stockLoading ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <Package className='w-5 h-5' />
            )}
            Update
          </button>
        </div>
      )}

      {/* Edit Form */}
      {editing ? (
        <form onSubmit={handleSave} className='space-y-5'>
          <div className='p-6 space-y-5 bg-white border rounded-2xl border-primary/5'>
            {/* Title */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Title
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <BookOpen className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='text'
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>

            {/* Price + Stock */}
            <div className='grid grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Price
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <DollarSign className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='number'
                    step='0.01'
                    min='0'
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Stock
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <Package className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='number'
                    min='0'
                    value={stockQuantity}
                    onChange={(e) => setStockQuantity(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            {/* Language + ISBN */}
            <div className='grid grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Language
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <Globe className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='text'
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  ISBN
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <Barcode className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='text'
                    value={isbn}
                    onChange={(e) => setIsbn(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            {/* Page Count + Published Date */}
            <div className='grid grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Page Count
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <FileText className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='number'
                    min='1'
                    value={pageCount}
                    onChange={(e) => setPageCount(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Published Date
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                    <Calendar className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='date'
                    value={publishedDate}
                    onChange={(e) => setPublishedDate(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            {/* Description */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className='w-full px-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm resize-none'
              />
            </div>

            {/* Publisher */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Publisher
              </label>
              <select
                value={publisherId}
                onChange={(e) => setPublisherId(e.target.value)}
                className='w-full pl-4 pr-10 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm appearance-none bg-no-repeat bg-[center_right_1rem]'
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%233F2305' opacity='0.3'%3E%3Cpath d='M6 8L1 3h10z'/%3E%3C/svg%3E\")",
                }}>
                <option value=''>No publisher</option>
                {publishers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className='w-full pl-4 pr-10 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm appearance-none bg-no-repeat bg-[center_right_1rem]'
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%233F2305' opacity='0.3'%3E%3Cpath d='M6 8L1 3h10z'/%3E%3C/svg%3E\")",
                }}>
                <option value=''>No category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Authors */}
            {authors.length > 0 && (
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Authors
                </label>
                <div className='p-4 space-y-2 bg-white/40 border border-primary/5 rounded-2xl max-h-48 overflow-y-auto'>
                  {authors.map((author) => (
                    <label key={author.id} className='flex items-center gap-3 cursor-pointer group'>
                      <input
                        type='checkbox'
                        checked={selectedAuthors.includes(author.id)}
                        onChange={() =>
                          setSelectedAuthors((prev) =>
                            prev.includes(author.id)
                              ? prev.filter((id) => id !== author.id)
                              : [...prev, author.id]
                          )
                        }
                        className='w-4 h-4 rounded border-primary/20 text-primary focus:ring-primary/20'
                      />
                      <span className='text-sm font-sans font-bold text-primary/70 group-hover:text-primary transition-colors'>
                        {author.name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className='flex gap-3 pt-4'>
              <button
                type='button'
                onClick={() => setEditing(false)}
                className='flex-1 py-4 bg-white border border-primary/10 text-primary rounded-2xl font-sans font-bold uppercase tracking-[0.1em] hover:border-primary/20 active:scale-[0.98] transition-all'>
                Cancel
              </button>
              <button
                type='submit'
                disabled={saveLoading}
                className='flex-1 py-4 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.1em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
                {saveLoading ? (
                  <Loader2 className='w-5 h-5 animate-spin' />
                ) : (
                  <Pencil className='w-5 h-5' />
                )}
                Save Changes
              </button>
            </div>
          </div>
        </form>
      ) : (
        <>
          {/* Detail cards */}
          <div className='grid gap-4 sm:grid-cols-2'>
            {/* Info card */}
            <div className='p-6 space-y-4 bg-white border rounded-2xl border-primary/5'>
              <h2 className='text-sm font-black uppercase tracking-[0.2em] text-primary/40'>
                Details
              </h2>
              <div className='space-y-3'>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    ISBN
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>{book.isbn || '—'}</p>
                </div>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Published
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>
                    {book.publishedDate
                      ? new Date(book.publishedDate).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Created
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>
                    {book.createdAt
                      ? new Date(book.createdAt).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Updated
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>
                    {book.updatedAt
                      ? new Date(book.updatedAt).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : '—'}
                  </p>
                </div>
              </div>
            </div>

            {/* Relationships card */}
            <div className='p-6 space-y-4 bg-white border rounded-2xl border-primary/5'>
              <h2 className='text-sm font-black uppercase tracking-[0.2em] text-primary/40'>
                Relationships
              </h2>
              <div className='space-y-3'>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Publisher
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>
                    {book.publisher ? (
                      <Link
                        to={`/admin/publishers/${book.publisher.id}`}
                        className='hover:underline'>
                        {book.publisher.name}
                      </Link>
                    ) : (
                      '—'
                    )}
                  </p>
                </div>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Category
                  </p>
                  <p className='font-sans text-sm font-bold text-primary'>
                    {book.category ? (
                      <Link
                        to={`/admin/categories/${book.category.id}`}
                        className='hover:underline'>
                        {book.category.name}
                      </Link>
                    ) : (
                      '—'
                    )}
                  </p>
                </div>
                <div>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Authors
                  </p>
                  {book.authors?.length > 0 ? (
                    <div className='mt-1 space-y-1'>
                      {book.authors.map((a) => (
                        <Link
                          key={a.id}
                          to={`/admin/authors/${a.id}`}
                          className='block font-sans text-sm font-bold text-primary hover:underline'>
                          {a.name}
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <p className='font-sans text-sm font-bold text-primary'>—</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Description card */}
          {book.description && (
            <div className='p-6 bg-white border rounded-2xl border-primary/5'>
              <h2 className='mb-3 text-sm font-black uppercase tracking-[0.2em] text-primary/40'>
                Description
              </h2>
              <p className='text-sm leading-relaxed font-sans font-medium text-primary/70'>
                {book.description}
              </p>
            </div>
          )}
        </>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(false)}>
        <DialogContent className='sm:max-w-md'>
          <DialogHeader>
            <DialogTitle className='font-serif text-xl font-black tracking-tighter text-destructive'>
              Delete Book
            </DialogTitle>
            <DialogDescription className='font-sans text-sm text-primary/60'>
              Are you sure you want to permanently delete &ldquo;{book.title}&rdquo;? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className='gap-2'>
            <Button
              variant='outline'
              onClick={() => setDeleteTarget(false)}
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
              Delete Forever
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
