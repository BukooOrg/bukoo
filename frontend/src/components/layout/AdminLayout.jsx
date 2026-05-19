import {
  LayoutDashboard,
  BookOpen,
  Library,
  FolderTree,
  Users,
  UserPlus,
  Building2,
  Package,
  MessageSquare,
  Bell,
  Warehouse,
  BarChart3,
} from 'lucide-react';
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

import { cn } from '@/lib/utils';

import { Header } from './header';

const sections = [
  {
    label: 'Dashboard',
    items: [{ to: '/admin', label: 'Overview', icon: LayoutDashboard }],
  },
  {
    label: 'Catalog',
    items: [
      { to: '/admin/books', label: 'Books', icon: BookOpen },
      { to: '/admin/collections', label: 'Collections', icon: Library },
      { to: '/admin/categories', label: 'Categories', icon: FolderTree },
      { to: '/admin/authors', label: 'Authors', icon: Users },
      { to: '/admin/publishers', label: 'Publishers', icon: Building2 },
    ],
  },
  {
    label: 'Users',
    items: [
      { to: '/admin/users', label: 'Manage Users', icon: Users },
      { to: '/admin/users/new', label: 'New User', icon: UserPlus },
    ],
  },
  {
    label: 'Orders & Reviews',
    items: [
      { to: '/admin/orders', label: 'Orders', icon: Package },
      { to: '/admin/reviews', label: 'Reviews', icon: MessageSquare },
    ],
  },
  {
    label: 'Inventory & Reports',
    items: [
      { to: '/admin/inventory', label: 'Inventory', icon: Warehouse },
      { to: '/admin/reports', label: 'Reports', icon: BarChart3 },
    ],
  },
  {
    label: 'Notifications',
    items: [{ to: '/admin/notifications', label: 'Notifications', icon: Bell }],
  },
];

export function AdminLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className='min-h-screen font-sans antialiased bg-background text-foreground'>
      <Header />

      <div className='flex'>
        {/* Sidebar — below fixed header */}
        <aside
          className={cn(
            'fixed left-0 z-40 w-80 bg-white border-r border-border flex flex-col transition-transform duration-300 md:w-96 top-24 md:top-32 h-[calc(100vh-6rem)] md:h-[calc(100vh-8rem)]',
            mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          )}>
          <div className='flex flex-col h-full p-8'>
            {/* Brand */}
            <div className='mb-8 shrink-0'>
              <p className='text-xs font-black uppercase tracking-[0.2em] text-primary/40'>Admin</p>
            </div>

            {/* Navigation — scrollable */}
            <nav className='flex-1 overflow-y-auto space-y-6'>
              {sections.map((section) => (
                <div key={section.label}>
                  <p className='mb-2 px-3 text-[10px] font-black uppercase tracking-[0.2em] text-primary/30'>
                    {section.label}
                  </p>
                  <div className='space-y-1.5'>
                    {section.items.map((item) => {
                      const isActive =
                        location.pathname === item.to ||
                        (item.to !== '/admin' && location.pathname.startsWith(item.to + '/'));
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
                  </div>
                </div>
              ))}
            </nav>

            {/* Bottom */}
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
            className='fixed inset-0 z-30 bg-black/20 md:hidden'
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Main content — offset for sidebar */}
        <main className='flex-1 p-6 pt-24 md:p-10 md:pt-32 md:ml-96 mx-auto max-w-5xl w-full'>
          <Outlet />
        </main>
      </div>
      <Toaster closeButton position='bottom-right' />
    </div>
  );
}
