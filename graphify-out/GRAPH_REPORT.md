# Graph Report - clipforge  (2026-11-18)

## Corpus Check
- 84 files · ~74,305 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .bat 4, (none) 3, .example 1)

## Summary
- 977 nodes · 2478 edges · 51 communities (37 shown, 14 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `59b07262`
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
- CalendarView.tsx
- BrandKit.tsx
- time.ts
- gen_map.py
- ProjectsList.tsx
- start.py
- extras.ts
- package.json
- dependencies
- compilerOptions
- server.py
- react
- layout.tsx
- Clip
- guard_read.py
- index.ts
- _live_source
- summarize
- TwitchChat
- AGENTS.md
- Status
- _QuietLog
- NovoClip · frontend
- scripts
- @fontsource-variable/bricolage-grotesque@^5.3.0
- CLAUDE.md
- frontend/AGENTS.md
- fonts.d.ts
- next.config.ts
- @react-aria/ssr@^3.10.1
- PROVENANCE.md
- iniciar_mac_linux.sh

## God Nodes (most connected - your core abstractions)
1. `Code map` - 50 edges
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
- `_worker()` --uses--> `Options`  [INFERRED]
  app.py → pipeline.py
- `_worker()` --calls--> `process()`  [EXTRACTED]
  app.py → pipeline.py

## Import Cycles
- None detected.

## Communities (51 total, 14 thin omitted)

### Community 0 - "app.py"
Cohesion: 0.05
Nodes (37): cancel_job(), classic(), _cleanup_partial(), clip_delete(), clip_for_edit(), clip_meta(), clip_optimize(), clip_rerender() (+29 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (36): analyze_framing(), apply_zoom(), _ass_color(), _avoid_box(), _blur_bg(), build_ass(), _cam_panel(), Cancelled (+28 more)

### Community 2 - "ai_backend"
Cohesion: 0.07
Nodes (33): config(), settings(), ai_backend(), ai_mode(), _ai_note(), ai_source(), ai_sources_status(), anthropic_key() (+25 more)

### Community 3 - "Code map"
Cohesion: 0.04
Nodes (51): ./, .claude/, .claude/agents/, .claude/hooks/, .claude/skills/model-router/, .claude/skills/model-router/references/, .claude/skills/model-router/scripts/, .claude/skills/token-optimization/ (+43 more)

### Community 4 - "ProjectDetail.tsx"
Cohesion: 0.14
Nodes (31): metadata, Page(), metadata, Page(), Inner(), Page(), Accounts(), NETWORKS (+23 more)

### Community 5 - "HomeFlow.tsx"
Cohesion: 0.10
Nodes (33): Page(), AI_NAMES, DEFAULTS, fmtTime(), HomeFlow(), LAYOUT_OPTIONS, parseTime(), ResultStep() (+25 more)

### Community 6 - "NovoClip ✂️ — tu propia app de clipping"
Cohesion: 0.05
Nodes (38): Ajuste automático según el equipo (nuevo), Archivos, 📷 Calidad de la webcam del streamer, 🎯 Clips con más sentido y notas más justas, 🎯 Clips que terminan la idea, Consejos, Conversaciones y podcasts (nuevo), Desarrollo con Claude Code: skill de ahorro de tokens (+30 more)

### Community 7 - "Options"
Cohesion: 0.13
Nodes (24): check_cancel(), describe_device(), download(), hook(), fetch_captions(), _ggml_model(), low_res_warning(), Options (+16 more)

### Community 8 - "process_live"
Cohesion: 0.08
Nodes (19): main(), _add_nvidia_dll_dirs(), cancel_thread(), _clip_video_bytes(), _encoder_test(), _fmt_clock(), _frames_b64(), hw_info() (+11 more)

### Community 9 - "types.ts"
Cohesion: 0.08
Nodes (25): FILTERS, guard(), failIfModeError(), extras, request(), ApiError, ClipEditData, ClipEdits (+17 more)

### Community 11 - "mock.ts"
Cohesion: 0.13
Nodes (23): allJobs(), buildEvents(), config, ASSET_KEYS, assetFor(), CLIP_POOL, ClipSeed, extremeJobs() (+15 more)

### Community 12 - "Path"
Cohesion: 0.12
Nodes (16): classify_video(), _grab_jpeg(), _group_words(), _job_info(), load_clip_for_edit(), _local_video(), locate_player(), norm_provider() (+8 more)

### Community 13 - "cn"
Cohesion: 0.16
Nodes (21): ResultThumb(), HOME_STEPS, Stepper(), ClipCard(), clipText(), GRAV, isReview(), ReviewPanel() (+13 more)

### Community 14 - "ask_claude"
Cohesion: 0.12
Nodes (17): ask_claude(), _auto_keywords(), complete_endings(), extend_to_sentence_end(), _line_energy(), _line_features(), _loudness_curve(), manual_clips() (+9 more)

### Community 15 - "CalendarView.tsx"
Cohesion: 0.15
Nodes (23): metadata, Page(), NetworkChip(), CalendarView(), cap(), Cursor, dayLabel(), Dots() (+15 more)

### Community 16 - "BrandKit.tsx"
Cohesion: 0.18
Nodes (20): metadata, Page(), blank(), BrandKit(), ColorField(), Group(), PreviewOf(), Soon() (+12 more)

### Community 17 - "time.ts"
Cohesion: 0.17
Nodes (21): ScheduledPost, addDays(), Day, dowMon(), groupByDay(), inputsFromIso(), keyOf(), mk() (+13 more)

### Community 18 - "gen_map.py"
Cohesion: 0.15
Nodes (10): build_map(), Entry, fmt_tokens(), list_files(), main(), markdown_sections(), render(), label() (+2 more)

### Community 19 - "ProjectsList.tsx"
Cohesion: 0.21
Nodes (16): metadata, Page(), Ring(), SR, StageList(), projectTitle(), STATE_META, expiryText() (+8 more)

### Community 20 - "start.py"
Cohesion: 0.18
Nodes (8): cap(), current_section(), doc_map(), main(), milestone_id(), read(), render(), section()

### Community 21 - "extras.ts"
Cohesion: 0.17
Nodes (17): createExtras(), ExtrasCtx, K, load(), NET_LABEL, seedAccounts(), seedPosts(), seedTemplates() (+9 more)

### Community 22 - "package.json"
Cohesion: 0.15
Nodes (18): devDependencies, postcss@^8.5.33, tailwindcss@^4.3.5, @tailwindcss/postcss@^4.3.5, @types/node@^26.6.6, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@^7.0.2 (+10 more)

### Community 23 - "dependencies"
Cohesion: 0.11
Nodes (19): dependencies, @fontsource/big-shoulders-display@^5.3.0, @fontsource-variable/figtree@^5.3.0, @heroui/react@^3.2.7, @heroui/styles@^3.2.7, lucide-react@^1.73.0, next@^16.4.6, react@^19.3.1 (+11 more)

### Community 24 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 25 - "server.py"
Cohesion: 0.18
Nodes (7): ai(), AIRequest, _db(), Img, _license(), license_status(), _used_today()

### Community 26 - "react"
Cohesion: 0.17
Nodes (13): FramingPreview(), clipText(), Net, NETS, svg, COLOR, Tone, Dialog() (+5 more)

### Community 27 - "layout.tsx"
Cohesion: 0.20
Nodes (9): metadata, RootLayout(), viewport, AppShell(), isActive(), LogoMark(), ToastProvider(), @fontsource-variable/manrope@^5.3.0 (+1 more)

### Community 28 - "Clip"
Cohesion: 0.20
Nodes (6): align_clip(), _all_words(), Clip, _cut_clip(), review_clip(), save_clip_words()

### Community 29 - "guard_read.py"
Cohesion: 0.24
Nodes (4): decide(), line_count(), main(), _manifest_summary()

### Community 30 - "index.ts"
Cohesion: 0.27
Nodes (9): MockSwitcher(), MODES, MockMode, networkLabel(), USE_MOCK, getMockMode(), mockApi, realApi (+1 more)

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

### Community 38 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, start, typecheck

### Community 39 - "@fontsource-variable/bricolage-grotesque@^5.3.0"
Cohesion: 0.33
Nodes (4): @fontsource-variable/bricolage-grotesque@^5.3.0, @internationalized/date@^3.12.4, @fontsource-variable/bricolage-grotesque, @internationalized/date

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `gemini_key()` connect `ai_backend` to `pipeline.py`, `NovoClip ✂️ — tu propia app de clipping`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052982456140350874 - nodes in this community are weakly interconnected._
- **Why does `IA incluida o clave propia (nuevo)` connect `NovoClip ✂️ — tu propia app de clipping` to `ai_backend`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052083333333333336 - nodes in this community are weakly interconnected._
- **Should `ai_backend` be split into smaller, more focused modules?**
  _Cohesion score 0.06509803921568627 - nodes in this community are weakly interconnected._
- **Should `Code map` be split into smaller, more focused modules?**
  _Cohesion score 0.0392156862745098 - nodes in this community are weakly interconnected._
- **Should `ProjectDetail.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._