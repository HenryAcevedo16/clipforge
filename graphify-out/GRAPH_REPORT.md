# Graph Report - clipforge  (2026-11-20)

## Corpus Check
- 91 files · ~82,175 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .bat 6, (none) 5, .example 1)

## Summary
- 1121 nodes · 2723 edges · 60 communities (46 shown, 14 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `93296708`
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
- process
- Path
- types.ts
- Api
- mock.ts
- create_job
- ClipCard.tsx
- Options
- Accounts.tsx
- ClipEditor.tsx
- package.json
- get
- start.py
- extras.ts
- _job_age_ref
- novoclip
- compilerOptions
- server.py
- BrandKit.tsx
- layout.tsx
- gen_map.py
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
- summarize
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- novoclip_signals.py
- Servidor de IA de NovoClip (IA incluida)
- PROVENANCE.md
- iniciar_mac_linux.sh
- opus-worker.md
- _live_source
- optimize_clip
- time.ts
- test_clip_editing.py
- Equipo de desarrollo IA de ClipForge
- shutil
- sonnet-reviewer.md

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 43 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 37 edges
5. `process()` - 34 edges
6. `Api` - 34 edges
7. `_render_clip_once()` - 32 edges
8. `optimize_clip()` - 31 edges
9. `process_live()` - 30 edges
10. `Button()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Start here (sesiÃ³n local nueva)` --references--> `yt_run()`  [INFERRED]
  docs/STATUS.md → pipeline.py
- `En la app` --references--> `gemini_key()`  [INFERRED]
  servidor_ia/LEEME.md → pipeline.py
- `IA incluida o clave propia (nuevo)` --references--> `gemini_key()`  [INFERRED]
  README.md → pipeline.py
- `hook()` --indirect_call--> `label()`  [INFERRED]
  pipeline.py → scripts/gen_map.py
- `test_rerender_inside_saved_piece_does_not_download()` --calls--> `rerender_clip()`  [EXTRACTED]
  tests/test_clip_editing.py → pipeline.py

## Import Cycles
- None detected.

## Communities (60 total, 14 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.12
Nodes (5): _anunciar_version(), api_version(), _IgnoreWinReset, settings(), _version()

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (33): _all_words(), analyze_framing(), apply_zoom(), _ass_color(), _attach_replay_signals(), _avoid_box(), _blur_bg(), build_ass() (+25 more)

### Community 2 - "ai_backend"
Cohesion: 0.10
Nodes (27): config(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key(), ask_claude() (+19 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.13
Nodes (31): metadata, Page(), Inner(), Page(), metadata, Page(), Accounts(), RecentProjects() (+23 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.09
Nodes (26): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), Settings (+18 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.04
Nodes (45): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+37 more)

### Community 7 - "process"
Cohesion: 0.12
Nodes (22): align_clip(), check_cancel(), classify_video(), describe_device(), download(), hook(), _ggml_model(), low_res_warning() (+14 more)

### Community 8 - "Path"
Cohesion: 0.09
Nodes (20): Clip, _clip_video_bytes(), _cut_clip(), delete_clip(), _filter_path(), _frames_b64(), _grab_jpeg(), _keep_clip_source() (+12 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (23): guard(), extras, realApi, request(), AiSource, ApiError, ClipEditData, ClipEdits (+15 more)

### Community 11 - "mock.ts"
Cohesion: 0.17
Nodes (14): config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K, latency() (+6 more)

### Community 12 - "create_job"
Cohesion: 0.20
Nodes (9): clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), create_job(), create_preview(), _opts(), purge_expired() (+1 more)

### Community 13 - "ClipCard.tsx"
Cohesion: 0.26
Nodes (16): ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO (+8 more)

### Community 14 - "Options"
Cohesion: 0.10
Nodes (21): _auto_keywords(), _best_hook(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips() (+13 more)

### Community 15 - "Accounts.tsx"
Cohesion: 0.14
Nodes (20): NETWORKS, NetworkIcon(), FramingPreview(), clipText(), Net, NETS, svg, MAP (+12 more)

### Community 16 - "ClipEditor.tsx"
Cohesion: 0.13
Nodes (22): metadata, Page(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS (+14 more)

### Community 17 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 19 - "get"
Cohesion: 0.14
Nodes (8): classic(), clip_for_edit(), diagnostics(), gemini_models(), get_file(), get_zip(), index(), diagnostics()

### Community 20 - "start.py"
Cohesion: 0.16
Nodes (10): main(), main(), cap(), current_section(), doc_map(), main(), milestone_id(), read() (+2 more)

### Community 21 - "extras.ts"
Cohesion: 0.14
Nodes (19): MODES, createExtras(), ExtrasCtx, K, load(), MockMode, NET_LABEL, networkLabel() (+11 more)

### Community 22 - "_job_age_ref"
Cohesion: 0.25
Nodes (4): get_job(), _job_age_ref(), _job_from_disk(), list_projects()

### Community 23 - "novoclip"
Cohesion: 0.22
Nodes (8): NOVOCLIP_WORKERS, build, environment, ports, restart, volumes, services, novoclip

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "BrandKit.tsx"
Cohesion: 0.17
Nodes (21): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+13 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "gen_map.py"
Cohesion: 0.17
Nodes (9): build_map(), Entry, fmt_tokens(), list_files(), markdown_sections(), render(), label(), scan() (+1 more)

### Community 29 - "guard_read.py"
Cohesion: 0.24
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "work"
Cohesion: 0.23
Nodes (9): _cleanup_partial(), work(), work(), work(), _edit_gate(), _worker(), progress(), begin_job() (+1 more)

### Community 31 - "process_live"
Cohesion: 0.10
Nodes (15): _add_nvidia_dll_dirs(), _encoder_test(), _fmt_clock(), hw_info(), _kill_tree(), process_live(), progress(), start_rec() (+7 more)

### Community 32 - "_job_dir"
Cohesion: 0.24
Nodes (5): clip_delete(), clip_meta(), _job_dir(), _no_cache_pages(), _refresh_result()

### Community 34 - "AGENTS.md"
Cohesion: 0.29
Nodes (5): Equipo de desarrollo, Mapa de documentos, Protocolo, Reglas de coste (siempre), Reglas de tokens y archivos

### Community 35 - "Status"
Cohesion: 0.40
Nodes (4): Notas de entorno, Preguntas abiertas para el dueÃ±o, Session log (newest first), Start here (sesiÃ³n local nueva)

### Community 37 - "NovoClip · frontend"
Cohesion: 0.40
Nodes (4): Cómo ejecutarlo, Datos simulados o reales, Estructura, NovoClip · frontend

### Community 38 - "mock-data.ts"
Cohesion: 0.17
Nodes (16): allJobs(), buildEvents(), ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs(), makeClips() (+8 more)

### Community 39 - "summarize"
Cohesion: 0.36
Nodes (7): clean(), _dash_summary(), _hash_summary(), _markdown_summary(), _python_summary(), _slash_summary(), summarize()

### Community 43 - "novoclip_signals.py"
Cohesion: 0.13
Nodes (7): audience_bonus(), overlap_ratio(), replay_intervals(), _valid_intervals(), AudienceBonusTests, OverlapRatioTests, ReplayIntervalsTests

### Community 44 - "Servidor de IA de NovoClip (IA incluida)"
Cohesion: 0.40
Nodes (4): Arrancarlo, En la app, Licencias, Servidor de IA de NovoClip (IA incluida)

### Community 48 - "opus-worker.md"
Cohesion: 0.40
Nodes (4): Antes de planificar, Coordinación y cierre, Entregable de arquitectura, Principios específicos

### Community 51 - "_live_source"
Cohesion: 0.09
Nodes (12): Cancelled, _cookie_methods(), _cookie_opts(), _cookie_opts_now(), _find_cookies_file(), _is_bot_check(), is_live_url(), _live_source() (+4 more)

### Community 54 - "optimize_clip"
Cohesion: 0.10
Nodes (17): fetch_captions(), _group_words(), _job_info(), _live_src(), load_clip_for_edit(), _local_video(), optimize_clip(), cut_text() (+9 more)

### Community 55 - "time.ts"
Cohesion: 0.11
Nodes (43): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+35 more)

### Community 56 - "test_clip_editing.py"
Cohesion: 0.08
Nodes (27): hook_of(), job(), mk_lines(), test_hook_cuts_at_question_and_prefers_strong_line(), test_hook_ignores_lines_after_25s(), test_hook_max_words_and_no_filler_edges(), test_hook_no_orphan_inverted_marks(), test_hook_single_word_not_empty_and_no_cta() (+19 more)

### Community 57 - "Equipo de desarrollo IA de ClipForge"
Cohesion: 0.29
Nodes (6): Equipo de desarrollo IA de ClipForge, Flujo recomendado, Política de modelos, Roles, Skills del proyecto, Skills externas opcionales para frontend

### Community 58 - "shutil"
Cohesion: 0.29
Nodes (3): cancel_job(), delete_job(), cancel_thread()

### Community 59 - "sonnet-reviewer.md"
Cohesion: 0.40
Nodes (4): Formato de salida, Revisión obligatoria, Riesgos específicos de vídeo, Riesgos específicos del frontend

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `Servidor de IA de NovoClip (IA incluida)`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12418300653594772 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.04971751412429379 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.09615384615384616 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `ProjectDetail.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.1292929292929293 - nodes in this community are weakly interconnected._