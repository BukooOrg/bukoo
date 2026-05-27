import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import * as apiClient from '@/lib/apiClient';
import AdminNotificationsPage from '@/pages/admin/NotificationsPage';

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
    userId: 'user-2',
    type: 'payment',
    subject: 'Payment Failed',
    body: 'Payment could not be processed.',
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

describe('AdminNotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClient.notificationApi.findNotifications.mockResolvedValue(mockApiResponse([], 1, 0));
  });

  it('renders page title', async () => {
    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('System Notifications')).toBeInTheDocument();
    });
  });

  it('shows empty state when no notifications', async () => {
    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('No notifications yet.')).toBeInTheDocument();
    });
  });

  it('renders notifications when data is loaded', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );

    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Order Shipped')).toBeInTheDocument();
      expect(screen.getByText('Payment Failed')).toBeInTheDocument();
    });
  });

  it('shows user badges for notifications', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );

    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('user-1')).toBeInTheDocument();
      expect(screen.getByText('user-2')).toBeInTheDocument();
    });
  });

  it('shows notification count summary', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );

    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Showing 2 notifications')).toBeInTheDocument();
    });
  });

  it('filters notifications by read status', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(
        mockNotifications.filter((n) => !n.isRead),
        1,
        1
      )
    );

    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(screen.getByText('System Notifications')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Unread'));
    await waitFor(() => {
      expect(apiClient.notificationApi.findNotifications).toHaveBeenCalledWith(
        expect.objectContaining({ isRead: false })
      );
    });
  });

  it('uses larger page size (20) for admin view', async () => {
    apiClient.notificationApi.findNotifications.mockResolvedValue(
      mockApiResponse(mockNotifications, 1, 2)
    );

    render(<AdminNotificationsPage />);
    await waitFor(() => {
      expect(apiClient.notificationApi.findNotifications).toHaveBeenCalledWith(
        expect.objectContaining({ pageSize: 20 })
      );
    });
  });
});
