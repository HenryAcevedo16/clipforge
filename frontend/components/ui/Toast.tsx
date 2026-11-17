"use client";
import { toast, Toast } from "@heroui/react";
import { createContext, useCallback, useContext, type ReactNode } from "react";

const Ctx = createContext<(text: string, tone?: "ok" | "bad") => void>(() => {});
export const useToast = () => useContext(Ctx);

/** Avisos con el Toast de HeroUI. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const show = useCallback((text: string, tone: "ok" | "bad" = "ok") => {
    if (tone === "bad") toast.danger(text);
    else toast.success(text);
  }, []);
  return (
    <Ctx.Provider value={show}>
      {children}
      <Toast.Provider placement="bottom" />
    </Ctx.Provider>
  );
}
