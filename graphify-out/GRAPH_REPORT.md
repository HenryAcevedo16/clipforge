# Graph Report - clipforge  (2026-11-19)

## Corpus Check
- 85 files · ~76,401 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .bat 6, (none) 5, .example 1)

## Summary
- 1013 nodes · 2547 edges · 57 communities (43 shown, 14 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `53c24d17`
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
- Path
- get
- types.ts
- Api
- mock.ts
- create_job
- ClipCard.tsx
- Options
- BrandKit.tsx
- _cookie_opts_now
- CalendarView.tsx
- gen_map.py
- brand.ts
- start.py
- extras.ts
- package.json
- novoclip
- compilerOptions
- server.py
- ClipEditor.tsx
- layout.tsx
- summarize
- guard_read.py
- work
- process_live
- _job_dir
- TwitchChat
- AGENTS.md
- Status
- _QuietLog
- NovoClip · frontend
- mock-data.ts
- label
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- _render_clip_once
- diagnostics
- PROVENANCE.md
- iniciar_mac_linux.sh
- Settings.tsx
- delete_job
- purge_expired
- get
- Servidor de IA de NovoClip (IA incluida)
- next.config.ts

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 39 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 36 edges
5. `Api` - 34 edges
6. `_render_clip_once()` - 32 edges
7. `process()` - 32 edges
8. `Button()` - 30 edges
9. `process_live()` - 30 edges
10. `HomeFlow()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Start here (sesiÃ³n local nueva)` --references--> `yt_run()`  [INFERRED]
  docs/STATUS.md → pipeline.py
- `En la app` --references--> `gemini_key()`  [INFERRED]
  servidor_ia/LEEME.md → pipeline.py
- `IA incluida o clave propia (nuevo)` --references--> `gemini_key()`  [INFERRED]
  README.md → pipeline.py
- `hook()` --indirect_call--> `label()`  [INFERRED]
  pipeline.py → scripts/gen_map.py
- `_worker()` --uses--> `Options`  [INFERRED]
  app.py → pipeline.py

## Import Cycles
- None detected.

## Communities (57 total, 14 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.12
Nodes (5): _anunciar_version(), api_version(), _IgnoreWinReset, settings(), _version()

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (38): _worker(), analyze_framing(), apply_zoom(), _ass_color(), _avoid_box(), begin_job(), _blur_bg(), build_ass() (+30 more)

### Community 2 - "ai_backend"
Cohesion: 0.08
Nodes (31): config(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key(), ask_claude() (+23 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.16
Nodes (26): Inner(), Page(), metadata, Page(), RecentProjects(), ProjectDetail(), FILTERS, projectTitle() (+18 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.11
Nodes (28): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), Settings (+20 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (42): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+34 more)

### Community 7 - "Path"
Cohesion: 0.07
Nodes (37): align_clip(), _all_words(), Clip, _cut_clip(), download(), hook(), _ggml_model(), _group_words() (+29 more)

### Community 8 - "get"
Cohesion: 0.18
Nodes (8): classic(), gemini_models(), get_file(), get_job(), get_zip(), index(), _job_from_disk(), list_projects()

### Community 9 - "types.ts"
Cohesion: 0.10
Nodes (21): guard(), extras, realApi, request(), ApiError, ClipEditData, ClipEdits, ClipReview (+13 more)

### Community 11 - "mock.ts"
Cohesion: 0.17
Nodes (14): config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K, latency() (+6 more)

### Community 12 - "create_job"
Cohesion: 0.23
Nodes (7): clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), create_job(), create_preview(), _opts()

### Community 13 - "ClipCard.tsx"
Cohesion: 0.24
Nodes (17): ScheduleDialog(), ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel() (+9 more)

### Community 14 - "Options"
Cohesion: 0.11
Nodes (18): main(), _auto_keywords(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips() (+10 more)

### Community 15 - "BrandKit.tsx"
Cohesion: 0.14
Nodes (25): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+17 more)

### Community 16 - "_cookie_opts_now"
Cohesion: 0.17
Nodes (6): _cookie_methods(), _cookie_opts(), _cookie_opts_now(), fetch_captions(), _find_cookies_file(), parse_json3()

### Community 17 - "CalendarView.tsx"
Cohesion: 0.12
Nodes (40): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+32 more)

### Community 18 - "gen_map.py"
Cohesion: 0.21
Nodes (7): build_map(), Entry, list_files(), main(), markdown_sections(), render(), scan()

### Community 19 - "brand.ts"
Cohesion: 0.29
Nodes (10): POS, PreviewProps, FontId, SubtitleStyleId, WatermarkPosition, ASPECT_META, FONT_META, FONT_ORDER (+2 more)

### Community 20 - "start.py"
Cohesion: 0.21
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.16
Nodes (17): createExtras(), ExtrasCtx, K, load(), NET_LABEL, networkLabel(), seedAccounts(), seedTemplates() (+9 more)

### Community 22 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 23 - "novoclip"
Cohesion: 0.22
Nodes (8): NOVOCLIP_WORKERS, build, environment, ports, restart, volumes, services, novoclip

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "ClipEditor.tsx"
Cohesion: 0.16
Nodes (17): NETWORKS, NetworkIcon(), FramingPreview(), clipText(), Net, NETS, svg, MAP (+9 more)

### Community 27 - "layout.tsx"
Cohesion: 0.26
Nodes (8): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), ToastProvider()

