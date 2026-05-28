import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import InventoryPage from '@/pages/admin/inventory/InventoryPage';

vi.mock('@/lib/apiClient', () => ({
  inventoryApi: {
    getInventoryMetrics: vi.fn(),
    findLowStockItems: vi.fn(),
    findOutOfStockItems: vi.fn(),
  },
}));

const mockMetrics = {
  data: {
    totalSkuCount: 150,
    outOfStockCount: 12,
    lowStockCount: 25,
    totalInventoryValue: '15000.00',
  },
};

const mockPaginatedResponse = {
  data: {
    items: [],
    pagination: { totalPages: 1 },
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <InventoryPage />
    </MemoryRouter>
  );
}

describe('InventoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header with title "Inventory"', () => {
    renderPage();
    expect(screen.getByText('Inventory')).toBeInTheDocument();
  });

  it('shows Overview tab active by default', () => {
    renderPage();

    const overviewTab = screen.getByRole('tab', { name: /overview/i });
    expect(overviewTab).toHaveAttribute('data-state', 'active');

    const lowStockTab = screen.getByRole('tab', { name: /low stock/i });
    expect(lowStockTab).toHaveAttribute('data-state', 'inactive');

    const outOfStockTab = screen.getByRole('tab', { name: /out of stock/i });
    expect(outOfStockTab).toHaveAttribute('data-state', 'inactive');
  });

  it('renders 3 metric cards on Overview tab', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockResolvedValueOnce(mockMetrics);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Total SKUs')).toBeInTheDocument();
    });

    // These labels appear in both tab triggers and metric cards
    expect(screen.getAllByText('Out of Stock').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Low Stock').length).toBeGreaterThanOrEqual(1);

    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();

    // Total Value card removed
    expect(screen.queryByText('Total Value')).not.toBeInTheDocument();
    expect(screen.queryByText('RM 15000.00')).not.toBeInTheDocument();
  });

  it('fetches metrics on mount for Overview tab', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockResolvedValueOnce(mockMetrics);

    renderPage();

    await waitFor(() => {
      expect(inventoryApi.getInventoryMetrics).toHaveBeenCalledTimes(1);
    });
  });

  it('switches to Low Stock tab and fetches low stock data', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockResolvedValue(mockMetrics);
    inventoryApi.findLowStockItems.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Total SKUs')).toBeInTheDocument();
    });

    const user = userEvent.setup();
    const lowStockTab = screen.getByRole('tab', { name: /low stock/i });
    await user.click(lowStockTab);

    await waitFor(() => {
      expect(inventoryApi.findLowStockItems).toHaveBeenCalled();
    });

    expect(screen.getByText('Low Stock Items')).toBeInTheDocument();
  });

  it('switches to Out of Stock tab and fetches out of stock data', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockResolvedValue(mockMetrics);
    inventoryApi.findOutOfStockItems.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Total SKUs')).toBeInTheDocument();
    });

    const user = userEvent.setup();
    const outOfStockTab = screen.getByRole('tab', { name: /out of stock/i });
    await user.click(outOfStockTab);

    await waitFor(() => {
      expect(inventoryApi.findOutOfStockItems).toHaveBeenCalled();
    });

    // "Out of Stock" appears in both the tab and the InventoryTable title; verify at least one exists
    expect(screen.getAllByText('Out of Stock').length).toBeGreaterThanOrEqual(1);
  });

  it('shows loading state while fetching metrics', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockImplementation(() => new Promise(() => {}));

    renderPage();

    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(3);
  });

  it('shows error state with retry button on metrics fetch failure', async () => {
    const { inventoryApi } = await import('@/lib/apiClient');
    inventoryApi.getInventoryMetrics.mockRejectedValueOnce(new Error('Network error'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Failed to load inventory metrics')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
