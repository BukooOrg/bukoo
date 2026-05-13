import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { useApiQuery } from './useApiQuery';

describe('useApiQuery', () => {
  it('fetches data on mount', async () => {
    const mockData = { data: { id: 1 } };
    const queryFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() => useApiQuery(queryFn));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual({ id: 1 });
  });

  it('handles error', async () => {
    const error = new Error('API error');
    const queryFn = vi.fn().mockRejectedValue(error);

    const { result } = renderHook(() => useApiQuery(queryFn));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toEqual(error);
    expect(result.current.data).toBe(null);
  });

  it('skips fetch when skip is true', async () => {
    const queryFn = vi.fn();

    const { result } = renderHook(() => useApiQuery(queryFn, { skip: true }));

    expect(result.current.loading).toBe(false);
    expect(queryFn).not.toHaveBeenCalled();
  });
});
