import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { NotificationCard } from '@/components/notifications/notification-card';

const mockNotification = {
  id: 'notif-1',
  userId: 'user-123',
  type: 'order',
  subject: 'Order Shipped',
  body: 'Your order #12345 has been shipped and is on its way.',
  isRead: false,
  readAt: null,
  createdAt: new Date(Date.now() - 3600000), // 1 hour ago
};

describe('NotificationCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders notification subject and body', () => {
    render(<NotificationCard notification={mockNotification} />);
    expect(screen.getByText('Order Shipped')).toBeInTheDocument();
    expect(screen.getByText(/Your order #12345/)).toBeInTheDocument();
  });

  it('shows unread indicator when notification is unread', () => {
    render(<NotificationCard notification={mockNotification} />);
    // The card container has role="button" (first one)
    const buttons = screen.getAllByRole('button');
    const card = buttons[0];
    // Unread cards have bg-primary/[0.02] background
    expect(card.className).toContain('bg-primary/[0.02]');
  });

  it('does not show unread indicator when notification is read', () => {
    const readNotification = { ...mockNotification, isRead: true, readAt: new Date() };
    render(<NotificationCard notification={readNotification} />);
    const card = screen.getByRole('button', { name: '' });
    const unreadDot = card.querySelector('.flex-none.w-2.h-2.rounded-full.bg-primary');
    expect(unreadDot).not.toBeInTheDocument();
  });

  it('calls onMarkAsRead when clicked and notification is unread', () => {
    const onMarkAsRead = vi.fn();
    render(<NotificationCard notification={mockNotification} onMarkAsRead={onMarkAsRead} />);
    // Click the card (first button with role="button")
    const card = screen.getAllByRole('button')[0];
    fireEvent.click(card);
    expect(onMarkAsRead).toHaveBeenCalledWith('notif-1');
  });

  it('does not call onMarkAsRead when notification is already read', () => {
    const onMarkAsRead = vi.fn();
    const readNotification = { ...mockNotification, isRead: true, readAt: new Date() };
    render(<NotificationCard notification={readNotification} onMarkAsRead={onMarkAsRead} />);
    const card = screen.getAllByRole('button')[0];
    fireEvent.click(card);
    expect(onMarkAsRead).not.toHaveBeenCalled();
  });

  it('shows user badge when showUser is true', () => {
    render(<NotificationCard notification={mockNotification} showUser />);
    expect(screen.getByText(mockNotification.userId.slice(0, 8))).toBeInTheDocument();
  });

  it('does not show user badge when showUser is false', () => {
    render(<NotificationCard notification={mockNotification} showUser={false} />);
    expect(screen.queryByText(mockNotification.userId.slice(0, 8))).not.toBeInTheDocument();
  });
});
