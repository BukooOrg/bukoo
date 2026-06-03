import { SearchIcon } from 'lucide-react';
import React, { useRef, useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';

import { useTypewriterPlaceholder } from '@/hooks/useTypewriterPlaceholder';
import { bookApi } from '@/lib/apiClient';

const PLACEHOLDER_PHRASES = [
  'Search for books, authors, or ISBN...',
  'Find your next great read...',
  'Explore our collection...',
  'What story are you looking for?',
  'Discover new arrivals...',
];

export default function Search() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const containerRef = useRef(null);
  const [value, setValue] = useState(searchParams.get('q') || '');
  const [focused, setFocused] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const debounceRef = useRef(null);

  const placeholder = useTypewriterPlaceholder(PLACEHOLDER_PHRASES, {
    typingSpeed: 40,
    deleteSpeed: 25,
    pauseDuration: 1500,
    paused: focused || value.length > 0,
  });

  useEffect(() => {
    const initial = searchParams.get('q') || '';
    setValue(initial);
  }, [searchParams]);

  useEffect(() => {
    if (!value.trim() || !focused) {
      setSuggestions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setSuggestLoading(true);
      try {
        const res = await bookApi.findBooks({ search: value.trim(), page: 1, pageSize: 5 });
        const items = res.data?.items || [];
        setSuggestions(
          items.sort((a, b) => {
            if (a.coverUrl && !b.coverUrl) return -1;
            if (!a.coverUrl && b.coverUrl) return 1;
            return 0;
          })
        );
      } catch {
        setSuggestions([]);
      }
      setSuggestLoading(false);
    }, 200);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, focused]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) {
      navigate(`/search?q=${encodeURIComponent(value.trim())}`);
      inputRef.current?.blur();
    }
  };

  const handleSuggestionClick = () => {
    inputRef.current?.blur();
    setSuggestions([]);
  };

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setSuggestions([]);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={containerRef} className='relative w-full group'>
      <form onSubmit={handleSubmit} className='relative'>
        <input
          ref={inputRef}
          type='text'
          name='q'
          placeholder={placeholder}
          autoComplete='off'
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className='w-full px-5 py-3 !text-black placeholder:!text-black/50 bg-transparent rounded-xl focus:outline-none focus:ring-1 focus:ring-black/10 font-sans font-medium text-base md:text-lg tracking-tight transition-colors caret-black'
        />

        <button type='submit' className='absolute right-0 top-0 mr-3 flex h-full items-center'>
          <SearchIcon className='size-4 text-gray-400 group-focus-within:text-black transition-colors' />
        </button>
      </form>

      {focused && value.trim() && (
        <div className='absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden z-50'>
          {suggestLoading ? (
            <div className='px-4 py-4 flex items-center gap-3'>
              <div className='size-4 border-2 border-gray-200 border-t-black rounded-full animate-spin' />
              <span className='text-xs font-medium text-gray-500'>Searching...</span>
            </div>
          ) : suggestions.length > 0 ? (
            suggestions.map((book) => (
              <Link
                key={book.id}
                to={`/product/${book.id}`}
                onClick={handleSuggestionClick}
                className='flex items-center gap-3 px-4 py-3 hover:bg-gray-100 transition-colors border-b border-gray-100 last:border-b-0'>
                {book.coverUrl && (
                  <img
                    src={book.coverUrl}
                    alt=''
                    referrerpolicy='no-referrer'
                    className='w-9 h-13 object-contain rounded-sm shrink-0 bg-gray-100'
                  />
                )}
                <div className='min-w-0 flex-1'>
                  <p className='text-sm font-bold text-black truncate'>{book.title}</p>
                  <p className='text-xs text-gray-500 truncate'>
                    {book.authors?.map((a) => a.name).join(', ') || 'Bukoo Editions'}
                  </p>
                </div>
              </Link>
            ))
          ) : (
            <div className='px-4 py-4 text-xs font-medium text-gray-400 text-center'>
              No results found for &ldquo;{value}&rdquo;
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function SearchSkeleton() {
  return (
    <div className='w-max-[550px] relative w-full lg:w-80 xl:w-full'>
      <input
        placeholder='Search for products...'
        className='w-full rounded-lg border bg-white px-4 py-2 text-sm text-black placeholder:text-neutral-500 dark:border-neutral-800 dark:bg-transparent dark:text-white dark:placeholder:text-neutral-400'
        readOnly
      />
      <div className='absolute right-0 top-0 mr-3 flex h-full items-center'>
        <SearchIcon className='h-4' />
      </div>
    </div>
  );
}
