import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { InventoryTable } from '@/components/inventory/inventory-table';

vi.mock('@/lib/apiClient', () => ({
  inventoryApi: {
    findLowStockItems: vi.fn(),
    findOutOfStockItems: vi.fn(),
  },
}));

const mockBooks = [
  {
    id: 'book-1',
    title: 'The Great Gatsby',
    isbn: '9780743273565',
    stockQuantity: 3,
    coverUrl: 'https://example.com/cover1.jpg',
    price: '25.00',
  },
  {
    id: 'book-2',
    title: '1984',
    isbn: '9780451524935',
    stockQuantity: 0,
    coverUrl: null,
    price: '20.00',
  },
];

const LOW_STOCK_RANGES = [
  { label: '< 5', min: 0, max: 4 },
  { label: '5–10', min: 5, max: 10 },
  { label: '10–20', min: 10, max: 20 },
  { label: '20–50', min: 20, max: 50 },
  { label: '50+', min: 50, max: null },
];

const mockPaginatedResponse = {
  data: { items: mockBooks, pagination: { totalPages: 1 } },
};

function renderTable(props = {}) {
  const defaultProps = {
    title: 'Low Stock Items',
    description: 'Books below threshold',
    fetchItems: vi.fn(),
    emptyMessage: 'No items found',
    ...props,
  };

  return render(
    <MemoryRouter>
      <InventoryTable {...defaultProps} />
    </MemoryRouter>
  );
}

describe('InventoryTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders table with book data (cover, title, ISBN, stock, link)', async () => {
    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({
      fetchItems,
      rangeSelector: { default: 0, options: LOW_STOCK_RANGES },
    });

    await waitFor(() => {
      expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
    });

    expect(screen.getByText('9780743273565')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'The Great Gatsby' })).toHaveAttribute(
      'src',
      'https://example.com/cover1.jpg'
    );

    const link = screen.getByRole('link', { name: 'The Great Gatsby' });
    expect(link).toHaveAttribute('href', '/admin/books/book-1');
  });

  it('shows loading skeleton initially', () => {
    const fetchItems = vi.fn().mockImplementation(() => new Promise(() => {}));

    renderTable({ fetchItems });

    expect(screen.getByText('Low Stock Items')).toBeInTheDocument();
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when no items', async () => {
    const fetchItems = vi.fn().mockResolvedValue({
      data: { items: [], pagination: { totalPages: 1 } },
    });

    renderTable({ fetchItems, emptyMessage: 'All books are well-stocked' });

    await waitFor(() => {
      expect(screen.getByText('All books are well-stocked')).toBeInTheDocument();
    });
  });

  it('shows search input', async () => {
    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({ fetchItems });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search by title or ISBN...')).toBeInTheDocument();
    });
  });

  it('shows range selector when rangeSelector is provided', async () => {
    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({
      fetchItems,
      rangeSelector: { default: 0, options: LOW_STOCK_RANGES },
    });

    await waitFor(() => {
      expect(screen.getByLabelText('Stock range')).toBeInTheDocument();
    });

    expect(screen.getByText('< 5 units')).toBeInTheDocument();
  });

  it('reloads data when range selector changes', async () => {
    const user = userEvent.setup();
    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({
      fetchItems,
      rangeSelector: { default: 0, options: LOW_STOCK_RANGES },
    });

    // Wait for initial load
    await waitFor(() => {
      expect(fetchItems).toHaveBeenCalledTimes(1);
    });

    // Initial call should have threshold=4 (max of first range "< 5") and pageSize=100
    expect(fetchItems).toHaveBeenLastCalledWith(
      expect.objectContaining({ threshold: 4, page: 1, pageSize: 100 })
    );

    // Change range to "≤ 10" (index 1, threshold=10)
    const select = screen.getByLabelText('Stock range');
    await user.selectOptions(select, '1');

    await waitFor(() => {
      expect(fetchItems).toHaveBeenCalledTimes(2);
    });

    // Second call should have threshold=10
    expect(fetchItems).toHaveBeenLastCalledWith(
      expect.objectContaining({ threshold: 10, page: 1 })
    );
  });

  it('does NOT show range selector when rangeSelector is not provided', async () => {
    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({
      fetchItems,
      title: 'Out of Stock',
    });

    await waitFor(() => {
      expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    });

    expect(screen.queryByLabelText('Stock range')).not.toBeInTheDocument();
    expect(screen.queryByText('Stock Qty')).not.toBeInTheDocument();
  });

  it('calls API with search query when user types', async () => {
    vi.useFakeTimers();

    const fetchItems = vi.fn().mockResolvedValue(mockPaginatedResponse);

    renderTable({ fetchItems });

    // Advance timers to let initial useEffect + promise resolve
    await act(async () => {
      vi.advanceTimersByTime(0);
    });

    expect(fetchItems).toHaveBeenCalled();
    fetchItems.mockClear();

    const searchInput = screen.getByPlaceholderText('Search by title or ISBN...');
    fireEvent.change(searchInput, { target: { value: 'gatsby' } });

    // Advance the debounce timer (400ms)
    await act(async () => {
      vi.advanceTimersByTime(400);
    });

    expect(fetchItems).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'gatsby', page: 1, pageSize: 100 })
    );

    vi.useRealTimers();
  });

  it('shows pagination controls when multiple pages', async () => {
    const manyBooks = Array.from({ length: 25 }, (_, i) => ({
      id: `book-${i}`,
      title: `Book ${i}`,
      isbn: `978000000000${i}`,
      stockQuantity: i + 1,
      coverUrl: null,
      price: '10.00',
    }));
    const fetchItems = vi.fn().mockResolvedValue({
      data: { items: manyBooks, pagination: { totalPages: 1 } },
    });

    renderTable({ fetchItems, rangeSelector: { default: 0, options: LOW_STOCK_RANGES } });

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });

    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
