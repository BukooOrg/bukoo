import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import * as apiClient from '@/lib/apiClient';
import AccountNotificationsPage from '@/pages/account/NotificationsPage';

vi.mock('@/lib/apiClient', () => ({
  notificationApi: {
    findNotifications: vi.fn(),
    getUnreadNotificationCount: vi.fn(),
    markNotificationAsRead: vi.fn(),
    markAllNotificationsAsRead: vi.fn(),
    deleteNotification: vi.fn(),
  },
}));

const mockNotifications = [
  {
    id: 'notif-1',
    userId: 'user-1',
    type: 'order',
    subject: 'Order Shipped',
    body: 'Your order has been shipped.',
    isRead: false,
    readAt: null,
    createdAt: new Date().toISOString(),
  },
  {
    id: 'notif-2',
    userId: 'user-1',
    type: 'payment',
    subject: 'Payment Received',
    body: 'Your payment was successful.',
    isRead: true,
    readAt: new Date().toISOString(),
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
];

function mockApiResponse(items = [], totalPages = 1, totalCount = 0) {
  return {
    data: {
      items,
      meta: { totalPages, totalCount },
    },
  };
}

describe('AccountNotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClient.notificationApi.findNotifications.mockResolvedValue(mockApiResponse([], 1, 0));
    apiClient.notificationApi.getUnreadNotificationCount.mockResolvedValue({
      data: { unreadCount: 0 },
    });
  });

  it('renders page title', async () => {
    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });
  });

  it('shows empty state when no notifications', async () => {
    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('No notifications yet.')).toBeInTheDocument();
    });
  });

  it('renders notifications when data is loaded', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );
    apiClient.notificationApi.getUnreadNotificationCount.mockResolvedValue({
      data: { unreadCount: 1 },
    });

    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Order Shipped')).toBeInTheDocument();
      expect(screen.getByText('Payment Received')).toBeInTheDocument();
    });
  });

  it('calls markNotificationAsRead when unread notification is clicked', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );
    apiClient.notificationApi.getUnreadNotificationCount.mockResolvedValue({
      data: { unreadCount: 1 },
    });
    apiClient.notificationApi.markNotificationAsRead.mockResolvedValue({ data: {} });

    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Order Shipped')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Order Shipped'));
    await waitFor(() => {
      expect(apiClient.notificationApi.markNotificationAsRead).toHaveBeenCalledWith({
        notificationId: 'notif-1',
      });
    });
  });

  it('calls markAllNotificationsAsRead when "Mark all read" is clicked', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );
    apiClient.notificationApi.getUnreadNotificationCount.mockResolvedValue({
      data: { unreadCount: 1 },
    });
    apiClient.notificationApi.markAllNotificationsAsRead.mockResolvedValue({
      data: { markedCount: 1 },
    });

    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Mark all read')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Mark all read'));
    await waitFor(() => {
      expect(apiClient.notificationApi.markAllNotificationsAsRead).toHaveBeenCalledWith({});
    });
  });

  it('filters notifications by unread status', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(
        mockNotifications.filter((n) => !n.isRead),
        1,
        1
      )
    );
    apiClient.notificationApi.getUnreadNotificationCount.mockResolvedValue({
      data: { unreadCount: 1 },
    });

    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Unread'));
    await waitFor(() => {
      expect(apiClient.notificationApi.findNotifications).toHaveBeenCalledWith(
        expect.objectContaining({ isRead: false })
      );
    });
  });

  it('shows search input', async () => {
    render(<AccountNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search notifications...')).toBeInTheDocument();
    });
  });
});
