import { useEffect, useState } from 'react';

/**
 * Debounces a fast-changing value (search inputs) so a request is only fired
 * after the user pauses. Keeps filter typing from hammering the API.
 */
export function useDebouncedValue<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
