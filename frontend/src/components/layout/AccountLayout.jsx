import {
  User,
  Lock,
  MapPin,
  ShoppingCart,
  Star,
  Bell,
  AlertTriangle,
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
  { to: '/account/password', label: 'Password', icon: Lock },
  { to: '/account/address', label: 'Address', icon: MapPin },
  { to: '/account/orders', label: 'Orders', icon: ShoppingCart },
  { to: '/account/reviews', label: 'Reviews', icon: Star },
  { to: '/account/notifications', label: 'Notifications', icon: Bell },
  { to: '/account/delete', label: 'Delete Account', icon: AlertTriangle, danger: true },
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
          {mobileOpen ? <X className='w-6 h-6' /> : <Menu className='w-6 h-6' />}
        </button>
        <span className='font-serif text-xl font-bold text-primary'>My Account</span>
        <div />
      </div>

      <div className='flex'>
        {/* Sidebar */}
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-border p-6 transition-transform duration-300 md:relative md:translate-x-0 md:inset-auto',
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}>
          {/* User info */}
          <div className='flex items-center gap-3 p-3 mb-6 rounded-xl bg-primary/5'>
            <Avatar className='w-10 h-10 border-2 border-primary/20'>
              <AvatarImage src={user?.avatarUrl} alt={user?.fullName} />
              <AvatarFallback className='font-bold text-sm bg-primary text-background'>
                {user?.fullName?.charAt(0)?.toUpperCase() ?? 'U'}
              </AvatarFallback>
            </Avatar>
            <div className='min-w-0'>
              <p className='text-sm font-bold truncate text-primary'>{user?.fullName}</p>
              <p className='text-xs truncate text-muted-foreground'>{user?.email}</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className='space-y-1'>
            {navItems.map((item) => {
              const isActive = location.pathname === item.to;
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    item.danger
                      ? 'text-destructive hover:bg-destructive/5'
                      : 'text-primary/70 hover:bg-primary/5 hover:text-primary',
                    isActive && !item.danger && 'bg-primary/10 text-primary font-bold',
                    isActive && item.danger && 'bg-destructive/10 text-destructive font-bold'
                  )}>
                  <Icon className='w-5 h-5 shrink-0' />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Back to home */}
          <div className='mt-8 pt-6 border-t border-border'>
            <Link
              to='/'
              className='flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
              ← Back to Store
            </Link>
          </div>
        </aside>

        {/* Mobile overlay */}
        {mobileOpen && (
          <div
            className='fixed inset-0 z-40 bg-black/20 md:hidden'
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Content */}
        <main className='flex-1 p-6 md:p-10 max-w-4xl'>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
