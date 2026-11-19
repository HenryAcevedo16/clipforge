# Graph Report - clipforge  (2026-11-19)

## Corpus Check
- 84 files · ~76,170 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .bat 6, (none) 3, .example 1)

## Summary
- 1016 nodes · 2532 edges · 54 communities (38 shown, 16 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `26d3b336`
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
- progress
- types.ts
- Api
- mock.ts
- create_job
- ClipCard.tsx
- Options
- BrandKit.tsx
- brand.ts
- CalendarView.tsx
- gen_map.py
- ProjectsList.tsx
- start.py
- extras.ts
- package.json
- _live_source
- compilerOptions
- server.py
- ClipEditor.tsx
- layout.tsx
- ask_claude
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
- _IgnoreWinReset
- PROVENANCE.md
- iniciar_mac_linux.sh

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
- `Start here (sesión local nueva)` --references--> `yt_run()`  [INFERRED]
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

## Communities (54 total, 16 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.12
Nodes (11): _anunciar_version(), api_version(), classic(), clip_for_edit(), get_file(), get_job(), get_zip(), index() (+3 more)

### Community 1 - "pipeline.py"
Cohesion: 0.06
Nodes (27): analyze_framing(), apply_zoom(), _ass_color(), _blur_bg(), build_ass(), _cam_panel(), _clean_word(), _cluster_people() (+19 more)

### Community 2 - "ai_backend"
Cohesion: 0.07
Nodes (31): config(), diagnostics(), gemini_models(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source() (+23 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.17
Nodes (17): Inner(), Page(), RecentProjects(), ProjectDetail(), FILTERS, STATE_META, SelectionNotice(), COLOR (+9 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.12
Nodes (22): Page(), ClipPreview(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime() (+14 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (42): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+34 more)

### Community 7 - "Path"
Cohesion: 0.10
Nodes (20): _all_words(), delete_clip(), _filter_path(), _group_words(), _job_info(), _live_src(), load_clip_for_edit(), _local_video() (+12 more)

### Community 8 - "progress"
Cohesion: 0.11
Nodes (23): align_clip(), Cancelled, check_cancel(), describe_device(), download(), hook(), _ggml_model(), _is_bot_check() (+15 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (22): guard(), extras, realApi, request(), AiSource, ApiError, ClipEditData, ClipEdits (+14 more)

### Community 11 - "mock.ts"
Cohesion: 0.17
Nodes (14): config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K, latency() (+6 more)

### Community 12 - "create_job"
Cohesion: 0.13
Nodes (12): cancel_job(), clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), create_job(), create_preview(), delete_job() (+4 more)

### Community 13 - "ClipCard.tsx"
Cohesion: 0.15
Nodes (22): ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO (+14 more)

### Community 14 - "Options"
Cohesion: 0.12
Nodes (18): _auto_keywords(), complete_endings(), _cookie_methods(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips() (+10 more)

### Community 15 - "BrandKit.tsx"
Cohesion: 0.11
Nodes (37): metadata, Page(), metadata, Page(), metadata, Page(), Accounts(), NETWORKS (+29 more)

### Community 16 - "brand.ts"
Cohesion: 0.29
Nodes (10): POS, PreviewProps, FontId, SubtitleStyleId, WatermarkPosition, ASPECT_META, FONT_META, FONT_ORDER (+2 more)

### Community 17 - "CalendarView.tsx"
Cohesion: 0.11
Nodes (43): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+35 more)

### Community 18 - "gen_map.py"
Cohesion: 0.15
Nodes (15): build_map(), clean(), _dash_summary(), Entry, _hash_summary(), list_files(), main(), _manifest_summary() (+7 more)

### Community 19 - "ProjectsList.tsx"
Cohesion: 0.23
Nodes (15): metadata, Page(), Ring(), SR, StageList(), projectTitle(), expiryText(), ProjectCard() (+7 more)

### Community 20 - "start.py"
Cohesion: 0.17
Nodes (9): main(), cap(), current_section(), doc_map(), main(), milestone_id(), read(), render() (+1 more)

### Community 21 - "extras.ts"
Cohesion: 0.12
Nodes (21): MODES, createExtras(), ExtrasCtx, K, load(), MockMode, NET_LABEL, networkLabel() (+13 more)

### Community 22 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 23 - "_live_source"
Cohesion: 0.12
Nodes (8): _cookie_opts(), _cookie_opts_now(), fetch_captions(), is_live_url(), _live_source(), parse_json3(), platform_of(), _tiktok_live_api()

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "ClipEditor.tsx"
Cohesion: 0.16
Nodes (12): FramingPreview(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS, TOGGLE_LABELS (+4 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "ask_claude"
Cohesion: 0.21
Nodes (8): ask_claude(), _ask_proxy(), classify_video(), _extract_json(), _grab_jpeg(), _included_cfg(), locate_player(), _proxy_url()

### Community 29 - "guard_read.py"
Cohesion: 0.27
Nodes (3): decide(), line_count(), main()

### Community 30 - "work"
Cohesion: 0.23
Nodes (9): _cleanup_partial(), work(), work(), work(), _edit_gate(), _worker(), progress(), begin_job() (+1 more)

### Community 31 - "process_live"
Cohesion: 0.08
Nodes (18): _add_nvidia_dll_dirs(), _clip_video_bytes(), _encoder_test(), _fmt_clock(), _frames_b64(), hw_info(), _kill_tree(), _live_keep_source() (+10 more)

### Community 32 - "_job_dir"
Cohesion: 0.18
Nodes (6): clip_delete(), clip_meta(), _job_age_ref(), _job_dir(), _no_cache_pages(), _refresh_result()

### Community 34 - "AGENTS.md"
Cohesion: 0.33
Nodes (4): Mapa de documentos, Protocolo, Reglas de coste (siempre), Reglas de tokens

### Community 35 - "Status"
Cohesion: 0.33
Nodes (5): Notas de entorno, Preguntas abiertas para el dueño, Session log (newest first), Start here (sesión local nueva), Status

### Community 37 - "NovoClip · frontend"
Cohesion: 0.40
Nodes (4): Cómo ejecutarlo, Datos simulados o reales, Estructura, NovoClip · frontend

### Community 38 - "mock-data.ts"
Cohesion: 0.17
Nodes (16): allJobs(), buildEvents(), ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs(), makeClips() (+8 more)

### Community 39 - "label"
Cohesion: 0.40
Nodes (3): fmt_tokens(), label(), size_label()

### Community 43 - "_render_clip_once"
Cohesion: 0.15
Nodes (10): _avoid_box(), Clip, _cut_clip(), keep_intervals(), player_track(), remap_time(), render_clip(), _render_clip_once() (+2 more)

## Knowledge Gaps
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06462585034013606 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.06717687074829932 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.11586452762923351 - nodes in this community are weakly interconnected._