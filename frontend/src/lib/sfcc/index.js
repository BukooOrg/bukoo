import Cookies from 'js-cookie';

import mockCollections from '@/data/mock/collections.json';
// Import mock data
import mockProducts from '@/data/mock/products.json';

import { apiFetch } from '../api';

import { reshapeProduct, reshapeCategory, reshapeCategories, reshapeProducts } from './utils';

const USE_MOCK = import.meta.env.VITE_MOCK_MODE === 'true';

export async function getSFCCMode() {
  return 'live';
}

export async function getCollections() {
  if (USE_MOCK) {
    return reshapeCategories(mockCollections);
  }
  try {
    return await apiFetch('/collections');
  } catch (error) {
    console.warn('API failed, falling back to mock data', error);
    return reshapeCategories(mockCollections);
  }
}

export async function getCollection(id) {
  if (USE_MOCK) {
    const coll = mockCollections.find((c) => c.id === id || c.handle === id);
    return reshapeCategory(coll);
  }
  try {
    return await apiFetch(`/collections/${id}`);
  } catch (error) {
    console.error(error);
    const coll = mockCollections.find((c) => c.id === id || c.handle === id);
    return reshapeCategory(coll);
  }
}

export async function getProduct(handle) {
  if (USE_MOCK) {
    const prod = mockProducts.find((p) => p.handle === handle || p.id === handle);
    return reshapeProduct(prod);
  }
  try {
    return await apiFetch(`/products/${handle}`);
  } catch (error) {
    console.error(error);

    const prod = mockProducts.find((p) => p.handle === handle || p.id === handle);
    return reshapeProduct(prod);
  }
}

export async function getCollectionProducts({
  collection: collectionHandle,
  limit = 100,
  sortKey,
  query,
}) {
  if (USE_MOCK) {
    const results = mockProducts.filter(
      (p) =>
        !collectionHandle || p.categoryId === collectionHandle || collectionHandle === 'joyco-root'
    );
    return reshapeProducts(results.slice(0, limit));
  }
  try {
    const params = new URLSearchParams({ limit });
    if (sortKey) params.append('sortKey', sortKey);
    if (query) params.append('query', query);

    return await apiFetch(`/collections/${collectionHandle}/products?${params.toString()}`);
  } catch (error) {
    console.error(error);

    const results = mockProducts.filter(
      (p) =>
        !collectionHandle || p.categoryId === collectionHandle || collectionHandle === 'joyco-root'
    );
    return reshapeProducts(results.slice(0, limit));
  }
}

export async function getProducts({ query, sortKey }) {
  if (USE_MOCK) {
    const results = query
      ? mockProducts.filter((p) => p.title.toLowerCase().includes(query.toLowerCase()))
      : mockProducts;
    return reshapeProducts(results);
  }
  try {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (sortKey) params.append('sortKey', sortKey);
    return await apiFetch(`/products?${params.toString()}`);
  } catch (error) {
    console.error(error);

    const results = query
      ? mockProducts.filter((p) => p.title.toLowerCase().includes(query.toLowerCase()))
      : mockProducts;
    return reshapeProducts(results);
  }
}

export async function createCart() {
  if (USE_MOCK) {
    const cart = {
      id: 'mock-cart',
      lines: [],
      cost: {
        totalAmount: { amount: '0', currencyCode: 'GBP' },
        totalTaxAmount: { amount: '0', currencyCode: 'GBP' },
      },
    };
    Cookies.set('cartId', cart.id, { expires: 30, path: '/' });
    return cart;
  }
  try {
    const cart = await apiFetch('/cart', { method: 'POST' });
    Cookies.set('cartId', cart.id, { expires: 30, path: '/' });
    return cart;
  } catch {
    return {
      id: 'mock-cart',
      lines: [],
      cost: {
        totalAmount: { amount: '0', currencyCode: 'GBP' },
        totalTaxAmount: { amount: '0', currencyCode: 'GBP' },
      },
    };
  }
}

export async function getCart() {
  const cartId = Cookies.get('cartId');
  if (!cartId) return null;

  if (cartId === 'mock-cart') {
    return {
      id: 'mock-cart',
      lines: [],
      totalQuantity: 0,
      cost: {
        totalAmount: { amount: '0', currencyCode: 'GBP' },
        totalTaxAmount: { amount: '0', currencyCode: 'GBP' },
      },
    };
  }

  try {
    return await apiFetch(`/cart/${cartId}`);
  } catch {
    return null;
  }
}

export async function addToCart(lines) {
  const cartId = Cookies.get('cartId');
  if (!cartId) {
    await createCart();
  }

  const currentId = Cookies.get('cartId');
  if (currentId === 'mock-cart') return;

  try {
    return await apiFetch(`/cart/${currentId}/items`, {
      method: 'POST',
      body: JSON.stringify(lines[0] || lines),
    });
  } catch {
    return;
  }
}

export async function removeFromCart(lineIds) {
  const cartId = Cookies.get('cartId');
  if (!cartId || cartId === 'mock-cart') return;
  try {
    return await apiFetch(`/cart/${cartId}/items/${lineIds[0]}`, { method: 'DELETE' });
  } catch {
    return;
  }
}

export async function updateCart(lines) {
  const cartId = Cookies.get('cartId');
  if (!cartId || cartId === 'mock-cart') return;
  try {
    const line = lines[0];
    return await apiFetch(`/cart/${cartId}/items/${line.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity: line.quantity }),
    });
  } catch {
    return;
  }
}

export async function getProductRecommendations(productId) {
  if (USE_MOCK) return reshapeProducts(mockProducts.slice(0, 4));
  try {
    return await apiFetch(`/products/${productId}/recommendations`);
  } catch {
    return reshapeProducts(mockProducts.slice(0, 4));
  }
}

export async function getShippingMethods() {
  return [{ id: 'standard', label: 'Standard Shipping', price: '0' }];
}
