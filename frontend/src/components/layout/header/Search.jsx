import { SearchIcon } from 'lucide-react';
import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function Search() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const q = formData.get('q');
    if (q) {
      navigate(`/search?q=${encodeURIComponent(q)}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} className='relative w-full group'>
      <input
        key={searchParams.get('q')}
        type='text'
        name='q'
        placeholder='Search for books, authors, or ISBN...'
        autoComplete='off'
        defaultValue={searchParams.get('q') || ''}
        className='w-full bg-transparent px-4 py-2 text-primary placeholder:text-primary/40 focus:outline-none font-sans font-medium text-xs md:text-sm tracking-tight'
      />

      <button type='submit' className='absolute right-0 top-0 mr-3 flex h-full items-center'>
        <SearchIcon className='h-4 text-primary/40 group-focus-within:text-primary transition-colors' />
      </button>
    </form>
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
