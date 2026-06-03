import { Bell, Check, Clock, Mail, MailOpen, MoreVertical, Trash2, User } from 'lucide-react';
import React, { useState } from 'react';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/overlays/dropdown-menu';
import { cn } from '@/lib/utils';

const TYPE_ICONS = {
  order: Mail,
  payment: Check,
  shipping: Clock,
  system: Bell,
  default: Bell,
};

const TYPE_COLORS = {
  order: 'bg-primary/10 text-primary',
  payment: 'bg-primary/10 text-primary',
  shipping: 'bg-primary/10 text-primary',
  system: 'bg-primary/10 text-primary',
  default: 'bg-primary/5 text-primary',
};

function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getTypeIcon(type) {
  return TYPE_ICONS[type] || TYPE_ICONS.default;
}

function getTypeColor(type) {
  return TYPE_COLORS[type] || TYPE_COLORS.default;
}

export function NotificationCard({
  notification,
  onMarkAsRead,
  onDelete,
  showUser = false,
  className,
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  const Icon = getTypeIcon(notification.type);
  const colorClass = getTypeColor(notification.type);

  return (
    <div
      className={cn(
        'group flex items-start gap-4 p-4 border rounded-2xl transition-colors',
        notification.isRead
          ? 'bg-white border-primary/5'
          : 'bg-primary/[0.02] border-primary/10 hover:border-primary/20',
        className
      )}
      onClick={() => {
        if (!notification.isRead && onMarkAsRead) {
          onMarkAsRead(notification.id);
        }
      }}
      role='button'
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && !notification.isRead && onMarkAsRead) {
          onMarkAsRead(notification.id);
        }
      }}>
      {/* Icon */}
      <div
        className={cn(
          'flex-none flex items-center justify-center w-10 h-10 rounded-full',
          colorClass
        )}>
        <Icon className='w-5 h-5' />
      </div>

      {/* Content */}
      <div className='flex-1 min-w-0'>
        <div className='flex items-start justify-between gap-2'>
          <div className='flex-1 min-w-0'>
            <div className='flex items-center gap-2 mb-1'>
              <h4
                className={cn(
                  'text-sm font-semibold truncate',
                  notification.isRead ? 'text-primary/60' : 'text-primary'
                )}>
                {notification.subject}
              </h4>
              {!notification.isRead && (
                <span className='flex-none w-2 h-2 rounded-full bg-primary' />
              )}
            </div>
            <p className='text-sm leading-relaxed text-primary/50 line-clamp-2'>
              {notification.body}
            </p>
          </div>

          {/* Actions */}
          <div className='flex flex-col items-end gap-1'>
            <span className='text-xs text-primary/30 whitespace-nowrap'>
              {formatDate(notification.createdAt)}
            </span>

            <div className='flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity'>
              {showUser && notification.userId && (
                <span className='flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded-2xl bg-primary/5 text-primary/50'>
                  <User className='w-3 h-3' />
                  {notification.userId.slice(0, 8)}
                </span>
              )}

              <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <button
                    className='p-1 rounded-2xl hover:bg-primary/5 transition-colors'
                    onClick={(e) => e.stopPropagation()}>
                    <MoreVertical className='w-4 h-4 text-primary/40' />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align='end' className='w-40'>
                  {!notification.isRead && onMarkAsRead && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        onMarkAsRead(notification.id);
                        setMenuOpen(false);
                      }}>
                      <MailOpen className='mr-2 w-4 h-4' />
                      Mark as read
                    </DropdownMenuItem>
                  )}
                  {onDelete && (
                    <DropdownMenuItem
                      className='text-destructive focus:text-destructive'
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(notification.id);
                        setMenuOpen(false);
                      }}>
                      <Trash2 className='mr-2 w-4 h-4' />
                      Delete
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function NotificationCardSkeleton() {
  return (
    <div className='flex items-start gap-4 p-4 border rounded-2xl border-primary/5 bg-white animate-pulse'>
      <div className='flex-none w-10 h-10 rounded-full bg-primary/5' />
      <div className='flex-1 space-y-2'>
        <div className='w-1/3 h-4 rounded bg-primary/5' />
        <div className='w-full h-3 rounded bg-primary/5' />
        <div className='w-2/3 h-3 rounded bg-primary/5' />
      </div>
    </div>
  );
}
