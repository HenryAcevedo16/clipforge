# Graph Report - clipforge  (2026-11-18)

## Corpus Check
- 84 files · ~74,950 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .bat 5, (none) 3, .example 1)

## Summary
- 990 nodes · 2491 edges · 60 communities (41 shown, 19 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cb40c55d`
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
- Options
- _render_clip_once
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
- ProjectDetail.tsx
- start.py
- extras.ts
- package.json
- dependencies
- compilerOptions
- server.py
- ClipEditor.tsx
- layout.tsx
- Clip
- guard_read.py
- _worker
- process_live
- summarize
- TwitchChat
- AGENTS.md
- Status
- _QuietLog
- NovoClip · frontend
- mock-data.ts
- brand.ts
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- hw_info
- scripts
- PROVENANCE.md
- iniciar_mac_linux.sh
- fetch_captions
- label
- @fontsource/big-shoulders-display@^5.3.0
- @fontsource-variable/manrope
- react-aria-components@^1.22.1

## God Nodes (most connected - your core abstractions)
1. `Code map` - 51 edges
2. `cn()` - 49 edges
3. `Options` - 36 edges
4. `NovoClip ✂️ — tu propia app de clipping` - 36 edges
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

## Communities (60 total, 19 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.05
Nodes (31): _anunciar_version(), api_version(), cancel_job(), classic(), clip_delete(), clip_for_edit(), clip_meta(), clip_optimize() (+23 more)

### Community 1 - "pipeline.py"
Cohesion: 0.06
Nodes (25): analyze_framing(), _ass_color(), build_ass(), Cancelled, _clean_word(), _cluster_people(), _cpu_name(), _detect_faces() (+17 more)

### Community 2 - "ai_backend"
Cohesion: 0.07
Nodes (32): config(), diagnostics(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status() (+24 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (52): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+44 more)

### Community 4 - "ProjectsList.tsx"
Cohesion: 0.19
Nodes (18): metadata, Page(), RecentProjects(), Ring(), FILTERS, projectTitle(), STATE_META, expiryText() (+10 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.18
Nodes (18): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), Settings (+10 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (41): Actualizar en Windows, Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, 🎯 Clips que terminan la idea, Consejos, Conversaciones y podcasts (nuevo) (+33 more)

### Community 7 - "Options"
Cohesion: 0.16
Nodes (19): check_cancel(), describe_device(), download(), hook(), _ggml_model(), low_res_warning(), preview_framing(), probe() (+11 more)

### Community 8 - "_render_clip_once"
Cohesion: 0.10
Nodes (18): apply_zoom(), _avoid_box(), _blur_bg(), _cam_panel(), draw_progress(), keep_intervals(), _kill_tree(), player_track() (+10 more)

### Community 9 - "types.ts"
Cohesion: 0.10
Nodes (19): extras, realApi, request(), ClipEditData, ClipEdits, ClipReview, ClipToggles, Config (+11 more)

### Community 11 - "mock.ts"
Cohesion: 0.17
Nodes (14): config, SeedJob, Ev, extras, failIfModeError(), getMockMode(), K, latency() (+6 more)

### Community 12 - "Path"
Cohesion: 0.10
Nodes (19): _all_words(), delete_clip(), _filter_path(), _group_words(), _job_info(), load_clip_for_edit(), _local_video(), norm_provider() (+11 more)

### Community 13 - "cn"
Cohesion: 0.13
Nodes (25): ResultStep(), ResultThumb(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel(), TIPO (+17 more)

### Community 14 - "ask_claude"
Cohesion: 0.11
Nodes (20): ask_claude(), _auto_keywords(), classify_video(), complete_endings(), extend_to_sentence_end(), _grab_jpeg(), _line_energy(), _line_features() (+12 more)

### Community 15 - "Accounts.tsx"
Cohesion: 0.15
Nodes (20): metadata, Page(), metadata, Page(), Accounts(), NETWORKS, NetworkIcon(), AI_LABEL (+12 more)

### Community 16 - "BrandKit.tsx"
Cohesion: 0.18
Nodes (20): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+12 more)

### Community 17 - "CalendarView.tsx"
Cohesion: 0.12
Nodes (41): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+33 more)

### Community 18 - "gen_map.py"
Cohesion: 0.21
Nodes (6): build_map(), Entry, list_files(), markdown_sections(), render(), scan()

### Community 19 - "ProjectDetail.tsx"
Cohesion: 0.17
Nodes (15): Inner(), Page(), ProjectDetail(), SelectionNotice(), PlatformIcon(), PlatformPill(), detectPlatform(), LinkKind (+7 more)

### Community 20 - "start.py"
Cohesion: 0.22
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.12
Nodes (22): MODES, createExtras(), ExtrasCtx, guard(), K, load(), MockMode, NET_LABEL (+14 more)

### Community 22 - "package.json"
Cohesion: 0.15
Nodes (18): devDependencies, postcss@^8.5.33, tailwindcss@^4.3.5, @tailwindcss/postcss@^4.3.5, @types/node@^26.6.6, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@^7.0.2 (+10 more)

### Community 23 - "dependencies"
Cohesion: 0.11
Nodes (19): dependencies, @fontsource-variable/bricolage-grotesque@^5.3.0, @fontsource-variable/figtree@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, lucide-react@^1.73.0, next@^16.4.6, react@^19.3.1 (+11 more)

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.17
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "ClipEditor.tsx"
Cohesion: 0.20
Nodes (12): FramingPreview(), ClipEditor(), LAYOUTS, norm(), sec(), STYLE_LABEL, TOGGLE_DEFAULTS, TOGGLE_LABELS (+4 more)

### Community 27 - "layout.tsx"
Cohesion: 0.24
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), NAV, LogoMark(), MockSwitcher() (+1 more)

### Community 28 - "Clip"
Cohesion: 0.18
Nodes (6): align_clip(), Clip, _clip_video_bytes(), _cut_clip(), _frames_b64(), review_clip()

### Community 29 - "guard_read.py"
Cohesion: 0.19
Nodes (4): decide(), line_count(), main(), main()

### Community 30 - "_worker"
Cohesion: 0.30
Nodes (8): _cleanup_partial(), work(), work(), work(), _worker(), progress(), begin_job(), end_job()

### Community 31 - "process_live"
Cohesion: 0.11
Nodes (10): main(), _fmt_clock(), is_live_url(), _live_source(), platform_of(), process_live(), progress(), start_rec() (+2 more)

### Community 32 - "summarize"
Cohesion: 0.32
Nodes (8): clean(), _dash_summary(), _hash_summary(), _manifest_summary(), _markdown_summary(), _python_summary(), _slash_summary(), summarize()

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
Cohesion: 0.18
Nodes (15): allJobs(), buildEvents(), ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs(), makeClips() (+7 more)

### Community 39 - "brand.ts"
Cohesion: 0.22
Nodes (12): POS, PreviewProps, FontId, Network, SubtitleStyleId, WatermarkPosition, ASPECT_META, FONT_META (+4 more)

### Community 43 - "hw_info"
Cohesion: 0.18
Nodes (5): _add_nvidia_dll_dirs(), _encoder_test(), hw_info(), video_encoder(), _windows_gpus()

### Community 44 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, start, typecheck

### Community 52 - "label"
Cohesion: 0.40
Nodes (3): fmt_tokens(), label(), size_label()

### Community 53 - "@fontsource/big-shoulders-display@^5.3.0"
Cohesion: 0.33
Nodes (4): @fontsource/big-shoulders-display@^5.3.0, @internationalized/date@^3.12.4, @fontsource/big-shoulders-display, @internationalized/date

## Knowledge Gaps
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05285592497868713 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06183574879227053 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.0653061224489796 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.038461538461538464 - nodes in this community are weakly interconnected._
- **Should `NovoClip ✂️ — tu propia app de clipping` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._