import {
  User,
  Lock,
  MapPin,
  ShoppingCart,
  Star,
  Bell,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import React from 'react';
import { Link } from 'react-router-dom';

import { StatusBadge } from '@/components/account/status-badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import { useApiQuery } from '@/hooks/useApiQuery';
import { userApi } from '@/lib/apiClient';

const quickLinks = [
  { to: '/account/profile', label: 'Profile', desc: 'Update your personal details', icon: User },
  { to: '/account/password', label: 'Password', desc: 'Change your password', icon: Lock },
  { to: '/account/address', label: 'Address', desc: 'Manage shipping address', icon: MapPin },
  { to: '/account/orders', label: 'Orders', desc: 'View order history', icon: ShoppingCart },
  { to: '/account/reviews', label: 'Reviews', desc: 'Manage your reviews', icon: Star },
  {
    to: '/account/notifications',
    label: 'Notifications',
    desc: 'Notification preferences',
    icon: Bell,
  },
];

export default function AccountPage() {
  const { data: profile, loading } = useApiQuery(() => userApi.getMe(), {
    select: (res) => res.data,
  });

  if (loading) {
    return (
      <div className='space-y-6 animate-pulse'>
        <div className='h-8 w-48 bg-primary/5 rounded-2xl' />
        <div className='h-32 bg-primary/5 rounded-2xl' />
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          {[...Array(6)].map((_, i) => (
            <div key={i} className='h-20 bg-primary/5 rounded-2xl' />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          My Account
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          Manage your profile and preferences
        </p>
      </div>

      {/* Profile Summary */}
      <div className='p-6 rounded-2xl border bg-white'>
        <div className='flex items-center gap-4'>
          <Avatar className='w-16 h-16 border-2 border-primary/20'>
            <AvatarImage src={profile?.avatarUrl} alt={profile?.fullName} />
            <AvatarFallback className='text-xl font-bold bg-primary text-background'>
              {profile?.fullName?.charAt(0)?.toUpperCase() ?? 'U'}
            </AvatarFallback>
          </Avatar>
          <div>
            <h2 className='text-xl font-bold text-primary'>{profile?.fullName}</h2>
            <p className='text-sm text-primary/40'>{profile?.email}</p>
            <div className='flex items-center gap-3 mt-1'>
              <StatusBadge status={profile?.status} />
              <span className='text-xs text-primary/40'>
                Member since {new Date(profile?.createdAt).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.to}
              to={link.to}
              className='flex items-center gap-4 p-4 rounded-2xl border bg-white hover:border-primary/20 hover:shadow-sm transition-all group'>
              <div className='p-2 rounded-lg bg-primary/5 group-hover:bg-primary/10 transition-colors'>
                <Icon className='w-5 h-5 text-primary' />
              </div>
              <div className='flex-1 min-w-0'>
                <p className='text-sm font-bold text-primary'>{link.label}</p>
                <p className='text-xs text-primary/40'>{link.desc}</p>
              </div>
              <ArrowRight className='w-4 h-4 text-primary/30 group-hover:text-primary transition-colors' />
            </Link>
          );
        })}
      </div>

      {/* Danger Zone */}
      <div className='p-6 rounded-2xl border border-destructive/20 bg-destructive/5'>
        <div className='flex items-center gap-3'>
          <AlertTriangle className='w-5 h-5 text-destructive' />
          <div className='flex-1'>
            <p className='text-sm font-bold text-destructive'>Delete Account</p>
            <p className='text-xs text-destructive/70'>
              Permanently delete your account and all data
            </p>
          </div>
          <Link
            to='/account/delete'
            className='px-4 py-2 text-xs font-bold text-destructive border border-destructive/30 rounded-2xl hover:bg-destructive/10 transition-colors'>
            Go to Delete
          </Link>
        </div>
      </div>
    </div>
  );
}
