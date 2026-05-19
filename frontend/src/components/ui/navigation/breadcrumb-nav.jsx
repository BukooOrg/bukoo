import { Home } from 'lucide-react';
import React from 'react';
import { Link, useLocation } from 'react-router-dom';

import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/navigation/breadcrumb';
import { cn } from '@/lib/utils';

const routeLabels = {
  admin: 'Admin',
  users: 'Users',
  books: 'Books',
  collections: 'Collections',
  categories: 'Categories',
  authors: 'Authors',
  publishers: 'Publishers',
  orders: 'Orders',
  reviews: 'Reviews',
  inventory: 'Inventory',
  reports: 'Reports',
  notifications: 'Notifications',
  new: 'New',
  account: 'Account',
  profile: 'Profile',
  address: 'Address',
  password: 'Password',
  wishlist: 'Wishlist',
  cart: 'Cart',
  checkout: 'Checkout',
  shop: 'Shop',
  login: 'Login',
  register: 'Register',
};

function formatSegment(segment) {
  if (routeLabels[segment]) return routeLabels[segment];
  return segment.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function BreadcrumbNav({ className, items, homeLabel = 'Home', maxItems = 4, ...props }) {
  const location = useLocation();

  const generatedItems = React.useMemo(() => {
    if (items) return items;

    const segments = location.pathname.split('/').filter(Boolean);
    const result = [];

    segments.forEach((segment, index) => {
      const isLast = index === segments.length - 1;
      const path = `/${segments.slice(0, index + 1).join('/')}`;

      if (isLast) {
        result.push({ label: formatSegment(segment), href: path, current: true });
      } else {
        result.push({ label: formatSegment(segment), href: path });
      }
    });

    return result;
  }, [items, location.pathname]);

  const displayItems = React.useMemo(() => {
    if (generatedItems.length <= maxItems) return generatedItems;

    const first = generatedItems[0];
    const last = generatedItems[generatedItems.length - 1];
    const _middle = generatedItems.slice(1, -1);

    return [first, { ellipsis: true }, last];
  }, [generatedItems, maxItems]);

  return (
    <Breadcrumb className={cn('mb-4', className)} {...props}>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link to='/' aria-label={homeLabel}>
              <Home className='w-4 h-4' />
            </Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {displayItems.map((item, index) => {
          if (item.ellipsis) {
            return (
              <React.Fragment key='ellipsis'>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbEllipsis />
                </BreadcrumbItem>
              </React.Fragment>
            );
          }

          const isLast = index === displayItems.length - 1;

          return (
            <React.Fragment key={item.href || index}>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                {isLast || item.current ? (
                  <BreadcrumbPage>{item.label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink asChild>
                    <Link to={item.href}>{item.label}</Link>
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </React.Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
