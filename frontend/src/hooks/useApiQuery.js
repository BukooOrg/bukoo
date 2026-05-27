import { useEffect, useRef, useState } from 'react';

/**
 * Generic hook for fetching data using the SDK client
 * @param {Function} queryFn - Async function that calls SDK API method
 * @param {Object} options - Optional configuration
 * @param {boolean} options.skip - Skip the query (default: false)
 * @returns {{ data: any, loading: boolean, error: Error | null }}
 */
export function useApiQuery(queryFn, options = {}) {
  const { skip = false } = options;

  const queryFnRef = useRef(queryFn);
  queryFnRef.current = queryFn;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(!skip);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (skip) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchData() {
      try {
        const response = await queryFnRef.current();
        if (!cancelled) {
          setData(response.data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [skip]);

  return { data, loading, error };
}
