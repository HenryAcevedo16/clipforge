# Graph Report - clipforge  (2026-11-20)

## Corpus Check
- 94 files · ~85,097 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .bat 6, (none) 5, .example 1)

## Summary
- 1169 nodes · 2842 edges · 72 communities (52 shown, 20 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e61fe7c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- pipeline.py
- ai_backend
- Code map
- BrandKit.tsx
- HomeFlow.tsx
- NovoClip ✂️ — tu propia app de clipping
- Options
- Clip
- types.ts
- Api
- mock.ts
- _clip_task
- ClipCard.tsx
- optimize_clip
- ProjectDetail.tsx
- cn
- package.json
- hw_info
- start.py
- extras.ts
- test_reglas.py
- novoclip
- compilerOptions
- server.py
- brand.ts
- layout.tsx
- gen_map.py
- guard_read.py
- work
- _render_clip_once
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
- dependencies
- Path
- time.ts
- test_clip_editing.py
- Equipo de desarrollo IA de ClipForge
- create_job
- sonnet-reviewer.md
- next
- real.ts
- Settings.tsx
- scripts
- Cancelled
- @fontsource/big-shoulders-display@^5.3.0
- is_live_url
- _IgnoreWinReset
- guia_ia.md
- @fontsource-variable/manrope
- react-aria-components@^1.22.1

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 45 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 37 edges
5. `Api` - 34 edges
6. `process()` - 34 edges
7. `_render_clip_once()` - 32 edges
8. `optimize_clip()` - 32 edges
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
- `test_hook_options_max3_first_is_current_no_leftovers()` --calls--> `_hook_options()`  [EXTRACTED]
  tests/test_reglas.py → pipeline.py

## Import Cycles
- None detected.

## Communities (72 total, 20 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.11
Nodes (13): _anunciar_version(), api_version(), classic(), clip_for_edit(), diagnostics(), gemini_models(), get_file(), get_job() (+5 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (40): analyze_framing(), apply_zoom(), _ass_color(), _auto_keywords(), _best_hook(), _blur_bg(), build_ass(), _cam_panel() (+32 more)

### Community 2 - "ai_backend"
Cohesion: 0.09
Nodes (27): config(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key(), _ask_gemini() (+19 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "BrandKit.tsx"
Cohesion: 0.21
Nodes (26): Accounts(), NETWORKS, NetworkIcon(), blank(), BrandKit(), ColorField(), Group(), Soon() (+18 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.09
Nodes (30): Page(), PreviewOf(), ClipPreview(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS (+22 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.04
Nodes (46): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+38 more)

### Community 7 - "Options"
Cohesion: 0.08
Nodes (33): main(), ask_claude(), classify_video(), complete_endings(), describe_device(), download(), hook(), extend_to_sentence_end() (+25 more)

### Community 8 - "Clip"
Cohesion: 0.20
Nodes (6): align_clip(), Clip, _cut_clip(), _keep_clip_source(), _live_keep_source(), test_keep_clip_source_moves_file()

### Community 9 - "types.ts"
Cohesion: 0.12
Nodes (16): AiSource, BrandTemplate, ClipEdits, ClipReview, ClipToggles, DiagItem, EditWord, HardwareProfile (+8 more)

### Community 11 - "mock.ts"
Cohesion: 0.16
Nodes (15): addedIds(), config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K (+7 more)

### Community 12 - "_clip_task"
Cohesion: 0.13
Nodes (8): cancel_job(), clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), _no_cache_pages(), settings(), cancel_thread()

### Community 13 - "ClipCard.tsx"
Cohesion: 0.18
Nodes (17): ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO (+9 more)

### Community 14 - "optimize_clip"
Cohesion: 0.14
Nodes (18): optimize_clip(), cut_text(), run_copy(), run_verify(), env(), roles(), set_review(), test_cli_model_error_falls_back_to_sonnet() (+10 more)

### Community 15 - "ProjectDetail.tsx"
Cohesion: 0.24
Nodes (10): FILTERS, projectTitle(), STATE_META, SelectionNotice(), COLOR, Tone, api, ProjectState (+2 more)

### Community 16 - "cn"
Cohesion: 0.12
Nodes (22): FramingPreview(), HOME_STEPS, Stepper(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL (+14 more)

### Community 17 - "package.json"
Cohesion: 0.15
Nodes (18): devDependencies, postcss@^8.5.33, tailwindcss@^4.3.5, @tailwindcss/postcss@^4.3.5, @types/node@^26.6.6, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@^7.0.2 (+10 more)

### Community 19 - "hw_info"
Cohesion: 0.12
Nodes (6): _add_nvidia_dll_dirs(), diagnostics(), _encoder_test(), hw_info(), whispercpp_exe(), _windows_gpus()

### Community 20 - "start.py"
Cohesion: 0.18
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.18
Nodes (15): MODES, createExtras(), ExtrasCtx, K, load(), MockMode, NET_LABEL, networkLabel() (+7 more)

### Community 22 - "test_reglas.py"
Cohesion: 0.09
Nodes (30): apply_glossary(), load_rules(), pick(), run_tech(), _lines(), _norm(), read_glossary(), read_guide() (+22 more)

### Community 23 - "novoclip"
Cohesion: 0.22
Nodes (8): NOVOCLIP_WORKERS, build, environment, ports, restart, volumes, services, novoclip

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "brand.ts"
Cohesion: 0.22
Nodes (12): POS, PreviewProps, FontId, Network, SubtitleStyleId, WatermarkPosition, ASPECT_META, FONT_META (+4 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "gen_map.py"
Cohesion: 0.15
Nodes (10): build_map(), Entry, fmt_tokens(), list_files(), main(), markdown_sections(), render(), label() (+2 more)

### Community 29 - "guard_read.py"
Cohesion: 0.24
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "work"
Cohesion: 0.23
Nodes (9): _cleanup_partial(), work(), work(), work(), _edit_gate(), _worker(), progress(), begin_job() (+1 more)

### Community 31 - "_render_clip_once"
Cohesion: 0.11
Nodes (19): _avoid_box(), check_cancel(), _filter_path(), _ggml_model(), keep_intervals(), _kill_tree(), _pick_music(), player_track() (+11 more)

### Community 32 - "_job_dir"
Cohesion: 0.24
Nodes (6): clip_delete(), clip_meta(), _job_age_ref(), _job_dir(), _refresh_result(), delete_clip()

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
Cohesion: 0.11
Nodes (9): _cookie_methods(), _cookie_opts(), _cookie_opts_now(), fetch_captions(), _find_cookies_file(), _group_words(), _live_source(), parse_json3() (+1 more)

### Community 53 - "dependencies"
Cohesion: 0.11
Nodes (19): dependencies, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, lucide-react@^1.73.0, next@^16.4.6, react@^19.3.1 (+11 more)

### Community 54 - "Path"
Cohesion: 0.09
Nodes (18): _all_words(), _attach_replay_signals(), _clip_video_bytes(), _frames_b64(), _grab_jpeg(), _job_info(), _live_src(), load_clip_for_edit() (+10 more)

### Community 55 - "time.ts"
Cohesion: 0.11
Nodes (43): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+35 more)

### Community 56 - "test_clip_editing.py"
Cohesion: 0.15
Nodes (14): hook_of(), job(), mk_lines(), test_hook_cuts_at_question_and_prefers_strong_line(), test_hook_ignores_lines_after_25s(), test_hook_max_words_and_no_filler_edges(), test_hook_no_orphan_inverted_marks(), test_hook_single_word_not_empty_and_no_cta() (+6 more)

### Community 57 - "Equipo de desarrollo IA de ClipForge"
Cohesion: 0.29
Nodes (6): Equipo de desarrollo IA de ClipForge, Flujo recomendado, Política de modelos, Roles, Skills del proyecto, Skills externas opcionales para frontend

### Community 58 - "create_job"
Cohesion: 0.18
Nodes (7): create_job(), create_preview(), delete_job(), _opts(), purge_expired(), _purge_loop(), parse_ranges()

### Community 59 - "sonnet-reviewer.md"
Cohesion: 0.40
Nodes (4): Formato de salida, Revisión obligatoria, Riesgos específicos de vídeo, Riesgos específicos del frontend

### Community 60 - "next"
Cohesion: 0.14
Nodes (10): metadata, Page(), metadata, Page(), Inner(), Page(), metadata, Page() (+2 more)

### Community 61 - "real.ts"
Cohesion: 0.17
Nodes (9): guard(), extras, realApi, request(), ApiError, ClipEditData, Config, CreateJobInput (+1 more)

### Community 62 - "Settings.tsx"
Cohesion: 0.26
Nodes (10): metadata, Page(), AI_LABEL, AI_SUB, DIAG_ICON, Diagnostics(), Settings(), TIER (+2 more)

### Community 63 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, start, typecheck

### Community 65 - "@fontsource/big-shoulders-display@^5.3.0"
Cohesion: 0.33
Nodes (4): @fontsource/big-shoulders-display@^5.3.0, @internationalized/date@^3.12.4, @fontsource/big-shoulders-display, @internationalized/date

## Knowledge Gaps
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `Servidor de IA de NovoClip (IA incluida)`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11396011396011396 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0505175983436853 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.0931174089068826 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.08780487804878048 - nodes in this community are weakly interconnected._