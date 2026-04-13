"use client";

import { startTransition, useEffect, useReducer, useState } from "react";

type UseApiResourceResult<T> = {
  data: T | null;
  error: unknown;
  loading: boolean;
  refreshing: boolean;
  reload: () => void;
};

export function useApiResource<T>(
  loader: () => Promise<T>,
  deps: readonly unknown[],
): UseApiResourceResult<T> {
  const [reloadKey, reload] = useReducer((value: number) => value + 1, 0);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let active = true;
    const hasData = data !== null;

    if (hasData) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    loader()
      .then((result) => {
        if (!active) {
          return;
        }
        startTransition(() => {
          setData(result);
          setLoading(false);
          setRefreshing(false);
        });
      })
      .catch((nextError: unknown) => {
        if (!active) {
          return;
        }
        startTransition(() => {
          setError(nextError);
          setLoading(false);
          setRefreshing(false);
        });
      });

    return () => {
      active = false;
    };
  }, [...deps, reloadKey]);

  return {
    data,
    error,
    loading,
    refreshing,
    reload,
  };
}
