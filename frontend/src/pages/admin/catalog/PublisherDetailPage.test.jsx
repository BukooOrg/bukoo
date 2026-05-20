import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import PublisherDetailPage from '@/pages/admin/catalog/PublisherDetailPage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ publisherId: 'pub-1' }),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/lib/apiClient', () => ({
  publisherApi: {
    viewPublisherDetail: vi.fn(),
    updatePublisher: vi.fn(),
    softDeletePublisher: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockPublisher = {
  id: 'pub-1',
  name: 'Penguin Random House',
  website: 'https://penguinrandomhouse.com',
  createdAt: '2024-01-10T08:00:00Z',
};

describe('PublisherDetailPage', () => {
  let publisherApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    publisherApi = mod.publisherApi;
    publisherApi.viewPublisherDetail.mockResolvedValue({ data: mockPublisher });
    publisherApi.updatePublisher.mockResolvedValue({ data: {} });
    publisherApi.softDeletePublisher.mockResolvedValue({ data: {} });
  });

  it('renders publisher name', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Penguin Random House');
    });
  });

  it('renders publisher website', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const websiteElements = screen.getAllByText('https://penguinrandomhouse.com');
      expect(websiteElements.length).toBeGreaterThan(0);
    });
  });

  it('renders created date', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/10 January 2024/)).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Publishers')).toBeInTheDocument();
    });
  });

  it('renders edit button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Publisher')).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete Publisher')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    publisherApi.viewPublisherDetail.mockRejectedValueOnce(new Error('Not found'));

    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load publisher')).toBeInTheDocument();
    });
  });

  it('opens edit dialog when edit button clicked', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Publisher');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Publisher')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit publisher/i })).toBeInTheDocument();
    });
  });

  it('updates publisher successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Publisher');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Publisher')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit publisher/i })).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Penguin Random House');
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Updated Publisher' } });
    });

    const saveButton = screen.getByText('Save Changes');
    await act(async () => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(publisherApi.updatePublisher).toHaveBeenCalled();
    });

    const callArgs = publisherApi.updatePublisher.mock.calls[0][0];
    expect(callArgs.publisherId).toBe('pub-1');
    expect(callArgs.updatePublisherRequest.name).toBe('Updated Publisher');
  });

  it('deletes publisher successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/publishers/pub-1']}>
        <PublisherDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete Publisher');
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    const deleteButton = screen.getAllByText('Delete Publisher')[0];
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Publisher?')).toBeInTheDocument();
    });

    const confirmButton = screen.getAllByText('Delete Publisher')[1];
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(publisherApi.softDeletePublisher).toHaveBeenCalledWith({ publisherId: 'pub-1' });
    });
  });
});
