# Graph Report - clipforge  (2026-11-19)

## Corpus Check
- 87 files · ~77,757 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .bat 6, (none) 5, .example 1)

## Summary
- 1039 nodes · 2561 edges · 61 communities (48 shown, 13 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d460281a`
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
- Path
- types.ts
- Api
- mock.ts
- create_job
- ClipCard.tsx
- Options
- ClipEditor.tsx
- Cancelled
- CalendarView.tsx
- get
- BrandKit.tsx
- start.py
- extras.ts
- package.json
- novoclip
- compilerOptions
- server.py
- ClipEditor.tsx
- layout.tsx
- gen_map.py
- guard_read.py
- work
- _sp_run
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
- Settings.tsx
- brand.ts
- PROVENANCE.md
- iniciar_mac_linux.sh
- opus-worker.md
- _live_source
- post
- _job_age_ref
- get
- PlatformPill.tsx
- Equipo de desarrollo IA de ClipForge
- system_profile
- sonnet-reviewer.md
- Servidor de IA de NovoClip (IA incluida)

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

## Communities (61 total, 13 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.14
Nodes (4): _anunciar_version(), api_version(), _IgnoreWinReset, _version()

### Community 1 - "pipeline.py"
Cohesion: 0.07
Nodes (29): analyze_framing(), apply_zoom(), _ass_color(), _avoid_box(), _blur_bg(), build_ass(), _cam_panel(), _clean_word() (+21 more)

### Community 2 - "ai_backend"
Cohesion: 0.09
Nodes (30): config(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key(), ask_claude() (+22 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.14
Nodes (30): metadata, Page(), Inner(), Page(), metadata, Page(), Accounts(), NetworkIcon() (+22 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.12
Nodes (20): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), Settings (+12 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (43): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, Clips de directo editables, 🎯 Clips que terminan la idea, Consejos (+35 more)

### Community 7 - "Options"
Cohesion: 0.11
Nodes (26): check_cancel(), classify_video(), _cookie_methods(), describe_device(), download(), hook(), _ggml_model(), low_res_warning() (+18 more)

### Community 8 - "Path"
Cohesion: 0.09
Nodes (22): _all_words(), Clip, _clip_video_bytes(), _cut_clip(), delete_clip(), _frames_b64(), _group_words(), _job_info() (+14 more)

### Community 9 - "types.ts"
Cohesion: 0.09
Nodes (23): guard(), extras, realApi, request(), AiSource, ApiError, ClipEditData, ClipEdits (+15 more)

### Community 11 - "mock.ts"
Cohesion: 0.17
Nodes (14): config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K, latency() (+6 more)

### Community 12 - "create_job"
Cohesion: 0.16
Nodes (8): _clip_task(), create_job(), create_preview(), delete_job(), _opts(), purge_expired(), _purge_loop(), is_live_url()

### Community 13 - "ClipCard.tsx"
Cohesion: 0.25
Nodes (10): ResultStep(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO, ScoreDial() (+2 more)

### Community 14 - "Options"
Cohesion: 0.10
Nodes (17): align_clip(), _auto_keywords(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips() (+9 more)

### Community 15 - "ClipEditor.tsx"
Cohesion: 0.18
Nodes (12): ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS, TOGGLE_LABELS, Tool (+4 more)

### Community 17 - "CalendarView.tsx"
Cohesion: 0.11
Nodes (44): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+36 more)

### Community 18 - "get"
Cohesion: 0.14
Nodes (8): classic(), clip_for_edit(), diagnostics(), gemini_models(), get_file(), get_zip(), index(), diagnostics()

### Community 19 - "BrandKit.tsx"
Cohesion: 0.27
Nodes (14): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+6 more)

### Community 20 - "start.py"
Cohesion: 0.17
Nodes (9): main(), cap(), current_section(), doc_map(), main(), milestone_id(), read(), render() (+1 more)

### Community 21 - "extras.ts"
Cohesion: 0.18
Nodes (15): createExtras(), ExtrasCtx, K, load(), NET_LABEL, networkLabel(), seedAccounts(), seedTemplates() (+7 more)

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
Nodes (20): NETWORKS, FramingPreview(), ResultThumb(), clipText(), Net, NETS, PublishDialog(), svg (+12 more)

### Community 27 - "layout.tsx"
Cohesion: 0.26
Nodes (8): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), ToastProvider()

### Community 28 - "gen_map.py"
Cohesion: 0.15
Nodes (15): build_map(), clean(), _dash_summary(), Entry, _hash_summary(), list_files(), main(), _manifest_summary() (+7 more)

### Community 29 - "guard_read.py"
Cohesion: 0.27
Nodes (3): decide(), line_count(), main()

### Community 30 - "work"
Cohesion: 0.23
Nodes (9): _cleanup_partial(), work(), work(), work(), _edit_gate(), _worker(), progress(), begin_job() (+1 more)

### Community 31 - "_sp_run"
Cohesion: 0.10
Nodes (16): _add_nvidia_dll_dirs(), _encoder_test(), _fmt_clock(), hw_info(), _kill_tree(), _live_keep_source(), process_live(), progress() (+8 more)

### Community 32 - "_job_dir"
Cohesion: 0.24
Nodes (6): clip_delete(), clip_meta(), clip_rerender(), _job_dir(), _no_cache_pages(), _refresh_result()

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
Cohesion: 0.16
Nodes (17): seedPosts(), allJobs(), buildEvents(), ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs() (+9 more)

### Community 39 - "label"
Cohesion: 0.40
Nodes (3): fmt_tokens(), label(), size_label()

### Community 43 - "Settings.tsx"
Cohesion: 0.23
Nodes (11): metadata, Page(), AI_LABEL, AI_SUB, DIAG_ICON, Diagnostics(), Settings(), TIER (+3 more)

### Community 44 - "brand.ts"
Cohesion: 0.29
Nodes (10): POS, PreviewProps, FontId, SubtitleStyleId, WatermarkPosition, ASPECT_META, FONT_META, FONT_ORDER (+2 more)

### Community 48 - "opus-worker.md"
Cohesion: 0.40
Nodes (4): Antes de planificar, Coordinación y cierre, Entregable de arquitectura, Principios específicos

### Community 51 - "_live_source"
Cohesion: 0.12
Nodes (8): _cookie_opts(), _cookie_opts_now(), fetch_captions(), _find_cookies_file(), _live_source(), parse_json3(), platform_of(), _tiktok_live_api()

### Community 52 - "post"
Cohesion: 0.22
Nodes (5): cancel_job(), clip_optimize(), clip_revert(), settings(), cancel_thread()

### Community 53 - "_job_age_ref"
Cohesion: 0.25
Nodes (4): get_job(), _job_age_ref(), _job_from_disk(), list_projects()

### Community 54 - "get"
Cohesion: 0.40
Nodes (5): MockSwitcher(), MODES, MockMode, USE_MOCK, writeString()

### Community 55 - "PlatformPill.tsx"
Cohesion: 0.31
Nodes (7): PlatformIcon(), PlatformPill(), LinkKind, PLATFORM_META, PlatformId, PlatformInfo, SUPPORTED_TEXT

### Community 57 - "Equipo de desarrollo IA de ClipForge"
Cohesion: 0.29
Nodes (6): Equipo de desarrollo IA de ClipForge, Flujo recomendado, Política de modelos, Roles, Skills del proyecto, Skills externas opcionales para frontend

### Community 58 - "system_profile"
Cohesion: 0.33
Nodes (5): _cpu_name(), _ps(), _ram_gb(), system_profile(), _vram_gb()

### Community 59 - "sonnet-reviewer.md"
Cohesion: 0.40
Nodes (4): Formato de salida, Revisión obligatoria, Riesgos específicos de vídeo, Riesgos específicos del frontend

### Community 60 - "Servidor de IA de NovoClip (IA incluida)"
Cohesion: 0.40
Nodes (4): Arrancarlo, En la app, Licencias, Servidor de IA de NovoClip (IA incluida)

## Knowledge Gaps
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `Servidor de IA de NovoClip (IA incluida)`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._
- **Why does `Api` connect `Api` to `types.ts`, `mock.ts`, `ClipEditor.tsx`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06636500754147813 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.08562367864693446 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `ProjectDetail.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.13658536585365855 - nodes in this community are weakly interconnected._