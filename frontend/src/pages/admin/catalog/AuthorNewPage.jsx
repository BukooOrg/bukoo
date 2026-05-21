import { ArrowLeft, Loader2, AlertCircle, Type } from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { authorApi } from '@/lib/apiClient';

export default function AuthorNewPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Author name is required');
      return;
    }

    setSubmitting(true);
    try {
      const res = await authorApi.createAuthor({
        createAuthorRequest: {
          name: name.trim(),
        },
      });

      const author = res.data;
      toast.success(`"${author.name}" created!`);
      navigate(`/admin/authors/${author.id}`);
    } catch (err) {
      let msg = 'Failed to create author';
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
    <div className='space-y-8 '>
      <Link
        to='/admin/authors'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Authors
      </Link>

      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          New Author
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Add a new author to the catalog</p>
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
              onChange={(e) => setName(e.target.value)}
              placeholder='e.g. Jane Austen'
              className={inputClass}
            />
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
              <Type className='w-5 h-5' />
              <span>Create Author</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
