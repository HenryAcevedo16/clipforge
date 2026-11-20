"""Optimizar con IA repartido: Sonnet (corte) -> Haiku (textos) -> Opus (verifica). ask_claude se simula."""
import json
import subprocess
from types import SimpleNamespace

import pytest

import pipeline


def words_for(n=120):
    return [{"w": f"p{i}", "s": 100 + i * 0.5, "e": 100 + i * 0.5 + 0.4} for i in range(n)]


@pytest.fixture
def env(tmp_path, monkeypatch):
    wd = tmp_path / "job"
    for d in ("edit", "clips"):
        (wd / d).mkdir(parents=True)
    json.dump(words_for(), (wd / "edit" / "01.json").open("w"))
    clip = {"index": 1, "start": 110.0, "end": 140.0, "title": "t", "hook": "H", "score": 50, "reason": "r", "caption": "c",
            "hashtags": ["#a"], "file": "01_t.mp4", "thumb": "", "review": {}, "duration": 30, "keywords": ["p1"]}
    (wd / "result.json").write_text(json.dumps({"title": "T", "language": "es", "source": {}, "clips": [clip]}))
    (wd / "job.json").write_text(json.dumps({"source": "https://youtube.com/watch?v=x", "opts": {}}))
    calls = []
    script = {"verify": [], "tech": None, "copy": None}

    def fake_ask(prompt, schema, opts, images=None, videos=None, role=None):
        calls.append((role, schema.__name__, prompt))
        if role == "tech":
            r = script["tech"] or dict(start_word=20, end_word=79, keywords=["p21"], layout="", cambios=["ajusté"], no_resuelto=[])
            return schema(**r)
        if role == "copy":
            return schema(**(script["copy"] or dict(title="Título nuevo", hook="Gancho nuevo", caption="¿Qué opinas?", hashtags=["x", "#y"])))
        v = script["verify"].pop(0) if script["verify"] else dict(ok=True)
        return schema(**v)

    monkeypatch.setattr(pipeline, "ask_claude", fake_ask)
    monkeypatch.setattr(pipeline, "ai_backend", lambda: "cli")
    monkeypatch.setattr(pipeline, "rerender_clip", lambda wd_, i, edits, prog=None: calls.append(("render", None, edits)))
    monkeypatch.setattr(pipeline, "update_clip_meta", lambda wd_, i, new: calls.append(("meta", None, new)))
    monkeypatch.setattr(pipeline, "review_clip", lambda *a, **k: {"nota": 80})
    return wd, calls, script


def roles(calls):
    return [r for r, _, _ in calls if r in ("tech", "copy", "verify")]


def set_review(wd, problems):
    res = json.loads((wd / "result.json").read_text())
    res["clips"][0]["review"] = {"nota": 40, "resumen": "x", "problemas": problems, "sugerencias": []}
    (wd / "result.json").write_text(json.dumps(res))


def test_no_technical_problems_skips_sonnet(env):
    wd, calls, _ = env
    set_review(wd, [{"tipo": "subtitulos", "gravedad": "baja", "detalle": "tapan algo"}])
    out = pipeline.optimize_clip(wd, 1)
    assert roles(calls) == ["copy", "verify"]
    assert any("subtitulos" in x for x in (out.get("opt_pending") or []))
    meta_or_render = [c for c in calls if c[0] in ("meta", "render")][0][2]
    assert (meta_or_render["start"], meta_or_render["end"]) == (110.0, 140.0)    # corte intacto


def test_happy_path_order_and_one_call_each(env):
    wd, calls, _ = env
    out = pipeline.optimize_clip(wd, 1)
    assert roles(calls) == ["tech", "copy", "verify"]
    assert out["optimized"] and any("Opus verificó" in n for n in out["opt_note"])
    assert out["opt_prev"]["title"] == "t"        # Deshacer sigue guardando lo anterior


def test_verify_fix_copy_repeats_only_haiku(env):
    wd, calls, script = env
    script["verify"] = [dict(ok=False, fix="copy", motivo="el gancho no tiene sentido"), dict(ok=True)]
    pipeline.optimize_clip(wd, 1)
    assert roles(calls) == ["tech", "copy", "verify", "copy", "verify"]
    assert "el gancho no tiene sentido" in [p for r, _, p in calls if r == "copy"][-1]


def test_two_rejections_opus_twice_and_pending(env):
    wd, calls, script = env
    script["verify"] = [dict(ok=False, fix="both", motivo="mal 1"), dict(ok=False, fix="both", motivo="mal 2")]
    out = pipeline.optimize_clip(wd, 1)
    assert roles(calls).count("verify") == 2
    assert any("mal 2" in x for x in out["opt_pending"])


def test_invalid_cut_keeps_original_and_does_not_call_opus_for_it(env):
    wd, calls, script = env
    script["tech"] = dict(start_word=0, end_word=2, keywords=[], layout="", cambios=["x"], no_resuelto=[])   # 1 s: fuera de [lo, hi]
    pipeline.optimize_clip(wd, 1)
    assert roles(calls).count("tech") == 2                         # un segundo intento
    payload = [c for c in calls if c[0] in ("meta", "render")][0][2]
    assert (payload["start"], payload["end"]) == (110.0, 140.0)     # se mantiene el corte original


def test_gemini_backend_ignores_roles_and_skips_verify(env, monkeypatch):
    wd, calls, _ = env
    monkeypatch.setattr(pipeline, "ai_backend", lambda: "gemini")
    pipeline.optimize_clip(wd, 1)
    assert "verify" not in roles(calls)


def test_cli_model_error_falls_back_to_sonnet(monkeypatch):
    seen = []

    def fake_run(cmd, **kw):
        m = cmd[cmd.index("--model") + 1]
        seen.append(m)
        if m == "haiku":
            return SimpleNamespace(returncode=1, stdout="", stderr="error: model not available")
        return SimpleNamespace(returncode=0, stdout=json.dumps({"result": '{"ok": true, "fix": "", "motivo": ""}'}), stderr="")

    from pydantic import BaseModel

    class V(BaseModel):
        ok: bool
        fix: str = ""
        motivo: str = ""

    monkeypatch.setattr(pipeline, "ai_backend", lambda: "cli")
    monkeypatch.setattr(pipeline, "_claude_cli", lambda: "claude")
    monkeypatch.setattr(pipeline, "_sp_run", fake_run)
    monkeypatch.delenv("NOVOCLIP_CLAUDE_MODEL", raising=False)
    monkeypatch.delenv("NOVOCLIP_MODEL_COPY", raising=False)
    assert pipeline.ask_claude("x", V, pipeline.Options(), role="copy").ok is True
    assert seen == ["haiku", "sonnet"]


def test_role_models_table(monkeypatch):
    for k in ("NOVOCLIP_CLAUDE_MODEL", "NOVOCLIP_MODEL_TECH", "NOVOCLIP_MODEL_COPY", "NOVOCLIP_MODEL_VERIFY"):
        monkeypatch.delenv(k, raising=False)
    o = pipeline.Options()
    assert pipeline._role_models("verify", "cli", o) == ["opus", "sonnet"]
    assert pipeline._role_models("tech", "cli", o) == ["sonnet"]
    assert pipeline._role_models("copy", "api", o) == ["claude-haiku-5-5", o.ai_model]
    assert pipeline._role_models(None, "cli", o) == ["sonnet"]
    monkeypatch.setenv("NOVOCLIP_MODEL_COPY", "sonnet")
    assert pipeline._role_models("copy", "cli", o) == ["sonnet"]
