import { setToken, clearToken } from '@/lib/apiClient';

const API_BASE_URL = '/api/app/v1';

export async function loginAction(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const result = await response.json();

    if (!response.ok) {
      return { error: result.error?.message || 'Authentication failed' };
    }

    setToken(result.data.access_token);

    return { success: true, data: result.data };
  } catch (err) {
    console.error(err);
    return { error: 'Could not connect to the authentication server' };
  }
}

export async function registerAction(email, password, fullName) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        confirm_password: password,
        full_name: fullName,
        date_of_birth: '1990-01-01',
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      return { error: result.error?.message || 'Registration failed' };
    }

    return { success: true, data: result.data };
  } catch (err) {
    console.error(err);
    return { error: 'Could not connect to the authentication server' };
  }
}

export async function logoutAction() {
  clearToken();
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    // Ignore errors during logout
  }
  return { success: true };
}
