import { ReportJobStatus, ReportType } from '@bukoo/api-client';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ReportHistoryTable } from '@/components/reports/report-history-table';

vi.mock('@/lib/apiClient', () => ({
  reportApi: {
    findReportJobs: vi.fn(),
    downloadReportRaw: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockJobs = [
  {
    jobId: 'job-001',
    type: ReportType.SALES_SUMMARY,
    dateFrom: new Date('2025-01-01'),
    dateTo: new Date('2025-01-31'),
    format: 'pdf',
    limit: null,
    status: ReportJobStatus.COMPLETED,
    createdAt: new Date('2025-02-01T10:00:00Z'),
    completedAt: new Date('2025-02-01T10:05:00Z'),
  },
  {
    jobId: 'job-002',
    type: ReportType.TOP_BOOKS,
    dateFrom: new Date('2025-02-01'),
    dateTo: new Date('2025-02-28'),
    format: 'csv',
    limit: 10,
    status: ReportJobStatus.PENDING,
    createdAt: new Date('2025-03-01T14:00:00Z'),
    completedAt: null,
  },
];

function renderTable() {
  return render(<ReportHistoryTable />);
}

describe('ReportHistoryTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockImplementation(() => new Promise(() => {}));
    renderTable();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders jobs table with data', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Sales Summary').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText('Top Books').length).toBeGreaterThanOrEqual(1);
  });

  it('shows status badges for each job', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Completed').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText('Pending').length).toBeGreaterThanOrEqual(1);
  });

  it('shows download button for completed jobs', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Completed').length).toBeGreaterThanOrEqual(1);
    });

    const downloadButtons = screen.getAllByRole('button');
    expect(downloadButtons.length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty state when no jobs', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: [], meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getByText('No report jobs yet')).toBeInTheDocument();
    });
  });

  it('filters by status', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Sales Summary').length).toBeGreaterThanOrEqual(1);
    });

    const statusSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(statusSelect, { target: { value: ReportJobStatus.COMPLETED } });

    await waitFor(() => {
      expect(reportApi.findReportJobs).toHaveBeenCalledWith(
        expect.objectContaining({ status: ReportJobStatus.COMPLETED })
      );
    });
  });

  it('filters by type', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Sales Summary').length).toBeGreaterThanOrEqual(1);
    });

    const typeSelect = screen.getAllByRole('combobox')[1];
    fireEvent.change(typeSelect, { target: { value: ReportType.TOP_BOOKS } });

    await waitFor(() => {
      expect(reportApi.findReportJobs).toHaveBeenCalledWith(
        expect.objectContaining({ type: ReportType.TOP_BOOKS })
      );
    });
  });

  it('resets to page 1 when filter changes', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 1 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getAllByText('Sales Summary').length).toBeGreaterThanOrEqual(1);
    });

    const statusSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(statusSelect, { target: { value: ReportJobStatus.PENDING } });

    await waitFor(() => {
      expect(reportApi.findReportJobs).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));
    });
  });

  it('shows pagination when multiple pages', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 3 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
  });

  it('navigates to next page', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: { items: mockJobs, meta: { totalPages: 3 } },
    });

    renderTable();

    await waitFor(() => {
      expect(screen.getByText('Next')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(reportApi.findReportJobs).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
    });
  });

  it('polls when jobs are pending/processing', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: {
        items: [mockJobs[1]], // pending job
        meta: { totalPages: 1 },
      },
    });

    vi.useFakeTimers();
    renderTable();

    // Flush initial render + promise
    await act(async () => {
      await Promise.resolve();
    });

    expect(reportApi.findReportJobs).toHaveBeenCalledTimes(1);

    // Advance timer by 5 seconds to trigger poll
    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(reportApi.findReportJobs).toHaveBeenCalledTimes(2);

    vi.useRealTimers();
  });

  it('does not poll when all jobs are completed', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue({
      data: {
        items: [mockJobs[0]], // completed job
        meta: { totalPages: 1 },
      },
    });

    vi.useFakeTimers();
    renderTable();

    // Flush initial render + promise
    await act(async () => {
      await Promise.resolve();
    });

    expect(reportApi.findReportJobs).toHaveBeenCalledTimes(1);

    // Advance timer by 5 seconds
    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    // Should not have been called again
    expect(reportApi.findReportJobs).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });
});
