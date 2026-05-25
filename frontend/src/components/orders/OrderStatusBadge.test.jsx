import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';

describe('OrderStatusBadge', () => {
  it('renders pending status', () => {
    render(<OrderStatusBadge status='pending' />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders paid status', () => {
    render(<OrderStatusBadge status='paid' />);
    expect(screen.getByText('Paid')).toBeInTheDocument();
  });

  it('renders shipped status', () => {
    render(<OrderStatusBadge status='shipped' />);
    expect(screen.getByText('Shipped')).toBeInTheDocument();
  });

  it('renders delivered status', () => {
    render(<OrderStatusBadge status='delivered' />);
    expect(screen.getByText('Delivered')).toBeInTheDocument();
  });

  it('renders cancelled status', () => {
    render(<OrderStatusBadge status='cancelled' />);
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('defaults to pending for unknown status', () => {
    render(<OrderStatusBadge status='unknown' />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('handles null status', () => {
    render(<OrderStatusBadge status={null} />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('applies additional className', () => {
    render(<OrderStatusBadge status='paid' className='custom-class' />);
    const badge = screen.getByText('Paid');
    expect(badge.className).toContain('custom-class');
  });
});
