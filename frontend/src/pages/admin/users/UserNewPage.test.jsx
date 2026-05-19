import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import UserNewPage from '@/pages/admin/users/UserNewPage';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/lib/apiClient', () => ({
  userApi: {
    registerAdmin: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockCreatedUser = {
  id: 'user-new-1',
  fullName: 'John Admin',
  email: 'john@bukoo.com',
  role: 'admin',
  status: 'active',
};

function renderWithRouter(ui) {
  return render(
    <MemoryRouter>
      <Routes>
        <Route path='*' element={ui} />
      </Routes>
    </MemoryRouter>
  );
}

describe('UserNewPage', () => {
  let userApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    userApi = mod.userApi;
    userApi.registerAdmin.mockResolvedValue({ data: mockCreatedUser });
  });

  it('renders page header', () => {
    renderWithRouter(<UserNewPage />);

    expect(screen.getByText('New Admin')).toBeInTheDocument();
    expect(screen.getByText('Register a new admin account')).toBeInTheDocument();
  });

  it('renders back to users link', () => {
    renderWithRouter(<UserNewPage />);

    const backLink = screen.getByText('Back to Users').closest('a');
    expect(backLink).toHaveAttribute('href', '/admin/users');
  });

  it('renders all form fields', () => {
    renderWithRouter(<UserNewPage />);

    expect(screen.getByPlaceholderText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument();
  });

  it('renders required field indicators', () => {
    renderWithRouter(<UserNewPage />);

    const labels = screen.getAllByText('*');
    expect(labels.length).toBeGreaterThanOrEqual(3);
  });

  it('shows error when email is empty', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    expect(screen.getByText('Email is required')).toBeInTheDocument();
  });

  it('shows error when password is empty', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'test@bukoo.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    expect(screen.getByText('Password is required')).toBeInTheDocument();
  });

  it('shows error when password is too short', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'test@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'short' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Doe' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument();
  });

  it('shows error when full name is empty', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'test@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'password123' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    expect(screen.getByText('Full name is required')).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'john@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Admin' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    await waitFor(() => {
      expect(userApi.registerAdmin).toHaveBeenCalledWith({
        registerAdminRequest: {
          email: 'john@bukoo.com',
          password: 'SecurePass123!',
          fullName: 'John Admin',
          dateOfBirth: undefined,
        },
      });
    });
  });

  it('submits form with date of birth', async () => {
    renderWithRouter(<UserNewPage />);

    const dateInputs = screen.getAllByRole('textbox');
    const dateInput = dateInputs.find((input) => input.getAttribute('type') === 'date');

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'john@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Admin' },
      });
      if (dateInput) {
        fireEvent.change(dateInput, {
          target: { value: '1990-05-15' },
        });
      }
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    await waitFor(() => {
      const callArgs = userApi.registerAdmin.mock.calls[0][0];
      expect(callArgs.registerAdminRequest.email).toBe('john@bukoo.com');
      expect(callArgs.registerAdminRequest.fullName).toBe('John Admin');
    });
  });

  it('navigates to user detail page on success', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'john@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Admin' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin/users/user-new-1');
    });
  });

  it('shows error message on API failure', async () => {
    userApi.registerAdmin.mockRejectedValueOnce({
      response: {
        clone: () => ({
          text: () =>
            Promise.resolve(JSON.stringify({ error: { message: 'Email already exists' } })),
        }),
      },
    });

    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'existing@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Admin' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('disables submit button while submitting', async () => {
    userApi.registerAdmin.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ data: mockCreatedUser }), 50))
    );

    renderWithRouter(<UserNewPage />);

    const submitButton = document.querySelector('button[type="submit"]');

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: 'john@bukoo.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: 'John Admin' },
      });
      fireEvent.click(submitButton);
    });

    expect(submitButton).toBeDisabled();

    await waitFor(
      () => {
        expect(submitButton).not.toBeDisabled();
      },
      { timeout: 2000 }
    );
  });

  it('toggles password visibility', async () => {
    renderWithRouter(<UserNewPage />);

    const passwordInput = screen.getByPlaceholderText('Enter password');
    expect(passwordInput).toHaveAttribute('type', 'password');

    const form = passwordInput.closest('form');
    const toggleButton = form.querySelector('button[type="button"]');
    expect(toggleButton).toBeTruthy();

    await act(async () => {
      fireEvent.click(toggleButton);
    });

    expect(passwordInput).toHaveAttribute('type', 'text');
  });

  it('trims whitespace from email and full name', async () => {
    renderWithRouter(<UserNewPage />);

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('admin@example.com'), {
        target: { value: '  john@bukoo.com  ' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter password'), {
        target: { value: 'SecurePass123!' },
      });
      fireEvent.change(screen.getByPlaceholderText('John Doe'), {
        target: { value: '  John Admin  ' },
      });
      fireEvent.click(screen.getByRole('button', { name: /create admin/i }));
    });

    await waitFor(() => {
      const callArgs = userApi.registerAdmin.mock.calls[0][0];
      expect(callArgs.registerAdminRequest.email).toBe('john@bukoo.com');
      expect(callArgs.registerAdminRequest.fullName).toBe('John Admin');
    });
  });
});
