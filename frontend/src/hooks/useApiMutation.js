import { useState } from 'react';

/**
 * Generic hook for mutations using the SDK client
 * @param {Function} mutationFn - Async function that calls SDK API method
 * @param {Object} options - Optional configuration
 * @param {Function} options.onSuccess - Callback on successful mutation
 * @param {Function} options.onError - Callback on mutation error
 * @returns {{ data: any, loading: boolean, error: Error | null, mutate: Function }}
 */
export function useApiMutation(mutationFn, options = {}) {
  const { onSuccess, onError } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mutate = async (variables) => {
    setLoading(true);
    setError(null);

    try {
      const response = await mutationFn(variables);
      setData(response.data);
      onSuccess?.(response.data);
      return response.data;
    } catch (err) {
      setError(err);
      onError?.(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, mutate };
}
