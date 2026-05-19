import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { AdminLayout } from '@/components/layout/AdminLayout';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      fullName: 'Admin User',
      email: 'admin@bukoo.com',
      role: 'admin',
    },
  }),
}));

vi.mock('@/components/layout/header', () => ({
  Header: () => <div data-testid='site-header'>Header</div>,
}));

vi.mock('sonner', async () => {
  const actual = await vi.importActual('sonner');
  return {
    ...actual,
    toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  };
});

describe('AdminLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sidebar with brand header', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders dashboard link', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Overview')).toBeInTheDocument();
  });

  it('renders catalog section links', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Books')).toBeInTheDocument();
    expect(screen.getByText('Collections')).toBeInTheDocument();
    expect(screen.getByText('Categories')).toBeInTheDocument();
    expect(screen.getByText('Authors')).toBeInTheDocument();
    expect(screen.getByText('Publishers')).toBeInTheDocument();
  });

  it('renders users section links', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Manage Users')).toBeInTheDocument();
    expect(screen.getByText('New User')).toBeInTheDocument();
  });

  it('renders orders and reviews links', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Reviews')).toBeInTheDocument();
  });

  it('renders inventory and reports links', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Inventory')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('renders notifications link', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    const elements = screen.getAllByText('Notifications');
    expect(elements.length).toBeGreaterThanOrEqual(2);
  });

  it('renders Back to Store link', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('← Back to Store')).toBeInTheDocument();
  });

  it('highlights active nav item', () => {
    render(
      <MemoryRouter initialEntries={['/admin/books']}>
        <AdminLayout />
      </MemoryRouter>
    );

    const booksLink = screen.getByText('Books').closest('a');
    expect(booksLink).toHaveClass('bg-primary/10');
  });

  it('section headers are rendered', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Catalog')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Orders & Reviews')).toBeInTheDocument();
    expect(screen.getByText('Inventory & Reports')).toBeInTheDocument();
  });
});
