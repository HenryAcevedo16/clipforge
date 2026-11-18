# Graph Report - clipforge  (2026-11-18)

## Corpus Check
- 84 files · ~74,773 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .bat 4, (none) 3, .example 1)

## Summary
- 988 nodes · 2489 edges · 57 communities (38 shown, 19 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8ab1311e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- pipeline.py
- ai_backend
- Code map
- ProjectDetail.tsx
- HomeFlow.tsx
- NovoClip ✂️ — tu propia app de clipping
- Options
- process_live
- types.ts
- Api
- mock.ts
- Path
- cn
- ask_claude
- Accounts.tsx
- BrandKit.tsx
- CalendarView.tsx
- gen_map.py
- ProjectsList.tsx
- start.py
- extras.ts
- package.json
- create_job
- compilerOptions
- server.py
- cn
- layout.tsx
- align_clip
- guard_read.py
- _worker
- _live_source
- summarize
- TwitchChat
- AGENTS.md
- Status
- _QuietLog
- NovoClip · frontend
- mock-data.ts
- _job_dir
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- ask_claude
- delete_job
- PROVENANCE.md
- iniciar_mac_linux.sh
- fetch_captions
- _IgnoreWinReset
- _job_age_ref

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `NovoClip ✂️ — tu propia app de clipping` - 36 edges
4. `Options` - 36 edges
5. `Api` - 34 edges
6. `_render_clip_once()` - 32 edges
7. `process()` - 32 edges
8. `Button()` - 30 edges
9. `process_live()` - 29 edges
10. `HomeFlow()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `En la app` --references--> `gemini_key()`  [INFERRED]
  servidor_ia/LEEME.md → pipeline.py
- `IA incluida o clave propia (nuevo)` --references--> `gemini_key()`  [INFERRED]
  README.md → pipeline.py
- `hook()` --indirect_call--> `label()`  [INFERRED]
  pipeline.py → scripts/gen_map.py
- `guard()` --calls--> `ApiError`  [EXTRACTED]
  frontend/lib/api/extras.ts → frontend/lib/api/types.ts
- `request()` --calls--> `ApiError`  [EXTRACTED]
  frontend/lib/api/real.ts → frontend/lib/api/types.ts

## Import Cycles
- None detected.

## Communities (57 total, 19 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.11
Nodes (12): _anunciar_version(), api_version(), classic(), diagnostics(), gemini_models(), get_file(), get_job(), get_zip() (+4 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (38): analyze_framing(), apply_zoom(), _ass_color(), _avoid_box(), _blur_bg(), build_ass(), _cam_panel(), Cancelled (+30 more)

### Community 2 - "ai_backend"
Cohesion: 0.07
Nodes (29): config(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key() (+21 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.18
Nodes (17): Inner(), Page(), RecentProjects(), ProjectDetail(), FILTERS, STATE_META, SelectionNotice(), Badge() (+9 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.10
Nodes (30): Page(), POS, PreviewProps, AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS (+22 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (39): Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, 🎯 Clips que terminan la idea, Consejos, Conversaciones y podcasts (nuevo), Desarrollo con Claude Code: skill de ahorro de tokens (+31 more)

### Community 7 - "Options"
Cohesion: 0.11
Nodes (28): main(), check_cancel(), classify_video(), describe_device(), download(), hook(), _ggml_model(), low_res_warning() (+20 more)

### Community 8 - "process_live"
Cohesion: 0.11
Nodes (13): _add_nvidia_dll_dirs(), _encoder_test(), hw_info(), _kill_tree(), start_rec(), _register(), run(), _silences_around() (+5 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (22): extras, realApi, request(), BrandTemplate, ClipEditData, ClipEdits, ClipReview, ClipToggles (+14 more)

### Community 11 - "mock.ts"
Cohesion: 0.14
Nodes (17): buildEvents(), config, assetFor(), SeedJob, Ev, extras, failIfModeError(), getMockMode() (+9 more)

### Community 12 - "Path"
Cohesion: 0.12
Nodes (17): _all_words(), Clip, _clip_video_bytes(), _cut_clip(), _frames_b64(), _group_words(), _job_info(), load_clip_for_edit() (+9 more)

### Community 13 - "cn"
Cohesion: 0.15
Nodes (24): ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO (+16 more)

### Community 14 - "ask_claude"
Cohesion: 0.12
Nodes (16): _auto_keywords(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips(), _norm() (+8 more)

### Community 15 - "Accounts.tsx"
Cohesion: 0.18
Nodes (15): metadata, Page(), Accounts(), NETWORKS, NetworkIcon(), FramingPreview(), Dialog(), PreviewNotice() (+7 more)

### Community 16 - "BrandKit.tsx"
Cohesion: 0.26
Nodes (12): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+4 more)

### Community 17 - "CalendarView.tsx"
Cohesion: 0.11
Nodes (43): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+35 more)

### Community 18 - "gen_map.py"
Cohesion: 0.15
Nodes (10): build_map(), Entry, fmt_tokens(), list_files(), main(), markdown_sections(), render(), label() (+2 more)

### Community 19 - "ProjectsList.tsx"
Cohesion: 0.23
Nodes (15): metadata, Page(), Ring(), SR, StageList(), projectTitle(), expiryText(), ProjectCard() (+7 more)

### Community 20 - "start.py"
Cohesion: 0.18
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.14
Nodes (19): MODES, createExtras(), ExtrasCtx, guard(), K, load(), MockMode, NET_LABEL (+11 more)

### Community 22 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 23 - "create_job"
Cohesion: 0.19
Nodes (9): clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), create_job(), create_preview(), _opts(), purge_expired() (+1 more)

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "cn"
Cohesion: 0.13
Nodes (27): metadata, Page(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS (+19 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 29 - "guard_read.py"
Cohesion: 0.24
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "_worker"
Cohesion: 0.27
Nodes (8): _cleanup_partial(), work(), work(), work(), _worker(), progress(), begin_job(), end_job()

### Community 31 - "_live_source"
Cohesion: 0.22
Nodes (4): is_live_url(), _live_source(), platform_of(), _tiktok_live_api()

### Community 32 - "summarize"
Cohesion: 0.36
Nodes (7): clean(), _dash_summary(), _hash_summary(), _markdown_summary(), _python_summary(), _slash_summary(), summarize()

### Community 34 - "AGENTS.md"
Cohesion: 0.33
Nodes (4): Mapa de documentos, Protocolo, Reglas de coste (siempre), Reglas de tokens

### Community 35 - "Status"
Cohesion: 0.33
Nodes (5): Environment notes, Open questions for the owner, Session log (newest first), Start here (next session), Status

### Community 37 - "NovoClip · frontend"
Cohesion: 0.40
Nodes (4): Cómo ejecutarlo, Datos simulados o reales, Estructura, NovoClip · frontend

### Community 38 - "mock-data.ts"
Cohesion: 0.29
Nodes (10): allJobs(), ASSET_KEYS, CLIP_POOL, ClipSeed, extremeJobs(), makeClips(), makeResult(), NOW() (+2 more)

### Community 39 - "_job_dir"
Cohesion: 0.22
Nodes (6): clip_delete(), clip_for_edit(), clip_meta(), _job_dir(), _no_cache_pages(), _refresh_result()

### Community 43 - "ask_claude"
Cohesion: 0.24
Nodes (7): ask_claude(), _ask_proxy(), _extract_json(), _grab_jpeg(), _included_cfg(), locate_player(), _proxy_url()

### Community 44 - "delete_job"
Cohesion: 0.33
Nodes (3): cancel_job(), delete_job(), cancel_thread()

## Knowledge Gaps
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.049883449883449886 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.07246376811594203 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.1006006006006006 - nodes in this community are weakly interconnected._