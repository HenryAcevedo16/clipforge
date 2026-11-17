import type { Job } from "./api/types";

/** Título legible de un trabajo: el del video si ya se conoce; si no, el nombre del archivo o "Video de YouTube (id)". */
export function jobTitle(job: Pick<Job, "source" | "result">): string {
  if (job.result?.title) return job.result.title;
  const s = job.source || "";
  if (/^https?:\/\//.test(s)) {
    const m = s.match(/[?&]v=([\w-]{6,})/) ?? s.match(/youtu\.be\/([\w-]{6,})/);
    return m ? `Video de YouTube (${m[1]})` : "Video de YouTube";
  }
  return s || "Video sin título";
}
