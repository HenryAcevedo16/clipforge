# Graph Report - clipforge  (2026-11-18)

## Corpus Check
- 84 files · ~75,433 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .bat 5, (none) 3, .example 1)

## Summary
- 1007 nodes · 2504 edges · 53 communities (36 shown, 17 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `24da183f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- pipeline.py
- ai_backend
- Code map
- ProjectsList.tsx
- HomeFlow.tsx
- NovoClip ✂️ — tu propia app de clipping
- Path
- cn
- types.ts
- Api
- mock.ts
- snap_to_silence
- Accounts.tsx
- ask_claude
- Accounts.tsx
- BrandKit.tsx
- CalendarView.tsx
- gen_map.py
- ProjectDetail.tsx
- start.py
- extras.ts
- package.json
- _live_source
- compilerOptions
- server.py
- ClipEditor.tsx
- layout.tsx
- _sp_run
- guard_read.py
- ApiError
- process_live
- summarize
- TwitchChat
- AGENTS.md
- Status
- _QuietLog
- NovoClip · frontend
- mock-data.ts
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- hw_info
- PROVENANCE.md
- iniciar_mac_linux.sh
- fetch_captions

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 36 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 36 edges
5. `Api` - 34 edges
6. `_render_clip_once()` - 32 edges
7. `process()` - 32 edges
8. `process_live()` - 30 edges
9. `Button()` - 30 edges
10. `HomeFlow()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `En la app` --references--> `gemini_key()`  [INFERRED]
  servidor_ia/LEEME.md → pipeline.py
- `IA incluida o clave propia (nuevo)` --references--> `gemini_key()`  [INFERRED]
  README.md → pipeline.py
- `hook()` --indirect_call--> `label()`  [INFERRED]
  pipeline.py → scripts/gen_map.py
- `_worker()` --uses--> `Options`  [INFERRED]
  app.py → pipeline.py
- `_worker()` --calls--> `process()`  [EXTRACTED]
  app.py → pipeline.py

## Import Cycles
- None detected.

## Communities (53 total, 17 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.05
Nodes (39): _anunciar_version(), api_version(), cancel_job(), classic(), _cleanup_partial(), clip_delete(), clip_for_edit(), clip_meta() (+31 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (39): analyze_framing(), apply_zoom(), _ass_color(), _avoid_box(), _blur_bg(), build_ass(), _cam_panel(), Cancelled (+31 more)

### Community 2 - "ai_backend"
Cohesion: 0.06
Nodes (35): config(), gemini_models(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status() (+27 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectsList.tsx"
Cohesion: 0.20
Nodes (14): metadata, Page(), RecentProjects(), FILTERS, projectTitle(), STATE_META, ProjectsList(), Tone (+6 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.10
Nodes (26): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), Settings (+18 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (42): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+34 more)

### Community 7 - "Path"
Cohesion: 0.10
Nodes (32): _all_words(), check_cancel(), classify_video(), download(), hook(), _ggml_model(), _group_words(), _job_info() (+24 more)

### Community 8 - "cn"
Cohesion: 0.25
Nodes (12): HOME_STEPS, Stepper(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO, Badge() (+4 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (23): extras, realApi, AiSource, ClipEditData, ClipEdits, ClipResult, ClipReview, ClipToggles (+15 more)

### Community 11 - "mock.ts"
Cohesion: 0.14
Nodes (17): buildEvents(), config, assetFor(), SeedJob, Ev, extras, failIfModeError(), getMockMode() (+9 more)

### Community 13 - "Accounts.tsx"
Cohesion: 0.15
Nodes (17): NETWORKS, NetworkIcon(), FramingPreview(), clipText(), Net, NETS, PublishDialog(), svg (+9 more)

### Community 14 - "ask_claude"
Cohesion: 0.13
Nodes (17): _auto_keywords(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips(), _norm() (+9 more)

### Community 15 - "Accounts.tsx"
Cohesion: 0.17
Nodes (16): metadata, Page(), AI_LABEL, AI_SUB, DIAG_ICON, Diagnostics(), Settings(), TIER (+8 more)

### Community 16 - "BrandKit.tsx"
Cohesion: 0.16
Nodes (23): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+15 more)

### Community 17 - "CalendarView.tsx"
Cohesion: 0.12
Nodes (41): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+33 more)

### Community 18 - "gen_map.py"
Cohesion: 0.15
Nodes (10): build_map(), Entry, fmt_tokens(), list_files(), main(), markdown_sections(), render(), label() (+2 more)

### Community 19 - "ProjectDetail.tsx"
Cohesion: 0.19
Nodes (19): metadata, Page(), Inner(), Page(), Accounts(), ScheduleDialog(), ResultStep(), ResultThumb() (+11 more)

### Community 20 - "start.py"
Cohesion: 0.18
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.12
Nodes (21): MODES, createExtras(), ExtrasCtx, K, load(), MockMode, NET_LABEL, networkLabel() (+13 more)

### Community 22 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 23 - "_live_source"
Cohesion: 0.22
Nodes (4): is_live_url(), _live_source(), platform_of(), _tiktok_live_api()

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "ClipEditor.tsx"
Cohesion: 0.18
Nodes (9): ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS, TOGGLE_LABELS, Tool (+1 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "_sp_run"
Cohesion: 0.14
Nodes (9): align_clip(), Clip, _clip_video_bytes(), _cut_clip(), _frames_b64(), _live_keep_source(), review_clip(), run() (+1 more)

### Community 29 - "guard_read.py"
Cohesion: 0.24
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "ApiError"
Cohesion: 0.50
Nodes (3): guard(), request(), ApiError

### Community 31 - "process_live"
Cohesion: 0.15
Nodes (11): main(), cancel_thread(), _fmt_clock(), _kill_tree(), process_live(), progress(), start_rec(), sub() (+3 more)

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

### Community 43 - "hw_info"
Cohesion: 0.15
Nodes (8): _add_nvidia_dll_dirs(), describe_device(), _encoder_test(), hw_info(), use_gpu(), video_encoder(), whispercpp_exe(), _windows_gpus()

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05031645569620253 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.048726953467954345 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.0632996632996633 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.09759759759759759 - nodes in this community are weakly interconnected._