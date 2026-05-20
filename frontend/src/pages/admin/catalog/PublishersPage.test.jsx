import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import PublishersPage from '@/pages/admin/catalog/PublishersPage';

vi.mock('@/lib/apiClient', () => ({
  publisherApi: {
    findPublishers: vi.fn(),
    softDeletePublisher: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockPublishers = [
  {
    id: 'pub-1',
    name: 'Penguin Random House',
    website: 'https://penguinrandomhouse.com',
    createdAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'pub-2',
    name: 'HarperCollins',
    website: 'https://harpercollins.com',
    createdAt: '2024-02-15T09:00:00Z',
  },
  {
    id: 'pub-3',
    name: 'Macmillan',
    website: null,
    createdAt: '2024-03-01T12:00:00Z',
  },
];

function mockPublisherResponse(items, totalItems) {
  return {
    data: {
      items,
      pagination: {
        page: 1,
        pageSize: 20,
        totalItems,
        totalPages: Math.ceil(totalItems / 20) || 1,
        hasNext: false,
        hasPrev: false,
      },
    },
  };
}

describe('PublishersPage', () => {
  let publisherApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    publisherApi = mod.publisherApi;
    publisherApi.findPublishers.mockResolvedValue(
      mockPublisherResponse(mockPublishers, mockPublishers.length)
    );
    publisherApi.softDeletePublisher.mockResolvedValue({ data: {} });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Publishers')).toBeInTheDocument();
    });
  });

  it('renders total publisher count', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('3 publishers total')).toBeInTheDocument();
    });
  });

  it('renders new publisher button', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Publisher')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search publishers/i)).toBeInTheDocument();
    });
  });

  it('renders all publisher names in table', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Penguin Random House')).toBeInTheDocument();
      expect(screen.getByText('HarperCollins')).toBeInTheDocument();
      expect(screen.getByText('Macmillan')).toBeInTheDocument();
    });
  });

  it('renders publisher websites', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('https://penguinrandomhouse.com')).toBeInTheDocument();
    });
  });

  it('shows empty state when no publishers', async () => {
    publisherApi.findPublishers.mockResolvedValueOnce(mockPublisherResponse([], 0));

    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No publishers found')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    publisherApi.findPublishers.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load publishers')).toBeInTheDocument();
    });
  });

  it('searches publishers when typing in search input', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search publishers/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search publishers/i);

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'penguin' } });
    });

    await waitFor(
      () => {
        const calls = publisherApi.findPublishers.mock.calls;
        const lastCall = calls[calls.length - 1][0];
        expect(lastCall.search).toBe('penguin');
      },
      { timeout: 2000 }
    );
  });

  it('deletes a publisher', async () => {
    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Penguin Random House')).toBeInTheDocument();
    });

    const pubRow = screen.getByText('Penguin Random House').closest('tr');
    const buttons = pubRow.querySelectorAll('button');
    const deleteButton = buttons[buttons.length - 1];

    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Publisher?')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Delete Publisher');
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(publisherApi.softDeletePublisher).toHaveBeenCalledWith({ publisherId: 'pub-1' });
    });
  });

  it('renders view button for each publisher', async () => {
    const { container } = render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const viewLinks = container.querySelectorAll('a[href^="/admin/publishers/"]');
      expect(viewLinks.length).toBeGreaterThanOrEqual(mockPublishers.length);
    });
  });

  it('renders pagination when total pages > 1', async () => {
    const manyPublishers = Array.from({ length: 25 }, (_, i) => ({
      id: `pub-${i}`,
      name: `Publisher ${i + 1}`,
      website: null,
      createdAt: '2024-01-10T08:00:00Z',
    }));

    publisherApi.findPublishers.mockResolvedValue(
      mockPublisherResponse(manyPublishers.slice(0, 20), 25)
    );

    render(
      <MemoryRouter>
        <PublishersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
    });

    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
