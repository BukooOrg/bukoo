import { UserIcon } from 'lucide-react';
import { LogOut } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

import CartModal from '@/components/cart/CartModal';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/overlays/dropdown-menu';
import { useAuth } from '@/context/AuthContext';
import { getCollections } from '@/lib/sfcc';
import { cn } from '@/lib/utils';

import MobileMenu from './MobileMenu';
import Search from './Search';

export function Header() {
  const { pathname } = useLocation();
  const [collections, setCollections] = useState([]);
  const { user, logout } = useAuth();

  useEffect(() => {
    async function loadCollections() {
      const data = await getCollections();
      setCollections(data);
    }
    loadCollections();
  }, []);

  return (
    <header className='fixed top-0 left-0 z-50 w-full transition-all duration-300'>
      {/* Primary Header Row */}
      <div className='flex items-center h-24 border-b p-sides bg-background/80 backdrop-blur-2xl border-secondary/20 md:h-32 gap-sides'>
        <div className='flex-none mr-4 md:hidden'>
          <MobileMenu collections={collections} />
        </div>

        {/* Large Logo */}
        <Link to='/' className='flex-none'>
          <span className='font-serif text-5xl font-black tracking-tighter md:text-7xl text-primary'>
            Bukoo
          </span>
        </Link>

        {/* Wide Search Bar (Centered/Expanded) */}
        <div className='flex justify-center flex-1 md:px-12 max-md:hidden'>
          <div className='w-full max-w-3xl px-6 py-2 border rounded-full bg-secondary/80 border-secondary/30 backdrop-blur-md'>
            <Search />
          </div>
        </div>

        {/* Action Buttons (Right) */}
        <nav className='flex items-center gap-4 ml-auto md:gap-8'>
          <CartModal />

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className='transition-all rounded-full outline-none ring-offset-background hover:scale-105 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2'>
                  <Avatar className='border shadow-lg size-12 border-secondary/30'>
                    <AvatarImage src={user.avatarUrl} alt={user.fullName} />

                    <AvatarFallback className='font-bold bg-primary text-background'>
                      {user.fullName?.charAt(0)?.toUpperCase() ?? 'U'}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>

              <DropdownMenuContent
                align='end'
                className='w-56 mt-2 rounded-2xl border-secondary/20 backdrop-blur-xl'>
                <div className='px-3 py-2 border-b border-secondary/10'>
                  <p className='text-sm font-semibold'>{user.fullName}</p>
                  <p className='text-xs truncate text-muted-foreground'>{user.email}</p>
                </div>

                <DropdownMenuItem asChild className='cursor-pointer'>
                  <Link to='/account/profile'>
                    <UserIcon className='mr-2 size-4' />
                    Profile
                  </Link>
                </DropdownMenuItem>

                <DropdownMenuItem
                  onClick={logout}
                  className='cursor-pointer text-destructive focus:text-destructive'>
                  <LogOut className='mr-2 size-4' />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link
              to='/login'
              className='flex items-center gap-2 px-8 py-4 bg-primary text-background rounded-full font-sans font-bold text-[10px] uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl'>
              <UserIcon className='size-4' />
              <span className='hidden lg:inline'>Login / Sign Up</span>
            </Link>
          )}
        </nav>
      </div>

      {/* Genre Header Row */}
      <div className='flex items-center justify-center h-12 border-b bg-background/60 backdrop-blur-xl border-secondary/15 md:h-16'>
        <ul className='flex items-center gap-10 overflow-x-auto md:gap-16 no-scrollbar px-sides'>
          {collections
            .filter((c) => c.handle !== 'joyco-root')
            .map((item) => (
              <li key={item.handle}>
                <Link
                  to={`/shop/${item.handle}`}
                  className={cn(
                    'text-[11px] md:text-sm font-sans font-black uppercase tracking-[0.25em] transition-all hover:opacity-100',
                    pathname.includes(item.handle)
                      ? 'opacity-100 text-primary scale-110'
                      : 'opacity-40'
                  )}>
                  {item.title}
                </Link>
              </li>
            ))}
        </ul>
      </div>
    </header>
  );
}
