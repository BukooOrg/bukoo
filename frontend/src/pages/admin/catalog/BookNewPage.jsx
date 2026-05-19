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
  ImagePlus,
  ArrowLeft,
} from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { bookApi, publisherApi, categoryApi, authorApi, uploadBookCover } from '@/lib/apiClient';

export default function BookNewPage() {
  const navigate = useNavigate();

  // Form state
  const [title, setTitle] = useState('');
  const [price, setPrice] = useState('');
  const [stockQuantity, setStockQuantity] = useState('1');
  const [language, setLanguage] = useState('English');
  const [isbn, setIsbn] = useState('');
  const [description, setDescription] = useState('');
  const [pageCount, setPageCount] = useState('');
  const [publishedDate, setPublishedDate] = useState('');
  const [publisherId, setPublisherId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [selectedAuthors, setSelectedAuthors] = useState([]);
  const [coverFile, setCoverFile] = useState(null);

  // Reference data
  const [publishers, setPublishers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [authors, setAuthors] = useState([]);
  const [refLoading, setRefLoading] = useState(true);

  // Submit state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

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
      } finally {
        setRefLoading(false);
      }
    }
    loadRefs();
  }, []);

  const handleAuthorToggle = (authorId) => {
    setSelectedAuthors((prev) => {
      if (prev.includes(authorId)) {
        return prev.filter((id) => id !== authorId);
      }
      return [...prev, authorId];
    });
  };

  const validateIsbn13 = (isbn) => {
    const digits = isbn.replace(/[-\s]/g, '');
    if (digits.length !== 13 || !/^\d+$/.test(digits)) return false;
    const total = digits
      .slice(0, 12)
      .split('')
      .reduce((sum, d, i) => sum + parseInt(d) * (i % 2 === 0 ? 1 : 3), 0);
    const check = (10 - (total % 10)) % 10;
    return check === parseInt(digits[12]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    if (!price || parseFloat(price) <= 0) {
      setError('Price must be a positive number');
      return;
    }
    if (!stockQuantity || parseInt(stockQuantity) < 0) {
      setError('Stock quantity must be 0 or greater');
      return;
    }
    if (!language.trim()) {
      setError('Language is required');
      return;
    }
    if (isbn.trim() && !validateIsbn13(isbn.trim())) {
      setError('Invalid ISBN-13 checksum. Use a valid 13-digit ISBN (e.g. 9781234567897)');
      return;
    }

    setSubmitting(true);
    try {
      const requestBody = {
        createBookRequest: {
          title: title.trim(),
          price: price,
          stockQuantity: parseInt(stockQuantity),
          language: language.trim(),
          isbn: isbn.trim() || undefined,
          description: description.trim() || undefined,
          pageCount: pageCount ? parseInt(pageCount) : undefined,
          publishedDate: publishedDate ? new Date(publishedDate + 'T00:00:00') : undefined,
          publisherId: publisherId || undefined,
          categoryId: categoryId || undefined,
          authors: selectedAuthors.map((authorId, i) => ({
            authorId,
            displayOrder: i + 1,
          })),
        },
      };
      const res = await bookApi.createBook(requestBody);

      const book = res.data;
      toast.success(`"${book.title}" created!`);

      if (coverFile) {
        try {
          await uploadBookCover(book.id, coverFile);
          toast.success('Cover uploaded!');
        } catch (err) {
          console.error('Cover upload failed:', err);
          toast.error('Book created but cover upload failed');
        }
      }

      navigate(`/admin/books/${book.id}`);
    } catch (err) {
      let msg = 'Failed to create book';
      try {
        const res = err?.response;
        if (res) {
          const text = await res.clone().text();
          console.error('Create book response body:', text);
          try {
            const body = JSON.parse(text);
            if (body?.error?.message) {
              msg = body.error.message;
            } else if (body?.detail) {
              msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
            }
          } catch {
            msg = text || err?.message || msg;
          }
        } else {
          msg = err?.message || msg;
        }
      } catch {
        msg = err?.message || msg;
      }
      console.error('Create book error:', err);
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm';

  if (refLoading) {
    return (
      <div className='animate-pulse space-y-4'>
        <div className='h-8 bg-primary/5 rounded-xl w-48' />
        <div className='h-96 bg-primary/5 rounded-2xl' />
      </div>
    );
  }

  return (
    <div className='space-y-8 max-w-2xl'>
      <Link
        to='/admin/books'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Books
      </Link>

      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          New Book
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Add a book to the catalog</p>
      </div>

      <form onSubmit={handleSubmit} className='max-w-2xl space-y-5'>
        {/* Title */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Title <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <BookOpen className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='text'
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder='Enter book title'
              className={inputClass}
            />
          </div>
        </div>

        {/* Price + Stock */}
        <div className='grid grid-cols-2 gap-4'>
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Price <span className='text-destructive'>*</span>
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
                placeholder='29.99'
                className={inputClass}
              />
            </div>
          </div>
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Stock <span className='text-destructive'>*</span>
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
                placeholder='1'
                className={inputClass}
              />
            </div>
          </div>
        </div>

        {/* Language + ISBN */}
        <div className='grid grid-cols-2 gap-4'>
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Language <span className='text-destructive'>*</span>
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <Globe className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type='text'
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder='English'
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
                placeholder='9781234567897'
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
                placeholder='320'
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

        {/* Cover Image */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Cover Image
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <ImagePlus className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='file'
              accept='image/*'
              onChange={(e) => setCoverFile(e.target.files?.[0] || null)}
              className={inputClass}
            />
          </div>
          {coverFile && <p className='text-xs font-bold text-primary/40 pl-1'>{coverFile.name}</p>}
        </div>

        {/* Description */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder='A brief description of the book...'
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
                    onChange={() => handleAuthorToggle(author.id)}
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

        {/* Error */}
        {error && (
          <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
            <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
            <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type='submit'
          disabled={submitting}
          className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
          {submitting ? (
            <Loader2 className='w-5 h-5 animate-spin' />
          ) : (
            <>
              <BookOpen className='w-5 h-5' />
              <span>Create Book</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
