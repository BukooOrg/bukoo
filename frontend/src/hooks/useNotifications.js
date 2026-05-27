import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

import { notificationApi } from '@/lib/apiClient';

/**
 * Hook for managing notifications (list, unread count, mark read, delete).
 *
 * @param {Object} options
 * @param {boolean} [options.isAdmin] - If true, fetches system-wide notifications
 * @param {number} [options.pageSize] - Items per page (default: 10)
 */
export function useNotifications({ isAdmin = false, pageSize = 10 } = {}) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [filter, setFilter] = useState('all'); // 'all' | 'unread' | 'read'
  const [searchQuery, setSearchQuery] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch notifications
  useEffect(() => {
    let cancelled = false;

    async function fetchNotifications() {
      setLoading(true);
      try {
        const params = {
          page,
          pageSize,
          sort: '-created_at',
        };

        if (filter === 'unread') params.isRead = false;
        else if (filter === 'read') params.isRead = true;

        if (searchQuery) params.search = searchQuery;

        const response = await notificationApi.findNotifications(params);
        if (!cancelled) {
          const data = response.data;
          setNotifications(data.items || []);
          setTotalPages(data.meta?.totalPages || 1);
          setTotalCount(data.meta?.totalCount || 0);
        }
      } catch {
        if (!cancelled) {
          setNotifications([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchNotifications();
    return () => {
      cancelled = true;
    };
  }, [page, pageSize, filter, searchQuery]);

  // Fetch unread count (for customer badge)
  useEffect(() => {
    if (isAdmin) return;

    let cancelled = false;

    async function fetchUnreadCount() {
      try {
        const response = await notificationApi.getUnreadNotificationCount();
        if (!cancelled) {
          setUnreadCount(response.data.unreadCount || 0);
        }
      } catch {
        // Silently fail — badge will show 0
      }
    }

    fetchUnreadCount();
    return () => {
      cancelled = true;
    };
  }, [isAdmin]);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      await notificationApi.markNotificationAsRead({ notificationId });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, isRead: true, readAt: new Date() } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      toast.error('Failed to mark notification as read.');
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      const response = await notificationApi.markAllNotificationsAsRead({});
      const markedCount = response.data.markedCount || 0;
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true, readAt: new Date() })));
      setUnreadCount(0);
      toast.success(`${markedCount} notification${markedCount !== 1 ? 's' : ''} marked as read.`);
    } catch {
      toast.error('Failed to mark all notifications as read.');
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId) => {
    try {
      await notificationApi.deleteNotification({ notificationId });
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      toast.success('Notification deleted.');
    } catch {
      toast.error('Failed to delete notification.');
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [notifRes, countRes] = await Promise.all([
        notificationApi.findNotifications({
          page,
          pageSize,
          sort: '-created_at',
          ...(filter === 'unread' ? { isRead: false } : {}),
          ...(filter === 'read' ? { isRead: true } : {}),
          ...(searchQuery ? { search: searchQuery } : {}),
        }),
        isAdmin
          ? Promise.resolve({ data: { unreadCount: 0 } })
          : notificationApi.getUnreadNotificationCount(),
      ]);

      const notifData = notifRes.data;
      setNotifications(notifData.items || []);
      setTotalPages(notifData.meta?.totalPages || 1);
      setTotalCount(notifData.meta?.totalCount || 0);
      setUnreadCount(countRes.data.unreadCount || 0);
    } catch {
      // Silently fail
    }
  }, [page, pageSize, filter, searchQuery, isAdmin]);

  return {
    notifications,
    loading,
    page,
    totalPages,
    totalCount,
    filter,
    searchQuery,
    unreadCount,
    setPage,
    setFilter,
    setSearchQuery,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    refresh,
  };
}
