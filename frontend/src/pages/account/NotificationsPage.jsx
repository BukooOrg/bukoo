import { Bell, MailOpen, Search } from 'lucide-react';
import React from 'react';

import { NotificationCard, NotificationCardSkeleton } from '@/components/notifications';
import { ConfirmDialog } from '@/components/ui/feedback/confirm-dialog';
import { Button } from '@/components/ui/forms/button';
import { Input } from '@/components/ui/forms/input';
import { useNotifications } from '@/hooks/useNotifications';
import { cn } from '@/lib/utils';

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'unread', label: 'Unread' },
  { key: 'read', label: 'Read' },
];

export default function AccountNotificationsPage() {
  const {
    notifications,
    loading,
    page,
    totalPages,
    totalCount: _totalCount,
    filter,
    searchQuery,
    unreadCount,
    setPage,
    setFilter,
    setSearchQuery,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  } = useNotifications();

  const [confirmDeleteId, setConfirmDeleteId] = React.useState(null);

  const handleDelete = (id) => {
    setConfirmDeleteId(id);
  };

  const handleConfirmDelete = () => {
    if (confirmDeleteId) {
      deleteNotification(confirmDeleteId);
      setConfirmDeleteId(null);
    }
  };

  return (
    <div className='px-sides py-16'>
      <div className='max-w-3xl mx-auto'>
        {/* Header */}
        <div className='flex items-center justify-between mb-8'>
          <div>
            <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
              Notifications
            </h1>
            <p className='text-primary/40 font-bold italic text-sm mt-1'>
              {unreadCount > 0
                ? `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}`
                : 'All caught up'}
            </p>
          </div>

          {unreadCount > 0 && (
            <Button variant='outline' onClick={markAllAsRead} className='h-10'>
              <MailOpen className='w-4 h-4 mr-1.5' />
              Mark all read
            </Button>
          )}
        </div>

        {/* Filters */}
        <div className='flex flex-col gap-4 mb-6 sm:flex-row sm:items-center sm:justify-between'>
          <div className='flex items-center gap-1 p-1 bg-primary/5 rounded-lg'>
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => {
                  setFilter(f.key);
                  setPage(1);
                }}
                className={cn(
                  'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                  filter === f.key
                    ? 'bg-white text-primary shadow-sm'
                    : 'text-primary/50 hover:text-primary'
                )}>
                {f.label}
                {f.key === 'unread' && unreadCount > 0 && (
                  <span className='ml-1.5 px-1.5 py-0.5 text-[10px] font-bold bg-primary text-white rounded-full'>
                    {unreadCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className='relative w-full sm:w-64'>
            <Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/30' />
            <Input
              type='text'
              placeholder='Search notifications...'
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className='pl-9 h-10'
            />
          </div>
        </div>

        {/* Notifications list */}
        {loading ? (
          <div className='space-y-3'>
            {Array.from({ length: 5 }).map((_, i) => (
              <NotificationCardSkeleton key={i} />
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className='py-20 text-center'>
            <Bell className='w-12 h-12 mx-auto mb-4 text-primary/10' />
            <p className='font-serif text-2xl italic text-primary/40'>
              {searchQuery
                ? 'No notifications match your search.'
                : filter === 'unread'
                  ? 'No unread notifications.'
                  : filter === 'read'
                    ? 'No read notifications.'
                    : 'No notifications yet.'}
            </p>
          </div>
        ) : (
          <div className='space-y-3'>
            {notifications.map((notification) => (
              <NotificationCard
                key={notification.id}
                notification={notification}
                onMarkAsRead={markAsRead}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className='flex items-center justify-center gap-3 mt-8'>
            <Button
              variant='outline'
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className='h-10'>
              Previous
            </Button>
            <span className='text-sm text-primary/40'>
              Page {page} of {totalPages}
            </span>
            <Button
              variant='outline'
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className='h-10'>
              Next
            </Button>
          </div>
        )}

        {/* Delete confirmation dialog */}
        <ConfirmDialog
          open={!!confirmDeleteId}
          onOpenChange={(open) => !open && setConfirmDeleteId(null)}
          variant='destructive'
          title='Delete Notification'
          description='Are you sure you want to delete this notification? This action cannot be undone.'
          confirmText='Delete'
          onConfirm={handleConfirmDelete}
        />
      </div>
    </div>
  );
}
