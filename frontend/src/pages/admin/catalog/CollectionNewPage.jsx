import { ArrowLeft, Loader2, AlertCircle, Type, Link2, Library } from 'lucide-react';
import React, { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { collectionApi } from '@/lib/apiClient';

export default function CollectionNewPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [urlSlug, setUrlSlug] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

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
      setError('Collection name is required');
      return;
    }
    if (!urlSlug.trim()) {
      setError('URL slug is required');
      return;
    }

    setSubmitting(true);
    try {
      const res = await collectionApi.createCollection({
        createCollectionRequest: {
          name: name.trim(),
          urlSlug: urlSlug.trim(),
        },
      });

      const col = res.data;
      toast.success(`"${col.name}" created!`);
      navigate(`/admin/collections/${col.id}`);
    } catch (err) {
      let msg = 'Failed to create collection';
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

  return (
    <div className='space-y-8 max-w-2xl'>
      <Link
        to='/admin/collections'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Collections
      </Link>

      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          New Collection
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          Add a new collection to the catalog
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
              placeholder='e.g. Fiction Books'
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
              placeholder='fiction-books'
              className={`${inputClass} font-mono`}
            />
          </div>
          <p className='text-xs text-primary/30 pl-1'>Auto-generated from name. Edit if needed.</p>
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
              <Library className='w-5 h-5' />
              <span>Create Collection</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
