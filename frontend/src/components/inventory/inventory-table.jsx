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

const PAGE_SIZE = 10;

export function InventoryTable({ title, description, fetchItems, emptyMessage, rangeSelector }) {
  const [allItems, setAllItems] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [rangeIndex, setRangeIndex] = useState(rangeSelector?.default ?? 0);
  const [reloadKey, setReloadKey] = useState(0);
  const searchTimeout = useRef(null);

  const range = rangeSelector?.options?.[rangeIndex];

  // Fetch ALL items from backend (in batches of 100), then filter + paginate client-side
  const doLoad = useCallback(async (s) => {
    setLoading(true);
    setError('');
    try {
      const params = { page: 1, pageSize: 100, ...(s && { search: s }) };
      // For ranges with max, use it as backend threshold to reduce data
      if (range?.max !== null && range?.max !== undefined) {
        params.threshold = range.max;
      }

      // Fetch first page
      const res = await fetchItems(params);
      const data = res.data;
      let allResults = data.items || [];
      const totalPagesBackend = data.pagination?.totalPages || 1;

      // Fetch remaining pages in parallel
      if (totalPagesBackend > 1) {
        const remainingPages = Array.from(
          { length: totalPagesBackend - 1 },
          (_, i) => i + 2
        );
        const results = await Promise.all(
          remainingPages.map((p) =>
            fetchItems({ ...params, page: p }).then((r) => r.data.items || [])
          )
        );
        allResults = [...allResults, ...results.flat()];
      }

      // Client-side filter for range min
      let filtered = allResults;
      if (range?.min > 0) {
        filtered = allResults.filter((item) => item.stockQuantity >= range.min);
      }

      setAllItems(filtered);
      // Client-side pagination
      const tp = Math.ceil(filtered.length / PAGE_SIZE) || 1;
      setTotalPages(tp);
      setItems(filtered.slice(0, PAGE_SIZE));
      setPage(1);
    } catch {
      setError('Failed to load inventory data');
      setAllItems([]);
      setItems([]);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  }, [fetchItems, range]);

  // Reload when range, search, or reloadKey changes
  useEffect(() => {
    doLoad(activeSearch);
  }, [rangeIndex, activeSearch, reloadKey, doLoad]);

  // Client-side page change
  const goToPage = useCallback((p) => {
    setPage(p);
    const start = (p - 1) * PAGE_SIZE;
    setItems(allItems.slice(start, start + PAGE_SIZE));
  }, [allItems]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setActiveSearch(val);
    }, 400);
  };

  const handleRangeChange = (e) => {
    const idx = Number(e.target.value);
    setRangeIndex(idx);
    setActiveSearch('');
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
                      <span className={cn('font-sans font-bold text-sm', book.stockQuantity === 0 && 'text-destructive', book.stockQuantity > 0 && range && book.stockQuantity <= (range.max ?? Infinity) && 'text-amber-600')}>
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
          <Button variant='outline' disabled={!hasPrev} onClick={() => goToPage(page - 1)} className='h-9 rounded-lg'>Previous</Button>
          <span className='text-sm text-primary/40'>Page {page} of {totalPages}</span>
          <Button variant='outline' disabled={!hasNext} onClick={() => goToPage(page + 1)} className='h-9 rounded-lg'>Next</Button>
        </div>
      )}
    </div>
  );
}
