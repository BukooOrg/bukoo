import { BookOpen } from 'lucide-react';
import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className='min-h-screen bg-background flex items-center justify-center px-sides'>
      <div className='text-center max-w-md'>
        <div className='flex justify-center mb-6'>
          <div className='w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center'>
            <BookOpen className='w-10 h-10 text-primary/40' />
          </div>
        </div>
        <h1 className='text-5xl font-serif font-black mb-3 text-primary tracking-tighter'>404</h1>
        <p className='font-serif text-2xl italic text-primary/40 mb-2'>Chapter Not Found</p>
        <p className='text-primary/40 font-bold text-sm mb-8'>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to='/'
          className='inline-flex items-center gap-3 py-5 px-8 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
          <BookOpen className='w-5 h-5' />
          <span>Back to Home</span>
        </Link>
      </div>
    </div>
  );
}
