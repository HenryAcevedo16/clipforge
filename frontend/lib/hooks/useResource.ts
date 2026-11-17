"use client";
import { useCallback, useEffect, useRef, useState } from "react";

export interface Resource<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: (silent?: boolean) => void;
  /** Cambia los datos en pantalla sin volver a pedirlos (actualización optimista). */
  set: (v: T | ((prev: T | null) => T)) => void;
}

/**
 * Carga datos asíncronos con sus 3 estados (cargando / error / datos). `reload()` vuelve a pedirlos.
 * Ignora respuestas viejas si el componente se desmonta o llega otra petición después.
 */
export function useResource<T>(fn: () => Promise<T>, deps: unknown[] = []): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useRef(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const load = useCallback((silent = false) => {
    const id = ++run.current;
    if (!silent) {
      setLoading(true);
      setError(null);
    }
    fnRef.current().then(
      (d) => {
        if (id !== run.current) return;
        setData(d);
        setError(null);
        setLoading(false);
      },
      (e: unknown) => {
        if (id !== run.current) return;
        setError(e instanceof Error ? e.message : "Algo salió mal. Inténtalo de nuevo.");
        setLoading(false);
      },
    );
  }, []);

  useEffect(() => {
    load();
    return () => {
      run.current++;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const set = useCallback((v: T | ((prev: T | null) => T)) => setData((p) => (typeof v === "function" ? (v as (p: T | null) => T)(p) : v)), []);
  return { data, error, loading, reload: (silent?: boolean) => load(silent), set };
}
