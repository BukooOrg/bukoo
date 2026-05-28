import { ReportFormat, ReportType } from '@bukoo/api-client';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ReportForm } from '@/components/reports/report-form';

vi.mock('@/lib/apiClient', () => ({
  reportApi: {
    createReportJob: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function renderForm(props = {}) {
  return render(<ReportForm onSuccess={props.onSuccess} />);
}

describe('ReportForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all report type options', () => {
    renderForm();
    expect(screen.getByText('Sales Summary')).toBeInTheDocument();
    expect(screen.getByText('Top Books')).toBeInTheDocument();
    expect(screen.getByText('Top Authors')).toBeInTheDocument();
    expect(screen.getByText('Monthly Volume')).toBeInTheDocument();
  });

  it('renders date inputs', () => {
    renderForm();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
  });

  it('renders format toggle with PDF and CSV', () => {
    renderForm();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
  });

  it('shows limit field for Top Books', () => {
    renderForm();
    const topBooksBtn = screen.getByText('Top Books');
    fireEvent.click(topBooksBtn);
    expect(screen.getByLabelText('Limit (max results)')).toBeInTheDocument();
  });

  it('shows limit field for Top Authors', () => {
    renderForm();
    const topAuthorsBtn = screen.getByText('Top Authors');
    fireEvent.click(topAuthorsBtn);
    expect(screen.getByLabelText('Limit (max results)')).toBeInTheDocument();
  });

  it('hides limit field for Sales Summary', () => {
    renderForm();
    expect(screen.queryByLabelText('Limit (max results)')).not.toBeInTheDocument();
  });

  it('hides limit field for Monthly Volume', () => {
    renderForm();
    const monthlyBtn = screen.getByText('Monthly Volume');
    fireEvent.click(monthlyBtn);
    expect(screen.queryByLabelText('Limit (max results)')).not.toBeInTheDocument();
  });

  it('shows validation error when dates are empty on submit', async () => {
    renderForm();
    const submitBtn = screen.getByRole('button', { name: 'Generate Report' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Start date is required')).toBeInTheDocument();
    });
  });

  it('shows validation error when start date is after end date', async () => {
    renderForm();
    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2025-12-01' },
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2025-01-01' },
    });

    const submitBtn = screen.getByRole('button', { name: 'Generate Report' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText('Start date must be before or equal to end date')
      ).toBeInTheDocument();
    });
  });

  it('submits successfully and calls onSuccess', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.createReportJob.mockResolvedValue({ data: { jobId: 'job-123' } });

    const onSuccess = vi.fn();
    renderForm({ onSuccess });

    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2025-01-01' },
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2025-12-31' },
    });

    const submitBtn = screen.getByRole('button', { name: 'Generate Report' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(reportApi.createReportJob).toHaveBeenCalledWith({
        createReportJobRequest: expect.objectContaining({
          type: ReportType.SALES_SUMMARY,
          format: ReportFormat.PDF,
        }),
      });
    });

    expect(onSuccess).toHaveBeenCalled();
  });

  it('shows disabled state while submitting', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.createReportJob.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    renderForm();

    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2025-01-01' },
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2025-12-31' },
    });

    const submitBtn = screen.getByRole('button', { name: 'Generate Report' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(submitBtn).toBeDisabled();
    });
  });

  it('shows error toast on submission failure', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.createReportJob.mockRejectedValue(new Error('Network error'));

    const { toast } = await import('sonner');
    renderForm();

    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2025-01-01' },
    });
    fireEvent.change(screen.getByLabelText('End Date'), {
      target: { value: '2025-12-31' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Generate Report' }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to create report job');
    });
  });
});
