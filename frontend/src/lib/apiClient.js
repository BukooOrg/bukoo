import {
  AuthApi,
  AuthorApi,
  HealthApi,
  UserApi,
  CategoryApi,
  Configuration,
  CollectionApi,
  BookApi,
  CartApi,
  WishlistApi,
  OrderApi,
  PublisherApi,
  ReviewApi,
  NotificationApi,
  InventoryApi,
  ReportApi,
} from '@bukoo/api-client';
import Cookies from 'js-cookie';

const TOKEN_KEY = 'bukoo_jwt';

export function getToken() {
  const sessionToken = sessionStorage.getItem(TOKEN_KEY);
  if (sessionToken) return sessionToken;
  return Cookies.get('jwt') || null;
}

export function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  Cookies.remove('jwt');
}

const configuration = new Configuration({
  basePath: '',
  middleware: [
    {
      pre: async (context) => {
        const token = getToken();
        if (token) {
          context.init.headers = {
            ...(context.init.headers || {}),
            Authorization: `Bearer ${token}`,
          };
        }
        return context;
      },
    },
  ],
});

export const authApi = new AuthApi(configuration);
export const authorApi = new AuthorApi(configuration);
export const bookApi = new BookApi(configuration);
export const cartApi = new CartApi(configuration);
export const categoryApi = new CategoryApi(configuration);
export const collectionApi = new CollectionApi(configuration);
export const healthApi = new HealthApi(configuration);
export const inventoryApi = new InventoryApi(configuration);
export const notificationApi = new NotificationApi(configuration);
export const orderApi = new OrderApi(configuration);
export const publisherApi = new PublisherApi(configuration);
export const reviewApi = new ReviewApi(configuration);
export const userApi = new UserApi(configuration);
export const wishlistApi = new WishlistApi(configuration);
export const reportApi = new ReportApi(configuration);

export async function uploadBookCover(bookId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const headers = {};
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`/api/app/v1/books/${bookId}/cover`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body?.error?.message || body?.detail || 'Upload failed';
    throw new Error(message);
  }

  return response.json();
}
