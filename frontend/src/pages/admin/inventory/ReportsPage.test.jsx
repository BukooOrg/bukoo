import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ReportsPage from '@/pages/admin/inventory/ReportsPage';

vi.mock('@/lib/apiClient', () => ({
  reportApi: {
    findReportJobs: vi.fn(),
    createReportJob: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockPaginatedResponse = {
  data: {
    items: [],
    meta: { totalPages: 1 },
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <ReportsPage />
    </MemoryRouter>
  );
}

describe('ReportsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header with title', () => {
    renderPage();
    expect(screen.getByText('Reports & Analytics')).toBeInTheDocument();
  });

  it('shows Generate Report tab active by default', () => {
    renderPage();

    const generateTab = screen.getByRole('tab', { name: /generate report/i });
    expect(generateTab).toHaveAttribute('data-state', 'active');

    const historyTab = screen.getByRole('tab', { name: /job history/i });
    expect(historyTab).toHaveAttribute('data-state', 'inactive');
  });

  it('renders report form on Generate tab', () => {
    renderPage();
    expect(screen.getByText('Sales Summary')).toBeInTheDocument();
    expect(screen.getByText('Top Books')).toBeInTheDocument();
    expect(screen.getByText('Top Authors')).toBeInTheDocument();
    expect(screen.getByText('Monthly Volume')).toBeInTheDocument();
  });

  it('switches to Job History tab and loads data', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    const user = userEvent.setup();
    const historyTab = screen.getByRole('tab', { name: /job history/i });
    await user.click(historyTab);

    expect(historyTab).toHaveAttribute('data-state', 'active');

    await waitFor(() => {
      expect(reportApi.findReportJobs).toHaveBeenCalled();
    });
  });

  it('shows empty state on Job History tab when no jobs', async () => {
    const { reportApi } = await import('@/lib/apiClient');
    reportApi.findReportJobs.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    const user = userEvent.setup();
    const historyTab = screen.getByRole('tab', { name: /job history/i });
    await user.click(historyTab);

    await waitFor(() => {
      expect(screen.getByText('No report jobs yet')).toBeInTheDocument();
    });
  });
});
