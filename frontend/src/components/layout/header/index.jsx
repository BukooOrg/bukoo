import { Heart, UserIcon } from 'lucide-react';
import { LogOut } from 'lucide-react';
import { Shield } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import CartModal from '@/components/cart/CartModal';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/overlays/dropdown-menu';
import { useWishlist } from '@/components/wishlist/WishlistContext';
import { useAuth } from '@/context/AuthContext';
import { getCollections } from '@/lib/sfcc';

import MobileMenu from './MobileMenu';
import Search from './Search';

export function Header() {
  const [collections, setCollections] = useState([]);
  const { user, logout } = useAuth();
  const { wishlist } = useWishlist();

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
          {user?.role !== 'admin' && (
            <Link
              to='/account/wishlist'
              className='relative transition-colors text-black hover:bg-gray-100 rounded-full p-2'>
              <Heart className='size-5' />
              {(wishlist?.items?.length || 0) > 0 && (
                <span className='absolute -top-0.5 -right-0.5 size-4 flex items-center justify-center text-[9px] font-bold bg-black text-white rounded-full'>
                  {wishlist.items.length}
                </span>
              )}
            </Link>
          )}

          {user?.role !== 'admin' && <CartModal />}

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

                {user?.role !== 'admin' && (
                  <DropdownMenuItem asChild className='cursor-pointer'>
                    <Link to='/account/profile'>
                      <UserIcon className='mr-2 size-4' />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                )}

                {user?.role === 'admin' && (
                  <DropdownMenuItem asChild className='cursor-pointer'>
                    <Link to='/admin'>
                      <Shield className='mr-2 size-4' />
                      Admin
                    </Link>
                  </DropdownMenuItem>
                )}

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
    </header>
  );
}
