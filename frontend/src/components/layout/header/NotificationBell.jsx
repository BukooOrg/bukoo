import { Bell, MailOpen } from 'lucide-react';
import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/overlays/dropdown-menu';
import { notificationApi } from '@/lib/apiClient';

function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  const diffMs = Date.now() - d;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function NotificationBell() {
  const [unreadCount, setUnreadCount] = React.useState(0);
  const [recentUnread, setRecentUnread] = React.useState([]);
  const [open, setOpen] = React.useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [countRes, listRes] = await Promise.all([
          notificationApi.getUnreadNotificationCount(),
          notificationApi.findNotifications({ page: 1, pageSize: 5, isRead: false }),
        ]);
        setUnreadCount(countRes.data.unreadCount || 0);
        setRecentUnread(listRes.data.items || []);
      } catch {
        // Silently fail
      }
    }
    fetchData();
  }, []);

  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationApi.markNotificationAsRead({ notificationId });
      setUnreadCount((prev) => Math.max(0, prev - 1));
      setRecentUnread((prev) => prev.filter((n) => n.id !== notificationId));
    } catch {
      // Silently fail
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationApi.markAllNotificationsAsRead({});
      setUnreadCount(0);
      setRecentUnread([]);
    } catch {
      // Silently fail
    }
  };

  if (unreadCount === 0) {
    return (
      <Link
        to='/account/notifications'
        className='relative transition-colors text-black hover:bg-gray-100 rounded-full p-2'>
        <Bell className='size-5' />
      </Link>
    );
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button className='relative transition-colors text-black hover:bg-gray-100 rounded-full p-2'>
          <Bell className='size-5' />
          <span className='absolute -top-0.5 -right-0.5 size-4 flex items-center justify-center text-[9px] font-bold bg-red-500 text-white rounded-full'>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align='end' className='w-80 mt-2'>
        <div className='px-3 py-2 border-b border-secondary/10'>
          <div className='flex items-center justify-between'>
            <p className='text-sm font-semibold'>Notifications</p>
            <span className='text-xs text-primary/40'>{unreadCount} unread</span>
          </div>
        </div>

        <div className='max-h-72 overflow-y-auto'>
          {recentUnread.length === 0 ? (
            <p className='px-3 py-4 text-sm text-center text-primary/30'>No unread notifications</p>
          ) : (
            recentUnread.map((n) => (
              <DropdownMenuItem
                key={n.id}
                className='flex flex-col items-start gap-1 px-3 py-2 cursor-pointer'
                onClick={() => handleMarkAsRead(n.id)}>
                <div className='flex items-center justify-between w-full'>
                  <p className='text-sm font-medium truncate'>{n.subject}</p>
                  <span className='text-[10px] text-primary/30 ml-2 whitespace-nowrap'>
                    {formatDate(n.createdAt)}
                  </span>
                </div>
                <p className='text-xs text-primary/50 truncate'>{n.body}</p>
              </DropdownMenuItem>
            ))
          )}
        </div>

        <div className='px-3 py-2 border-t border-secondary/10'>
          <DropdownMenuItem
            className='justify-center cursor-pointer text-primary'
            onClick={handleMarkAllAsRead}>
            <MailOpen className='mr-2 w-4 h-4' />
            Mark all as read
          </DropdownMenuItem>
          <DropdownMenuItem asChild className='justify-center cursor-pointer'>
            <Link to='/account/notifications' onClick={() => setOpen(false)}>
              View all notifications
            </Link>
          </DropdownMenuItem>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
