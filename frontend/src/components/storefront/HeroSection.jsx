import { motion } from 'motion/react';
import { useEffect, useState } from 'react';

import mockProducts from '@/data/mock/products.json';
import { bookApi } from '@/lib/apiClient';
import { fromApiBooks, reshapeProducts } from '@/lib/sfcc/utils';
import { cn } from '@/lib/utils';

const MARQUEE_SPEED_LEFT = 80;
const MARQUEE_SPEED_RIGHT = 110;
const BOOKS_PER_COLUMN = 12;

function getBooks() {
  const mockBooks = reshapeProducts(mockProducts);
  return mockBooks
    .filter((b) => b.featuredImage?.url && b.featuredImage.url.length > 0)
    .slice(0, BOOKS_PER_COLUMN);
}

function MarqueeColumn({ books, speed, className }) {
  return (
    <div className={cn('relative overflow-hidden', className)}>
      <motion.div
        initial={{ y: 0 }}
        animate={{ y: '-100%' }}
        transition={{
          duration: speed,
          repeat: Infinity,
          ease: 'linear',
        }}
        className='flex flex-col gap-4'>
        {[...books, ...books]
          .filter((book) => book.featuredImage?.url && book.featuredImage.url.length > 0)
          .map((book, i) => (
            <div
              key={`${book.id}-${i}`}
              className='w-full aspect-[2/3] rounded-lg overflow-hidden shadow-md bg-gray-100 border border-secondary/20 flex-shrink-0 hover:scale-105 transition-transform duration-300'>
              <img
                src={book.featuredImage.url}
                alt={book.featuredImage.altText || book.title}
                referrerPolicy='no-referrer'
                className='w-full h-full object-contain'
                draggable={false}
              />
            </div>
          ))}
      </motion.div>
      {/* Fade edges */}
      <div className='pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-background to-transparent z-10' />
      <div className='pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-background to-transparent z-10' />
    </div>
  );
}

export function HeroSection() {
  const [books, setBooks] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await bookApi.findBooks({
          status: 'activate',
          page: 1,
          pageSize: 50,
        });
        const items = fromApiBooks(res.data?.items || []);
        const withCover = items.filter(
          (b) => b.featuredImage?.url && b.featuredImage.url.length > 0
        );
        setBooks(withCover.length > 0 ? withCover.slice(0, BOOKS_PER_COLUMN) : getBooks());
      } catch {
        setBooks(getBooks());
      }
    }
    load();
  }, []);

  if (books.length === 0) return null;

  const leftBooks = books.slice(0, Math.ceil(books.length / 2));
  const rightBooks = books.slice(Math.ceil(books.length / 2));

  return (
    <section className='relative min-h-screen bg-background overflow-hidden'>
      <div className='max-w-[1440px] mx-auto px-sides h-full min-h-screen flex flex-col lg:flex-row items-start gap-8 lg:gap-16 pt-0 lg:pt-0'>
        {/* Left: Logo + Editorial */}
        <div className='flex-1 flex flex-col justify-start z-10 lg:pt-20 lg:pb-24 pt-12'>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}>
            <span className='text-7xl md:text-8xl font-serif font-black tracking-tight text-primary'>
              Bukoo.
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15, ease: 'easeOut' }}
            className='font-serif text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-primary max-w-lg'>
            Where every page begins a conversation.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: 'easeOut' }}
            className='mt-6 text-base md:text-lg font-sans text-muted-foreground max-w-md leading-relaxed'>
            Curated shelves of fiction, non-fiction, and rare finds — handpicked for readers who
            seek more than just a story.
          </motion.p>
        </div>

        {/* Right: Scrolling Book Marquee */}
        <div className='flex-1 relative h-[60vh] lg:h-[80vh] lg:self-stretch lg:my-0'>
          <div className='grid grid-cols-2 gap-4 h-full'>
            {leftBooks.length > 0 && <MarqueeColumn books={leftBooks} speed={MARQUEE_SPEED_LEFT} />}
            {rightBooks.length > 0 && (
              <MarqueeColumn books={rightBooks} speed={MARQUEE_SPEED_RIGHT} />
            )}
          </div>
        </div>
      </div>

      {/* Bottom fade for clean transition into product grid */}
      <div className='absolute bottom-0 inset-x-0 h-32 bg-gradient-to-b from-transparent to-background pointer-events-none z-20' />
    </section>
  );
}
