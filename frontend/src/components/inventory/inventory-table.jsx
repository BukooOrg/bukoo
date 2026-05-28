import { AlertCircle, BookOpen, ExternalLink, Search } from 'lucide-react';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { Button } from '@/components/ui/forms/button';
import { cn } from '@/lib/utils';

export function InventoryTable({ title, description, fetchItems, emptyMessage, rangeSelector }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [rangeIndex, setRangeIndex] = useState(rangeSelector?.default ?? 0);
  const [reloadKey, setReloadKey] = useState(0);
  const searchTimeout = useRef(null);

  const range = rangeSelector?.options?.[rangeIndex];

  const doLoad = useCallback(async (p, s, r) => {
    setLoading(true);
    setError('');
    try {
      const params = { page: p, pageSize: 10, ...(s && { search: s }) };
      if (r?.threshold !== null && r?.threshold !== undefined) params.threshold = r.threshold;
      const res = await fetchItems(params);
      const data = res.data;
      setItems(data.items || []);
      setTotalPages(data.pagination?.totalPages || 1);
    } catch {
      setError('Failed to load inventory data');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [fetchItems]);

  // Single source of truth: reloads when any of these change
  useEffect(() => {
    doLoad(page, search, range);
  }, [page, rangeIndex, search, reloadKey, doLoad, range]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      setSearch(val);
    }, 400);
  };

  const handleRangeChange = (e) => {
    const idx = Number(e.target.value);
    setRangeIndex(idx);
    setPage(1);
    setSearch('');
    setReloadKey((k) => k + 1);
  };

  const handleRetry = () => setReloadKey((k) => k + 1);

  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  if (loading && items.length === 0) {
    return (
      <div className='space-y-6'>
        <div className='text-center pt-4'>
          <h2 className='text-2xl font-serif font-black tracking-tighter text-primary'>{title}</h2>
          <p className='text-primary/40 font-bold italic text-sm mt-1'>{description}</p>
        </div>
        <div className='animate-pulse space-y-3'>
          {[...Array(5)].map((_, i) => (
            <div key={i} className='h-16 bg-primary/5 rounded-xl' />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div className='text-center pt-4'>
        <h2 className='text-2xl font-serif font-black tracking-tighter text-primary'>{title}</h2>
        <p className='text-primary/40 font-bold italic text-sm mt-1'>{description}</p>
      </div>

      <div className='flex flex-wrap items-center gap-3'>
        <div className='relative flex-1 max-w-sm group'>
          <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
            <Search className='w-4 h-4 text-primary/30 group-focus-within:text-primary transition-colors' />
          </div>
          <input
            type='text'
            value={search}
            onChange={handleSearchChange}
            placeholder='Search by title or ISBN...'
            className='w-full pl-10 pr-4 py-2.5 bg-white/40 border border-primary/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
            aria-label='Search inventory'
          />
        </div>
        {rangeSelector && (
          <select
            value={rangeIndex}
            onChange={handleRangeChange}
            className='h-10 px-3 text-sm transition-all border rounded-lg border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10'
            aria-label='Stock range'>
            {rangeSelector.options.map((opt, i) => (
              <option key={i} value={i}>
                {opt.label} units
              </option>
            ))}
          </select>
        )}
      </div>

      {error && (
        <div className='flex items-center justify-between p-4 border bg-destructive/5 border-destructive/10 rounded-xl'>
          <div className='flex items-start gap-3'>
            <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
            <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
          </div>
          <Button variant='outline' size='sm' onClick={handleRetry} className='rounded-lg'>
            Retry
          </Button>
        </div>
      )}

      <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className='w-20'>Cover</TableHead>
              <TableHead>Title</TableHead>
              <TableHead className='w-32'>ISBN</TableHead>
              {rangeSelector && <TableHead className='w-24'>Stock Qty</TableHead>}
              <TableHead className='w-20 text-right'>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={rangeSelector ? 5 : 4} className='py-16 text-center'>
                  <BookOpen className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                  <p className='font-serif text-lg italic text-primary/30'>{emptyMessage}</p>
                </TableCell>
              </TableRow>
            ) : (
              items.map((book) => (
                <TableRow key={book.id}>
                  <TableCell>
                    {book.coverUrl ? (
                      <img src={book.coverUrl} alt={book.title} className='object-cover w-12 h-16 rounded shadow-sm' />
                    ) : (
                      <div className='flex items-center justify-center w-12 h-16 rounded bg-primary/5'>
                        <BookOpen className='w-4 h-4 text-primary/20' />
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Link to={`/admin/books/${book.id}`} className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                      {book.title}
                    </Link>
                  </TableCell>
                  <TableCell className='font-mono text-xs text-primary/50'>{book.isbn || '—'}</TableCell>
                  {rangeSelector && (
                    <TableCell>
                      <span className={cn('font-sans font-bold text-sm', book.stockQuantity === 0 && 'text-destructive', book.stockQuantity > 0 && range && range.threshold !== null && book.stockQuantity <= range.threshold && 'text-amber-600')}>
                        {book.stockQuantity}
                      </span>
                    </TableCell>
                  )}
                  <TableCell className='text-right'>
                    <Link to={`/admin/books/${book.id}`} aria-label={`View ${book.title} details`}>
                      <Button variant='ghost' size='icon-sm' className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                        <ExternalLink className='w-4 h-4' />
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className='flex items-center justify-center gap-3'>
          <Button variant='outline' disabled={!hasPrev} onClick={() => setPage((p) => p - 1)} className='h-9 rounded-lg'>Previous</Button>
          <span className='text-sm text-primary/40'>Page {page} of {totalPages}</span>
          <Button variant='outline' disabled={!hasNext} onClick={() => setPage((p) => p + 1)} className='h-9 rounded-lg'>Next</Button>
        </div>
      )}
    </div>
  );
}
