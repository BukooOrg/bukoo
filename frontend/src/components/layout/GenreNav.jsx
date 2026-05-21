import { ChevronDown } from 'lucide-react';
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';

import { cn } from '@/lib/utils';

const MAIN_SLUGS = new Set(['fiction', 'non-fiction', 'business-finance', 'academic-textbooks']);

const MAIN_ORDER = ['fiction', 'non-fiction', 'business-finance', 'academic-textbooks'];

export function GenreNav({ collections, activeHandle }) {
  const [moreOpen, setMoreOpen] = useState(false);
  const [dropdownStyle, setDropdownStyle] = useState({});
  const triggerRef = useRef(null);

  const openDropdown = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setDropdownStyle({
        position: 'fixed',
        top: rect.bottom + 8,
        left: rect.left,
        zIndex: 99999,
      });
    }
    setMoreOpen(true);
  };

  useEffect(() => {
    if (!moreOpen) return;
    function handleClickOutside(e) {
      if (triggerRef.current && !triggerRef.current.contains(e.target)) {
        const dropdown = document.getElementById('genre-more-dropdown');
        if (dropdown && !dropdown.contains(e.target)) {
          setMoreOpen(false);
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [moreOpen]);

  const mainCollections = collections
    .filter((c) => MAIN_SLUGS.has(c.handle))
    .sort((a, b) => MAIN_ORDER.indexOf(a.handle) - MAIN_ORDER.indexOf(b.handle));

  const moreCollections = collections.filter((c) => !MAIN_SLUGS.has(c.handle));

  return (
    <div className='flex items-center justify-center h-12 border-b bg-background/60 backdrop-blur-xl border-secondary/15 md:h-14 px-4'>
      <ul className='flex items-center gap-6 md:gap-10'>
        {mainCollections.map((item) => (
          <li key={item.handle}>
            <Link
              to={`/shop/${item.handle}`}
              className={cn(
                'text-[10px] md:text-sm font-sans font-black uppercase tracking-[0.2em] transition-all hover:opacity-100 whitespace-nowrap',
                item.handle === activeHandle
                  ? 'opacity-100 text-primary scale-110 inline-block'
                  : 'opacity-40'
              )}>
              {item.title}
            </Link>
          </li>
        ))}

        {moreCollections.length > 0 && (
          <li ref={triggerRef}>
            <button
              type='button'
              onClick={moreOpen ? () => setMoreOpen(false) : openDropdown}
              className='flex items-center gap-0.5 text-[10px] md:text-sm font-sans font-black uppercase tracking-[0.2em] transition-all hover:opacity-100 whitespace-nowrap opacity-40'>
              More
              <ChevronDown
                className={cn('w-3 h-3 transition-transform', moreOpen && 'rotate-180')}
              />
            </button>
          </li>
        )}
      </ul>

      {moreOpen &&
        createPortal(
          <div
            id='genre-more-dropdown'
            style={dropdownStyle}
            className='py-3 px-5 bg-white border border-border shadow-2xl rounded-xl min-w-[220px]'>
            <ul className='space-y-0.5'>
              {moreCollections.map((item) => (
                <li key={item.handle}>
                  <Link
                    to={`/shop/${item.handle}`}
                    onClick={() => setMoreOpen(false)}
                    className='block py-2 px-3 text-[10px] md:text-sm font-sans font-black uppercase tracking-[0.2em] text-primary/70 hover:text-primary hover:bg-primary/5 rounded-lg transition-colors whitespace-nowrap'>
                    {item.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>,
          document.body
        )}
    </div>
  );
}
