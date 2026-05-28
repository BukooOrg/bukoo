import { FolderTree, ArrowLeft, Loader2, AlertCircle, Type, Link2 } from 'lucide-react';
import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { categoryApi, collectionApi } from '@/lib/apiClient';

export default function CategoryNewPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [urlSlug, setUrlSlug] = useState('');
  const [collectionId, setCollectionId] = useState('');
  const [collections, setCollections] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [loadingCollections, setLoadingCollections] = useState(true);

  useEffect(() => {
    async function loadCollections() {
      try {
        const res = await collectionApi.findCollections();
        setCollections(res.data?.items || []);
        if (res.data?.items?.length === 1) {
          setCollectionId(res.data.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load collections:', err);
        setError('Failed to load collections');
      } finally {
        setLoadingCollections(false);
      }
    }
    loadCollections();
  }, []);

  const generateSlug = useCallback((value) => {
    return value
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 60);
  }, []);

  const handleNameChange = (e) => {
    const val = e.target.value;
    setName(val);
    setUrlSlug(generateSlug(val));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Category name is required');
      return;
    }
    if (!urlSlug.trim()) {
      setError('URL slug is required');
      return;
    }
    if (!collectionId) {
      setError('Please select a collection');
      return;
    }

    setSubmitting(true);
    try {
      const res = await categoryApi.createCategory({
        createCategoryRequest: {
          name: name.trim(),
          urlSlug: urlSlug.trim(),
          collectionId,
        },
      });

      const cat = res.data;
      toast.success(`"${cat.name}" created!`);
      navigate(`/admin/categories/${cat.id}`);
    } catch (err) {
      let msg = 'Failed to create category';
      try {
        const res = err?.response;
        if (res) {
          const text = await res.clone().text();
          try {
            const body = JSON.parse(text);
            msg = body?.error?.message || body?.detail || msg;
          } catch {
            msg = text || err?.message || msg;
          }
        } else {
          msg = err?.message || msg;
        }
      } catch {
        msg = err?.message || msg;
      }
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm';

  if (loadingCollections) {
    return (
      <div className='space-y-8 '>
        <div className='animate-pulse space-y-6'>
          <div className='h-6 bg-primary/5 rounded-lg w-32' />
          <div className='h-10 bg-primary/5 rounded-2xl' />
          <div className='h-10 bg-primary/5 rounded-2xl' />
          <div className='h-10 bg-primary/5 rounded-2xl' />
          <div className='h-14 bg-primary/5 rounded-2xl' />
        </div>
      </div>
    );
  }

  if (collections.length === 0) {
    return (
      <div className='space-y-8 '>
        <Link
          to='/admin/categories'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Categories
        </Link>
        <div className='text-center pt-8'>
          <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
            New Category
          </h1>
        </div>
        <div className='flex items-start gap-3 p-4 border bg-primary/5 border-primary/10 rounded-2xl'>
          <AlertCircle className='w-5 h-5 text-primary shrink-0' />
          <div>
            <p className='text-xs font-bold leading-relaxed text-primary'>
              No collections exist. Create a collection first before adding categories.
            </p>
            <Link
              to='/admin/collections/new'
              className='text-xs font-bold text-primary underline mt-2 inline-block'>
              Go to Collections →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-8 '>
      <Link
        to='/admin/categories'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Categories
      </Link>

      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          New Category
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          Add a new genre or topic category
        </p>
      </div>

      <form onSubmit={handleSubmit} className='space-y-5'>
        {/* Name */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Name <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <Type className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='text'
              value={name}
              onChange={handleNameChange}
              placeholder='e.g. Science Fiction'
              className={inputClass}
            />
          </div>
        </div>

        {/* URL Slug */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            URL Slug <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <Link2 className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='text'
              value={urlSlug}
              onChange={(e) => setUrlSlug(e.target.value)}
              placeholder='science-fiction'
              className={`${inputClass} font-mono`}
            />
          </div>
          <p className='text-xs text-primary/30 pl-1'>Auto-generated from name. Edit if needed.</p>
        </div>

        {/* Collection */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Collection <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <FolderTree className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <select
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              className={inputClass}>
              <option value=''>Select a collection</option>
              {collections.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.name}
                </option>
              ))}
            </select>
          </div>
        </div>

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
              <FolderTree className='w-5 h-5' />
              <span>Create Category</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