### Community 28 - "summarize"
Cohesion: 0.36
Nodes (7): clean(), _dash_summary(), _hash_summary(), _markdown_summary(), _python_summary(), _slash_summary(), summarize()

### Community 29 - "guard_read.py"
Cohesion: 0.21
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "work"
Cohesion: 0.24
Nodes (6): _cleanup_partial(), work(), work(), work(), _edit_gate(), progress()

### Community 31 - "process_live"
Cohesion: 0.07
Nodes (22): Cancelled, check_cancel(), _clip_video_bytes(), _fmt_clock(), _frames_b64(), _is_bot_check(), is_live_url(), _kill_tree() (+14 more)

### Community 32 - "_job_dir"
Cohesion: 0.20
Nodes (7): clip_delete(), clip_for_edit(), clip_meta(), _job_dir(), _no_cache_pages(), _refresh_result(), delete_clip()

### Community 34 - "AGENTS.md"
Cohesion: 0.33
Nodes (4): Mapa de documentos, Protocolo, Reglas de coste (siempre), Reglas de tokens

### Community 35 - "Status"
Cohesion: 0.40
Nodes (4): Notas de entorno, Preguntas abiertas para el dueÃ±o, Session log (newest first), Start here (sesiÃ³n local nueva)

### Community 37 - "NovoClip · frontend"
Cohesion: 0.40
Nodes (4): Cómo ejecutarlo, Datos simulados o reales, Estructura, NovoClip · frontend

### Community 38 - "mock-data.ts"
Cohesion: 0.16
Nodes (17): seedPosts(), allJobs(), buildEvents(), ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs() (+9 more)

### Community 39 - "label"
Cohesion: 0.40
Nodes (3): fmt_tokens(), label(), size_label()

### Community 43 - "_render_clip_once"
Cohesion: 0.15
Nodes (7): _add_nvidia_dll_dirs(), describe_device(), _encoder_test(), hw_info(), video_encoder(), whispercpp_exe(), _windows_gpus()

### Community 51 - "Settings.tsx"
Cohesion: 0.18
Nodes (14): metadata, Page(), metadata, Page(), Accounts(), AI_LABEL, AI_SUB, DIAG_ICON (+6 more)

### Community 52 - "delete_job"
Cohesion: 0.33
Nodes (3): cancel_job(), delete_job(), cancel_thread()

### Community 53 - "purge_expired"
Cohesion: 0.33
Nodes (3): _job_age_ref(), purge_expired(), _purge_loop()

### Community 54 - "get"
Cohesion: 0.40
Nodes (5): MockSwitcher(), MODES, MockMode, USE_MOCK, writeString()

### Community 55 - "Servidor de IA de NovoClip (IA incluida)"
Cohesion: 0.40
Nodes (4): Arrancarlo, En la app, Licencias, Servidor de IA de NovoClip (IA incluida)

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`, `Servidor de IA de NovoClip (IA incluida)`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11695906432748537 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05257936507936508 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.08115942028985507 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10756302521008404 - nodes in this community are weakly interconnected._