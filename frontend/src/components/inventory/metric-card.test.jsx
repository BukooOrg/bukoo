import { render, screen } from '@testing-library/react';
import { Package } from 'lucide-react';
import { describe, it, expect } from 'vitest';

import { MetricCard } from '@/components/inventory/metric-card';

describe('MetricCard', () => {
  it('renders with label, value, and icon', () => {
    render(<MetricCard icon={Package} label='Total SKUs' value={150} />);

    expect(screen.getByText('Total SKUs')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('applies red accent variant correctly', () => {
    const { container } = render(
      <MetricCard icon={Package} label='Out of Stock' value={12} accent='red' />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('border-destructive/20');
    expect(card).toHaveClass('bg-destructive/[0.04]');
  });

  it('applies amber accent variant correctly', () => {
    const { container } = render(
      <MetricCard icon={Package} label='Low Stock' value={25} accent='amber' />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('border-primary/20');
    expect(card).toHaveClass('bg-primary/[0.04]');
  });

  it('applies green accent variant correctly', () => {
    const { container } = render(
      <MetricCard icon={Package} label='Total Value' value='RM 15,000.00' accent='green' />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('border-primary/20');
    expect(card).toHaveClass('bg-primary/[0.04]');
  });

  it('renders with default variant when no accent specified', () => {
    const { container } = render(<MetricCard icon={Package} label='Total SKUs' value={150} />);

    const card = container.firstChild;
    expect(card).toHaveClass('border-primary/10');
    expect(card).toHaveClass('bg-primary/[0.03]');
  });
});
