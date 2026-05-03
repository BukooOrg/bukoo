import Cookies from 'js-cookie';

const API_BASE_URL = '/api';

export async function loginAction(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.detail || 'Authentication failed' };
    }

    // Set JWT in cookie
    Cookies.set('jwt', data.token, {
      expires: 1, // 1 day
      secure: window.location.protocol === 'https:',
      sameSite: 'strict',
    });

    return { success: true, user: data.user };
  } catch (err) {
    console.error(err);
    return { error: 'Could not connect to the authentication server' };
  }
}

export async function registerAction(email, password, fullName) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.detail || 'Registration failed' };
    }

    // Set JWT in cookie
    Cookies.set('jwt', data.token, {
      expires: 1,
      secure: window.location.protocol === 'https:',
      sameSite: 'strict',
    });

    return { success: true, user: data.user };
  } catch (err) {
    console.error(err);
    return { error: 'Could not connect to the authentication server' };
  }
}

export async function logoutAction() {
  Cookies.remove('jwt');
  Cookies.remove('cartId');
  return { success: true };
}
