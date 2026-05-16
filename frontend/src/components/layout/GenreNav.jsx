import React from 'react';
import { Link } from 'react-router-dom';

import { cn } from '@/lib/utils';

export function GenreNav({ collections, activeHandle }) {
  return (
    <div className='flex items-center justify-center h-12 border-b bg-background/60 backdrop-blur-xl border-secondary/15 md:h-14'>
      <ul className='flex items-center gap-8 overflow-x-auto md:gap-12 no-scrollbar'>
        {collections
          .filter((c) => c.handle !== 'joyco-root')
          .map((item) => (
            <li key={item.handle}>
              <Link
                to={`/shop/${item.handle}`}
                className={cn(
                  'text-[11px] md:text-sm font-sans font-black uppercase tracking-[0.25em] transition-all hover:opacity-100 whitespace-nowrap',
                  item.handle === activeHandle ? 'opacity-100 text-primary scale-110' : 'opacity-40'
                )}>
                {item.title}
              </Link>
            </li>
          ))}
      </ul>
    </div>
  );
}
