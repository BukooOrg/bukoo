import { BookApi, Configuration } from '@bukoo/api-client';
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('BookApi createBook request body', () => {
  let fetchSpy;
  let bookApi;

  beforeEach(() => {
    const mockBookResponse = {
      id: 'test-id',
      title: 'Test',
      price: '29.99',
      language: 'English',
      stock_quantity: 10,
      cover_url: null,
      isbn: null,
      description: null,
      page_count: null,
      published_date: null,
      is_active: true,
      publisher: null,
      category: null,
      authors: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    fetchSpy = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: mockBookResponse,
          meta: { request_id: 'test', timestamp: '2024-01-01T00:00:00Z' },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } }
      )
    );
    globalThis.fetch = fetchSpy;

    const config = new Configuration({ basePath: '', fetchApi: fetchSpy });
    bookApi = new BookApi(config);
  });

  it('sends correct request body with all fields filled', async () => {
    await bookApi.createBook({
      createBookRequest: {
        title: 'Test Book',
        price: '29.99',
        stockQuantity: 10,
        language: 'English',
        isbn: '978-0-123456-47-2',
        description: 'A test description.',
        pageCount: 320,
        publishedDate: new Date('2024-01-15'),
        publisherId: 'pub-1',
        categoryId: 'cat-1',
        authors: [{ authorId: 'auth-1', displayOrder: 1 }],
      },
    });

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    console.log('=== Full body ===');
    console.log(JSON.stringify(body, null, 2));

    expect(body.title).toBe('Test Book');
    expect(body.price).toBe('29.99');
    expect(body.stock_quantity).toBe(10);
    expect(body.language).toBe('English');
    expect(body.isbn).toBe('978-0-123456-47-2');
    expect(body.description).toBe('A test description.');
    expect(body.page_count).toBe(320);
    expect(body.published_date).toBe('2024-01-15');
    expect(body.publisher_id).toBe('pub-1');
    expect(body.category_id).toBe('cat-1');
    expect(body.authors).toEqual([{ author_id: 'auth-1', display_order: 1 }]);
  });

  it('sends correct request body with minimal fields', async () => {
    await bookApi.createBook({
      createBookRequest: {
        title: 'Minimal Book',
        price: '9.99',
        stockQuantity: 5,
        language: 'English',
      },
    });

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    console.log('=== Minimal body ===');
    console.log(JSON.stringify(body, null, 2));

    expect(body.title).toBe('Minimal Book');
    expect(body.price).toBe('9.99');
    expect(body.stock_quantity).toBe(5);
    expect(body.language).toBe('English');
    // Optional fields should be absent or null
    expect(body.isbn).toBeUndefined();
    expect(body.description).toBeUndefined();
    expect(body.page_count).toBeUndefined();
    expect(body.published_date).toBeUndefined();
    expect(body.publisher_id).toBeUndefined();
    expect(body.category_id).toBeUndefined();
    expect(body.authors).toEqual([]);
  });

  it('sends null ISBN correctly', async () => {
    await bookApi.createBook({
      createBookRequest: {
        title: 'No ISBN',
        price: '5.00',
        stockQuantity: 1,
        language: 'English',
        isbn: null,
      },
    });

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    console.log('=== Null ISBN body ===');
    console.log(JSON.stringify(body, null, 2));

    // null should be sent as null
    expect(body.isbn).toBeNull();
  });

  it('sends empty authors array correctly', async () => {
    await bookApi.createBook({
      createBookRequest: {
        title: 'No Authors',
        price: '5.00',
        stockQuantity: 1,
        language: 'English',
        authors: [],
      },
    });

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    console.log('=== Empty authors body ===');
    console.log(JSON.stringify(body, null, 2));

    expect(body.authors).toEqual([]);
  });

  it('sends price as number correctly', async () => {
    // Test what happens when we send price as a number (from parseFloat)
    await bookApi.createBook({
      createBookRequest: {
        title: 'Price Test',
        price: 29.99, // number, not string
        stockQuantity: 5,
        language: 'English',
      },
    });

    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    console.log('=== Number price body ===');
    console.log(JSON.stringify(body, null, 2));

    expect(body.price).toBe(29.99);
  });
});
