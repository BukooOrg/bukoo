import {
  Bell,
  ChevronLeft,
  ChevronRight,
  Heart,
  LayoutDashboard,
  Lock,
  MapPin,
  Menu,
  ShoppingBag,
  ShoppingCart,
  Star,
  User,
  X,
} from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import { SkipLink } from '@/components/ui/misc/skip-link';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/overlays/tooltip';
import { useAuth } from '@/context/AuthContext';
import { useSidebarCollapse } from '@/hooks/useSidebarCollapse';
import { cn } from '@/lib/utils';

import { Header } from './header';

const navItems = [
  { to: '/account', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/account/profile', label: 'Profile', icon: User },
  { to: '/account/address', label: 'Address', icon: MapPin },
  { to: '/account/wishlist', label: 'Wishlist', icon: Heart },
  { to: '/account/cart', label: 'Cart', icon: ShoppingBag },
  { to: '/account/orders', label: 'Orders', icon: ShoppingCart },
  { to: '/account/reviews', label: 'Reviews', icon: Star },
  { to: '/account/notifications', label: 'Notifications', icon: Bell },
  { to: '/account/password', label: 'Password', icon: Lock },
];

const SIDEBAR_WIDTH_EXPANDED = 'w-80 md:w-96';
const SIDEBAR_WIDTH_COLLAPSED = 'w-16';
const MAIN_MARGIN_EXPANDED = 'md:ml-96';
const MAIN_MARGIN_COLLAPSED = 'md:ml-16';

export function AccountLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { collapsed, toggleCollapsed } = useSidebarCollapse();

  return (
    <TooltipProvider delayDuration={0}>
      <div className='min-h-screen bg-background'>
        <SkipLink />
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

        <Header shouldRenderSearchBar={false} />
        <div className='flex'>
          {/* Sidebar — below fixed header, full remaining height */}
          <aside
            className={cn(
              'fixed left-0 z-50 bg-white border-r border-border flex flex-col transition-all duration-300 top-24 md:top-32 h-[calc(100vh-6rem)] md:h-[calc(100vh-8rem)]',
              collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED,
              mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
            )}>
            <div
              className={cn(
                'flex flex-col h-full transition-all duration-300',
                collapsed ? 'p-2' : 'p-4 md:p-8'
              )}>
              {/* User info — expanded only */}
              {!collapsed && (
                <div className='flex items-center gap-4 p-4 mb-6 md:mb-8 rounded-xl bg-primary/5 shrink-0'>
                  <Avatar className='w-12 h-12 border-2 border-primary/20'>
                    <AvatarImage src={user?.avatarUrl} alt={user?.fullName} />
                    <AvatarFallback className='text-base font-bold bg-primary text-background'>
                      {user?.fullName?.charAt(0)?.toUpperCase() ?? 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div className='min-w-0'>
                    <p className='font-sans text-base font-bold truncate text-primary'>
                      {user?.fullName}
                    </p>
                    <p className='font-sans text-sm truncate text-muted-foreground'>
                      {user?.email}
                    </p>
                  </div>
                </div>
              )}

              {/* Profile label + Collapse toggle */}
              <div
                className={cn(
                  'shrink-0 flex items-center justify-between transition-all duration-300 mb-2',
                  collapsed && 'justify-center'
                )}>
                {!collapsed && (
                  <p className='text-xs font-black uppercase tracking-[0.2em] text-primary/40'>
                    Profile
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

              {/* Navigation — scrollable middle */}
              <nav
                className={cn(
                  'flex-1 overflow-y-auto transition-all duration-300',
                  collapsed ? 'space-y-0.5' : 'space-y-1'
                )}>
                {navItems.map((item) => {
                  const isActive = location.pathname === item.to;
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
              </nav>

              {/* Back to home — pinned bottom */}
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
              className='fixed inset-0 z-40 bg-black/20 md:hidden'
              onClick={() => setMobileOpen(false)}
            />
          )}

          {/* Content — offset for fixed sidebar on desktop, full width */}
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
      </div>
    </TooltipProvider>
  );
}
