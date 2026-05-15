import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { useApiMutation } from './useApiMutation';

describe('useApiMutation', () => {
  it('mutates data on call', async () => {
    const mockResponse = { data: { id: 1 } };
    const mutationFn = vi.fn().mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApiMutation(mutationFn));

    expect(result.current.loading).toBe(false);

    result.current.mutate({ name: 'test' });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual({ id: 1 });
    });

    expect(mutationFn).toHaveBeenCalledWith({ name: 'test' });
  });

  it('handles error', async () => {
    const error = new Error('API error');
    const mutationFn = vi.fn().mockRejectedValue(error);

    const { result } = renderHook(() => useApiMutation(mutationFn));

    result.current.mutate({ name: 'test' }).catch(() => {});

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).not.toBeNull();
    });
  });

  it('calls onSuccess callback', async () => {
    const mockData = { data: { id: 1 } };
    const mutationFn = vi.fn().mockResolvedValue(mockData);
    const onSuccess = vi.fn();

    const { result } = renderHook(() => useApiMutation(mutationFn, { onSuccess }));

    await result.current.mutate({ name: 'test' });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith({ id: 1 });
    });
  });

  it('calls onError callback', async () => {
    const error = new Error('API error');
    const mutationFn = vi.fn().mockRejectedValue(error);
    const onError = vi.fn();

    const { result } = renderHook(() => useApiMutation(mutationFn, { onError }));

    await expect(result.current.mutate({ name: 'test' })).rejects.toThrow('API error');

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(error);
    });
  });
});
