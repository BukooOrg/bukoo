import {
  User,
  Lock,
  MapPin,
  ShoppingCart,
  Star,
  Bell,
  LayoutDashboard,
  Menu,
  X,
} from 'lucide-react';
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/account', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/account/profile', label: 'Profile', icon: User },
  { to: '/account/address', label: 'Address', icon: MapPin },
  { to: '/account/orders', label: 'Orders', icon: ShoppingCart },
  { to: '/account/reviews', label: 'Reviews', icon: Star },
  { to: '/account/notifications', label: 'Notifications', icon: Bell },
  { to: '/account/password', label: 'Password', icon: Lock },
];

export function AccountLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className='min-h-screen bg-background'>
      {/* Mobile header */}
      <div className='flex items-center justify-between p-4 border-b md:hidden'>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className='p-2 rounded-lg hover:bg-primary/5'>
          {mobileOpen ? <X className='w-5 h-5' /> : <Menu className='w-5 h-5' />}
        </button>
        <span className='font-serif text-lg font-bold text-primary'>My Account</span>
        <div />
      </div>

      <div className='flex'>
        {/* Sidebar — below fixed header, full remaining height */}
        <aside
          className={cn(
            'fixed left-0 z-50 w-80 bg-white border-r border-border flex flex-col transition-transform duration-300 md:w-96 top-24 md:top-32 h-[calc(100vh-6rem)] md:h-[calc(100vh-8rem)]',
            mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          )}>
          <div className='flex flex-col h-full p-8'>
            {/* User info — pinned top */}
            <div className='flex items-center gap-4 p-4 mb-8 rounded-xl bg-primary/5 shrink-0'>
              <Avatar className='w-12 h-12 border-2 border-primary/20'>
                <AvatarImage src={user?.avatarUrl} alt={user?.fullName} />
                <AvatarFallback className='font-bold text-base bg-primary text-background'>
                  {user?.fullName?.charAt(0)?.toUpperCase() ?? 'U'}
                </AvatarFallback>
              </Avatar>
              <div className='min-w-0'>
                <p className='text-base font-sans font-bold truncate text-primary'>
                  {user?.fullName}
                </p>
                <p className='text-sm font-sans truncate text-muted-foreground'>{user?.email}</p>
              </div>
            </div>

            {/* Navigation — scrollable middle */}
            <nav className='space-y-1.5 flex-1 overflow-y-auto'>
              {navItems.map((item) => {
                const isActive = location.pathname === item.to;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      'flex items-center gap-3.5 px-4 py-3 rounded-lg text-base font-sans font-medium leading-relaxed transition-colors',
                      'text-primary/70 hover:bg-primary/5 hover:text-primary',
                      isActive && 'bg-primary/10 text-primary font-bold'
                    )}>
                    <Icon className='w-5 h-5 shrink-0' />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Back to home — pinned bottom */}
            <div className='pt-6 mt-6 border-t border-border shrink-0'>
              <Link
                to='/'
                className='flex items-center gap-2 text-sm font-sans font-bold uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
                ← Back to Store
              </Link>
            </div>
          </div>
        </aside>

        {/* Mobile overlay */}
        {mobileOpen && (
          <div
            className='fixed inset-0 z-40 bg-black/20 md:hidden'
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Content — centered, offset for fixed sidebar on desktop */}
        <main className='flex-1 p-6 pt-24 md:p-10 md:pt-32 md:ml-96 mx-auto max-w-5xl w-full'>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
