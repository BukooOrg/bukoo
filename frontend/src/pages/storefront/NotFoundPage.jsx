import { BookOpen } from 'lucide-react';
import { motion } from 'motion/react';
import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.1, ease: 'easeOut' }}
      className='min-h-screen bg-background flex items-center justify-center px-sides'>
      <div className='text-center max-w-md'>
        <div className='flex justify-center mb-6'>
          <div className='w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center'>
            <BookOpen className='w-10 h-10 text-gray-400' />
          </div>
        </div>
        <h1 className='text-5xl font-sans font-bold mb-3 text-black tracking-tight'>404</h1>
        <p className='font-sans text-xl text-gray-500 mb-2'>Chapter Not Found</p>
        <p className='text-gray-500 text-sm mb-8'>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to='/'
          className='inline-flex items-center gap-3 py-4 px-8 border-2 border-black text-black bg-transparent rounded-2xl font-sans font-bold uppercase tracking-[0.2em] hover:bg-black hover:text-white transition-all'>
          <BookOpen className='w-5 h-5' />
          <span>Back to Home</span>
        </Link>
      </div>
    </motion.div>
  );
}
