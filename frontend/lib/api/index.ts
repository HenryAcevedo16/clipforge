import type { Api } from "./types";
import { mockApi } from "./mock";
import { realApi } from "./real";

/**
 * ÚNICA puerta de entrada a los datos. Las pantallas importan `api` y nunca saben si es simulado o real.
 * NEXT_PUBLIC_USE_MOCK=false -> backend real; cualquier otro valor (o ausente) -> simulado.
 */
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
export const api: Api = USE_MOCK ? mockApi : realApi;

export * from "./types";
export { getMockMode } from "./mock";
export type { MockMode } from "./extras";
export { networkLabel } from "./extras";
