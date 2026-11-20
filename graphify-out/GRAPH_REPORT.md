# Graph Report - clipforge  (2026-11-20)

## Corpus Check
- 94 files · ~85,276 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .bat 6, (none) 5, .example 1)

## Summary
- 1171 nodes · 2846 edges · 63 communities (46 shown, 17 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f7a01b95`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.py
- pipeline.py
- ai_backend
- Code map
- Accounts.tsx
- HomeFlow.tsx
- NovoClip ✂️ — tu propia app de clipping
- Options
- Path
- types.ts
- Api
- mock.ts
- create_job
- select_heuristic
- ask_claude
- ProjectDetail.tsx
- ClipEditor.tsx
- package.json
- _job_age_ref
- start.py
- extras.ts
- test_reglas.py
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
- label
- PROVENANCE.md
- iniciar_mac_linux.sh
- opus-worker.md
- _live_source
- snap_to_silence
- optimize_clip
- time.ts
- test_clip_editing.py
- Equipo de desarrollo IA de ClipForge
- shutil
- sonnet-reviewer.md
- Cancelled
- guia_ia.md

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 45 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 37 edges
5. `process()` - 34 edges
6. `Api` - 34 edges
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
- `test_rerender_inside_saved_piece_does_not_download()` --calls--> `rerender_clip()`  [EXTRACTED]
  tests/test_clip_editing.py → pipeline.py

## Import Cycles
- None detected.

## Communities (63 total, 17 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.12
Nodes (10): _anunciar_version(), api_version(), classic(), clip_for_edit(), gemini_models(), get_file(), get_zip(), _IgnoreWinReset (+2 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (35): analyze_framing(), apply_zoom(), _ass_color(), _attach_replay_signals(), _avoid_box(), _blur_bg(), build_ass(), _cam_panel() (+27 more)

### Community 2 - "ai_backend"
Cohesion: 0.07
Nodes (30): config(), diagnostics(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status() (+22 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "Accounts.tsx"
Cohesion: 0.19
Nodes (16): metadata, Page(), metadata, Page(), Accounts(), NETWORKS, NetworkIcon(), ProjectsList() (+8 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.10
Nodes (32): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), ResultStep() (+24 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.04
Nodes (46): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+38 more)

### Community 7 - "Options"
Cohesion: 0.14
Nodes (23): main(), check_cancel(), classify_video(), describe_device(), download(), hook(), _ggml_model(), low_res_warning() (+15 more)

### Community 8 - "Path"
Cohesion: 0.12
Nodes (17): _all_words(), Clip, _clip_video_bytes(), _cut_clip(), _filter_path(), _frames_b64(), _grab_jpeg(), _keep_clip_source() (+9 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (22): guard(), extras, realApi, request(), AiSource, ApiError, ClipEditData, ClipEdits (+14 more)

### Community 11 - "mock.ts"
Cohesion: 0.13
Nodes (18): MODES, MockMode, USE_MOCK, config, SeedJob, Ev, extras, failIfModeError() (+10 more)

### Community 12 - "create_job"
Cohesion: 0.20
Nodes (9): clip_optimize(), clip_rerender(), clip_revert(), _clip_task(), create_job(), create_preview(), _opts(), purge_expired() (+1 more)

### Community 13 - "select_heuristic"
Cohesion: 0.10
Nodes (17): align_clip(), _auto_keywords(), _best_hook(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), manual_clips() (+9 more)

### Community 14 - "ask_claude"
Cohesion: 0.16
Nodes (10): ask_claude(), _ask_proxy(), _extract_json(), _included_cfg(), run_tech(), run_verify(), _proxy_url(), _role_models() (+2 more)

### Community 15 - "ProjectDetail.tsx"
Cohesion: 0.12
Nodes (30): Inner(), Page(), RecentProjects(), Ring(), SR, StageList(), ProjectDetail(), FILTERS (+22 more)

### Community 16 - "ClipEditor.tsx"
Cohesion: 0.09
Nodes (36): metadata, Page(), FramingPreview(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL (+28 more)

### Community 17 - "package.json"
Cohesion: 0.05
Nodes (50): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @fontsource-variable/manrope@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, @internationalized/date@^3.12.4 (+42 more)

### Community 19 - "_job_age_ref"
Cohesion: 0.25
Nodes (4): get_job(), _job_age_ref(), _job_from_disk(), list_projects()

### Community 20 - "start.py"
Cohesion: 0.23
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.14
Nodes (19): createExtras(), ExtrasCtx, K, load(), NET_LABEL, networkLabel(), seedAccounts(), seedPosts() (+11 more)

### Community 22 - "test_reglas.py"
Cohesion: 0.08
Nodes (32): apply_glossary(), _hook_options(), load_rules(), pick(), _lines(), _norm(), read_glossary(), read_guide() (+24 more)

### Community 23 - "novoclip"
Cohesion: 0.22
Nodes (8): NOVOCLIP_WORKERS, build, environment, ports, restart, volumes, services, novoclip

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.17
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "BrandKit.tsx"
Cohesion: 0.16
Nodes (22): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+14 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "gen_map.py"
Cohesion: 0.21
Nodes (6): build_map(), Entry, list_files(), markdown_sections(), render(), scan()

### Community 29 - "guard_read.py"
Cohesion: 0.19
Nodes (4): decide(), line_count(), main(), main()

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
Cohesion: 0.29
Nodes (8): clean(), _dash_summary(), _hash_summary(), _manifest_summary(), _markdown_summary(), _python_summary(), _slash_summary(), summarize()

### Community 43 - "novoclip_signals.py"
Cohesion: 0.13
Nodes (7): audience_bonus(), overlap_ratio(), replay_intervals(), _valid_intervals(), AudienceBonusTests, OverlapRatioTests, ReplayIntervalsTests

### Community 44 - "label"
Cohesion: 0.40
Nodes (3): fmt_tokens(), label(), size_label()

### Community 48 - "opus-worker.md"
Cohesion: 0.40
Nodes (4): Antes de planificar, Coordinación y cierre, Entregable de arquitectura, Principios específicos

### Community 51 - "_live_source"
Cohesion: 0.09
Nodes (11): _cookie_methods(), _cookie_opts(), _cookie_opts_now(), fetch_captions(), _find_cookies_file(), _group_words(), is_live_url(), _live_source() (+3 more)

### Community 54 - "optimize_clip"
Cohesion: 0.14
Nodes (13): _job_info(), _live_src(), load_clip_for_edit(), _local_video(), norm_provider(), optimize_clip(), cut_text(), run_copy() (+5 more)

### Community 55 - "time.ts"
Cohesion: 0.12
Nodes (40): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+32 more)

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
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11594202898550725 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.047593865679534636 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.07030527289546716 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `HomeFlow.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.09990749306197964 - nodes in this community are weakly interconnected._