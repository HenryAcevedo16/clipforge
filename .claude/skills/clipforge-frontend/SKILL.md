---
name: clipforge-frontend
description: Project-specific frontend engineering guide for ClipForge/NovoClip. Use when changing Next.js routes, React components, TypeScript API contracts, editor/timeline interactions, project progress, mock data, responsive UI, accessibility, or frontend performance.
---

# ClipForge Frontend Engineering

Load this skill for frontend tasks only.

## Project constraints
- Frontend source is frontend/; web/ is generated static output and must not be edited by hand.
- Stack: Next.js 16 App Router, React 19, TypeScript, Tailwind CSS 4 and HeroUI 3.
- Read frontend/AGENTS.md and the relevant frontend/LEEME.md section first.
- This Next.js version has breaking changes. Before writing code, read the relevant installed documentation under frontend/node_modules/next/dist/docs/; do not rely on remembered APIs.
- API types live in frontend/lib/api/types.ts. Keep the mock and real adapters aligned.
- NEXT_PUBLIC_USE_MOCK=true is the default for local UI work. Verify real backend behavior when changing API contracts.
- Kit de marca, calendario y cuentas have areas marked as preview / backend pending. Do not imply that those screens publish or persist server-side until implemented.

## UI implementation rules
- Reuse existing UI wrappers in frontend/components/ui/ and existing design tokens/styles before adding dependencies.
- Keep components focused. Extract shared logic only when it has more than one real consumer.
- Avoid boolean-prop proliferation; prefer composition and explicit variants.
- Keep progress, cancellation, retry, empty, loading, success and error states explicit.
- Preserve keyboard interaction, visible focus, semantic labels, contrast and reduced-motion preferences.
- Test mobile and desktop layouts, especially the clip editor, project list and creation flow.
- Avoid rendering or storing huge transcript/video payloads in UI state unless needed. Paginate, window or summarize long lists where appropriate.
- Avoid waterfalls in data fetching and unnecessary client components. Keep non-interactive rendering server-side where compatible with static export.
- Use stable keys and derived state; do not duplicate source-of-truth values.

## Clip editor correctness
- Keep the selected clip, source time range, displayed transcript range and caption corrections consistent.
- Distinguish source timestamps from clip-relative timestamps.
- Preserve click, double-click and modifier-key interactions in the transcript editor.
- Show the difference between preview-only metadata and changes actually persisted by the backend.
- Do not claim a rendered clip has changed until the backend job completes successfully.

## Verification
- Run the narrowest applicable typecheck/test first.
- Use cd frontend && npm run typecheck and npm run build when relevant.
- The app is exported statically: verify the configured output/export behavior and then copy build output to web/ only through the documented build workflow.
- Do not commit .next, node_modules, caches, or generated temporary media.
