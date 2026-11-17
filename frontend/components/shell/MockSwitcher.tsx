"use client";
import { useEffect, useState } from "react";
import { getMockMode, USE_MOCK, type MockMode } from "@/lib/api";
import { writeString } from "@/lib/api/storage";

const MODES: { v: MockMode; l: string }[] = [
  { v: "normal", l: "Normal" },
  { v: "empty", l: "Vacío (sin datos)" },
  { v: "error", l: "Con errores" },
  { v: "slow", l: "Carga lenta" },
  { v: "extreme", l: "Caso extremo" },
];

/**
 * Solo en modo simulado. Cambia el tipo de datos de ejemplo para revisar cada estado de pantalla
 * (vacío, error, carga lenta, datos extremos). Se guarda en el navegador y recarga la página.
 */
export function MockSwitcher({ className = "" }: { className?: string }) {
  const [mode, setMode] = useState<MockMode>("normal");
  useEffect(() => setMode(getMockMode()), []);
  if (!USE_MOCK) {
    return <p className={`text-xs text-ink-3 ${className}`}>Conectado al servidor real</p>;
  }
  return (
    <div className={className}>
      <label htmlFor="mockmode" className="mb-1 block text-xs font-semibold text-ink-3">
        Datos de prueba (simulados)
      </label>
      <select
        id="mockmode"
        value={mode}
        onChange={(e) => {
          writeString("novoclip:mock:mode", e.target.value);
          setMode(e.target.value as MockMode);
          window.location.reload();
        }}
        className="min-h-10 w-full rounded-xl border border-line bg-raised px-2.5 text-base font-medium text-ink-2 transition-colors hover:border-line-2 lg:text-sm"
      >
        {MODES.map((m) => (
          <option key={m.v} value={m.v}>
            {m.l}
          </option>
        ))}
      </select>
    </div>
  );
}
