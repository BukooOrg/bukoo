import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import PublisherNewPage from '@/pages/admin/catalog/PublisherNewPage';

vi.mock('@/lib/apiClient', () => ({
  publisherApi: {
    createPublisher: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('PublisherNewPage', () => {
  let publisherApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    publisherApi = mod.publisherApi;
    publisherApi.createPublisher.mockResolvedValue({
      data: { id: 'pub-new', name: 'Test Publisher', website: null },
    });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Publisher')).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Publishers')).toBeInTheDocument();
    });
  });

  it('renders name input', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Penguin Random House/i)).toBeInTheDocument();
    });
  });

  it('renders website input', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/https:\/\/example\.com/i)).toBeInTheDocument();
    });
  });

  it('shows error when submitting with empty name', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Create Publisher')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Create Publisher');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Publisher name is required')).toBeInTheDocument();
    });
  });

  it('creates a publisher successfully', async () => {
    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Penguin Random House/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Penguin Random House/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Publisher' } });
    });

    const websiteInput = screen.getByPlaceholderText(/https:\/\/example\.com/i);
    await act(async () => {
      fireEvent.change(websiteInput, { target: { value: 'https://test.com' } });
    });

    const submitButton = screen.getByText('Create Publisher');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(publisherApi.createPublisher).toHaveBeenCalledWith({
        createPublisherRequest: {
          name: 'Test Publisher',
          website: 'https://test.com',
        },
      });
    });
  });

  it('shows error on API failure', async () => {
    publisherApi.createPublisher.mockRejectedValueOnce(new Error('API error'));

    render(
      <MemoryRouter>
        <PublisherNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Penguin Random House/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Penguin Random House/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Publisher' } });
    });

    const submitButton = screen.getByText('Create Publisher');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('API error')).toBeInTheDocument();
    });
  });
});
