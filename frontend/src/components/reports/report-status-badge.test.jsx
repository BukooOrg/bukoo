import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { ReportStatusBadge } from '@/components/reports/report-status-badge';

describe('ReportStatusBadge', () => {
  it('renders pending status', () => {
    render(<ReportStatusBadge status='pending' />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders processing status', () => {
    render(<ReportStatusBadge status='processing' />);
    expect(screen.getByText('Processing')).toBeInTheDocument();
  });

  it('renders completed status', () => {
    render(<ReportStatusBadge status='completed' />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders failed status', () => {
    render(<ReportStatusBadge status='failed' />);
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('defaults to pending for unknown status', () => {
    render(<ReportStatusBadge status='unknown' />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('applies additional className', () => {
    render(<ReportStatusBadge status='completed' className='custom-class' />);
    const badge = screen.getByText('Completed');
    expect(badge.className).toContain('custom-class');
  });
});
