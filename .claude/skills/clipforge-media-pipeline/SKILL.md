---
name: clipforge-media-pipeline
description: Project-specific engineering guide for ClipForge/NovoClip media processing. Use when changing video ingestion/downloads, yt-dlp, Twitch/Kick/TikTok live capture, Whisper transcription, clip scoring and boundaries, face/speaker framing, captions, FFmpeg rendering, GPU encoders, audio processing, cancellation, or media job lifecycle.
---

# ClipForge Media Pipeline

Use this skill only for media-pipeline work. Do not load it for unrelated UI copy or documentation edits.

## Architecture first
1. Read docs/STATUS.md and the relevant section of docs/MAP.md.
2. If graphify-out/graph.json exists, run graphify query "<specific question>" before grep or source reads.
3. Locate symbols with grep -n; pipeline.py is large. Read only bounded line ranges.
4. Identify the existing pipeline stage and its callers before changing contracts. Prefer extending the existing stage over creating parallel logic.
5. Check current tests and fixtures before adding new abstractions.

## Pipeline invariants
- Preserve the sequence and data contracts between source ingestion, audio/video acquisition, transcription, segment selection, boundary refinement, reframing, caption composition, rendering, and result persistence.
- Keep times in seconds internally unless the surrounding contract explicitly uses milliseconds. Convert once at subsystem boundaries and name units in variables.
- Treat Whisper word timestamps as the source for word-level caption timing. Keep words, punctuation, segment offsets, and clip-relative timestamps aligned when extracting only a source interval.
- Clip starts/ends must preserve a complete thought and should snap to real silence/word boundaries only when that does not cut the intended hook or payoff.
- Never silently change score thresholds, clip count, min/max duration, or ranking semantics.
- Keep 9:16, 4:5, 1:1 and 16:9 output behavior explicit. Respect rotation metadata, SAR/DAR, crop coordinates, and safe zones for captions.
- Keep audio/video duration aligned. Preserve source audio unless the requested edit explicitly changes it. Mix background music with ducking; never let it mask speech.
- Retain existing modes: normal file, YouTube instant/subtitle path, quick download, full-download fallback, and live chunk processing.

## Downloads and live sources
- Use the existing yt-dlp integration and source-specific fallback behavior; do not replace working cookie/browser handling with a simpler anonymous-only path.
- Never print, commit, upload, or expose browser cookies, cookies.txt contents, session tokens, API keys, or signed media URLs in logs or error messages.
- Bound retries and timeouts. Distinguish unsupported URL, authentication/bot-check, transient network errors, unavailable source, and malformed media.
- For live jobs, preserve chunk boundaries, deduplication across adjacent chunks, stop/cancel semantics, and already completed clips.
- Do not delete source files or user media as part of routine cleanup. Clean only app-owned temporary files.

## FFmpeg and performance
- Reuse existing FFmpeg helpers and argument builders. Prefer argument arrays over shell command strings.
- Check return codes and capture enough stderr to diagnose failures without dumping huge logs.
- Keep hardware encoder selection capability-based (NVENC, AMF, QSV) and preserve the CPU/x264 fallback. Do not assume a GPU or codec exists because a GPU is detected.
- Release subprocesses, pipes, temporary files and GPU resources on success, failure, timeout and cancellation.
- Avoid unnecessary full-source downloads or transcodes. Preserve the existing instant/quick-download optimization where possible.
- Never put large media, generated renders, Whisper models, or job artifacts into Git.

## Tests and verification
- Prefer tiny synthetic fixtures over downloading real content.
- Test time conversion, clip-boundary math, subtitle offsets, aspect ratios, cancellation and fallback paths independently.
- For FFmpeg integration tests, use short generated color/sine sources and inspect output with ffprobe.
- Verify both success and failure paths. A mocked subprocess test does not prove a real codec works; state that distinction.
- Use the verification ladder: touched module → focused tests → one broader check. Stop at first failure.
- After code changes, refresh Graphify as required by CLAUDE.md.

## Scope discipline
Do not refactor unrelated pipeline stages while fixing one bug. Do not add a new media framework (for example Remotion) unless the architecture plan explicitly requires it. The current product uses Python/FFmpeg for media processing and Next.js for its interface.
