import {
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  ChevronLeft,
  ChevronRight,
  FolderTree,
  LayoutDashboard,
  Library,
  MessageSquare,
  Package,
  UserPlus,
  Users,
  Warehouse,
} from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

import { SkipLink } from '@/components/ui/misc/skip-link';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/overlays/tooltip';
import { useSidebarCollapse } from '@/hooks/useSidebarCollapse';
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
    label: 'Inventory & Reports',
    items: [
      { to: '/admin/inventory', label: 'Inventory', icon: Warehouse },
      { to: '/admin/reports', label: 'Reports', icon: BarChart3 },
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
    label: 'Notifications',
    items: [{ to: '/admin/notifications', label: 'Notifications', icon: Bell }],
  },
];

const SIDEBAR_WIDTH_EXPANDED = 'w-80 md:w-96';
const SIDEBAR_WIDTH_COLLAPSED = 'w-16';
const MAIN_MARGIN_EXPANDED = 'md:ml-96';
const MAIN_MARGIN_COLLAPSED = 'md:ml-16';

export function AdminLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { collapsed, toggleCollapsed } = useSidebarCollapse();

  return (
    <TooltipProvider delayDuration={0}>
      <div className='min-h-screen font-sans antialiased bg-background text-foreground'>
        <SkipLink />
        <Header shouldRenderSearchBar={false} />

        <div className='flex'>
          {/* Sidebar — below fixed header */}
          <aside
            className={cn(
              'fixed left-0 z-40 bg-white border-r border-border flex flex-col transition-all duration-300 top-24 md:top-32 h-[calc(100vh-6rem)] md:h-[calc(100vh-8rem)]',
              collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED,
              mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
            )}>
            <div
              className={cn(
                'flex flex-col h-full transition-all duration-300',
                collapsed ? 'p-2' : 'p-4 md:p-8'
              )}>
              {/* Brand + Collapse toggle */}
              <div
                className={cn(
                  'shrink-0 flex items-center justify-between transition-all duration-300',
                  collapsed ? 'mb-2' : 'mb-6 md:mb-8'
                )}>
                {!collapsed && (
                  <p className='text-xs font-black uppercase tracking-[0.2em] text-primary/40'>
                    Admin
                  </p>
                )}

                {/* Collapse toggle — desktop only */}
                <button
                  onClick={toggleCollapsed}
                  aria-expanded={!collapsed}
                  aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                  className={cn(
                    'hidden md:flex items-center justify-center w-8 h-8 rounded-lg hover:bg-primary/5 transition-colors shrink-0',
                    collapsed && 'mx-auto'
                  )}>
                  {collapsed ? (
                    <ChevronRight className='w-4 h-4 text-primary/40' />
                  ) : (
                    <ChevronLeft className='w-4 h-4 text-primary/40' />
                  )}
                </button>
              </div>

              {/* Navigation — scrollable */}
              <nav
                className={cn(
                  'flex-1 overflow-y-auto transition-all duration-300',
                  collapsed ? 'space-y-2' : 'space-y-4 md:space-y-6'
                )}>
                {sections.map((section) => (
                  <div key={section.label}>
                    {!collapsed && (
                      <p className='mb-2 px-3 text-[10px] font-black uppercase tracking-[0.2em] text-primary/30'>
                        {section.label}
                      </p>
                    )}

                    <div className={cn('space-y-1', collapsed && 'space-y-0.5')}>
                      {section.items.map((item) => {
                        const isActive =
                          location.pathname === item.to ||
                          (item.to !== '/admin' && location.pathname.startsWith(item.to + '/'));
                        const Icon = item.icon;

                        if (collapsed) {
                          return (
                            <Tooltip key={item.to}>
                              <TooltipTrigger asChild>
                                <Link
                                  to={item.to}
                                  onClick={() => setMobileOpen(false)}
                                  className='flex items-center justify-center p-3 transition-colors rounded-lg cursor-pointer text-primary/70 hover:bg-primary/5 hover:text-primary'>
                                  <Icon className='w-5 h-5 shrink-0' />
                                </Link>
                              </TooltipTrigger>
                              <TooltipContent side='right' align='center' sideOffset={8}>
                                {item.label}
                              </TooltipContent>
                            </Tooltip>
                          );
                        }

                        return (
                          <Link
                            key={item.to}
                            to={item.to}
                            onClick={() => setMobileOpen(false)}
                            className={cn(
                              'flex items-center gap-3.5 px-4 py-3 rounded-lg text-base font-sans font-medium leading-relaxed transition-colors cursor-pointer text-primary/70 hover:bg-primary/5 hover:text-primary',
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
              <div
                className={cn(
                  'border-t border-border shrink-0 transition-all duration-300',
                  collapsed ? 'pt-2 mt-2' : 'pt-4 md:pt-6 mt-4 md:mt-6'
                )}>
                {collapsed ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        to='/'
                        className='flex items-center justify-center p-3 transition-colors rounded-lg cursor-pointer text-primary/40 hover:text-primary hover:bg-primary/5'>
                        <span className='text-base'>←</span>
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side='right' align='center' sideOffset={8}>
                      Back to Store
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Link
                    to='/'
                    className='flex items-center gap-2 font-sans text-sm font-bold tracking-widest uppercase transition-colors text-primary/40 hover:text-primary'>
                    ← Back to Store
                  </Link>
                )}
              </div>
            </div>
          </aside>

          {/* Mobile overlay */}
          {mobileOpen && (
            <div
              className='fixed inset-0 z-30 bg-primary/20 md:hidden'
              onClick={() => setMobileOpen(false)}
            />
          )}

          {/* Main content — offset for sidebar, full width */}
          <main
            id='main-content'
            className={cn(
              'flex-1 p-6 pt-24 md:p-10 md:pt-32 transition-all duration-300',
              collapsed ? MAIN_MARGIN_COLLAPSED : MAIN_MARGIN_EXPANDED
            )}>
            <motion.div
              initial={{ y: 6 }}
              animate={{ y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.1, ease: 'easeOut' }}>
              <Outlet />
            </motion.div>
          </main>
        </div>
        <Toaster closeButton position='bottom-right' />
      </div>
    </TooltipProvider>
  );
}
