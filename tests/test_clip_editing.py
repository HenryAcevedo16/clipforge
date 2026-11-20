"""Pruebas de: gancho con sentido, nota absoluta, trozo guardado por clip y rerender sin volver a descargar."""
import json
from pathlib import Path

import pytest

import pipeline


def mk_lines(texts, gap=3.0):
    lines, t = [], 0.0
    for tx in texts:
        ws = [{"w": w, "s": t + k * 0.4, "e": t + k * 0.4 + 0.35} for k, w in enumerate(tx.split())]
        lines.append({"s": ws[0]["s"], "e": ws[-1]["e"], "text": tx, "words": ws})
        t += gap
    return lines


def hook_of(texts, gap=3.0):
    lines = mk_lines(texts, gap)
    feats = pipeline._line_features(lines, [0.0] * len(lines))
    return pipeline._best_hook(lines, feats, 0, len(lines) - 1)


# ---------------- gancho ----------------
def test_hook_max_words_and_no_filler_edges():
    h = hook_of(["Entonces pues bueno la cosa es que nadie sabe por qué pasa esto de verdad"])
    assert 0 < len(h.split()) <= 7
    assert pipeline._norm(h.split()[0]) not in pipeline.FILLER_START
    assert pipeline._norm(h.split()[-1]) not in pipeline.HOOK_TAIL


def test_hook_cuts_at_question_and_prefers_strong_line():
    h = hook_of(["y luego pues eso", "¿Por qué nadie te cuenta esto? Lo demás da igual de verdad", "normal."])
    assert h.endswith("?") and "luego" not in h


def test_hook_no_orphan_inverted_marks():
    h = hook_of(["¿Sabes cuál es el gran secreto de todo este asunto que nadie"])
    assert "¿" not in h or "?" in h


def test_hook_single_word_not_empty_and_no_cta():
    assert hook_of(["Bueno"]) != ""
    h = hook_of(["suscríbete y dale like a este canal ahora mismo", "El secreto está en 3 cosas simples"])
    assert "suscr" not in h.lower()


def test_hook_ignores_lines_after_25s():
    h = hook_of(["tema normal sin nada especial aquí", "otra frase normal sin más"], gap=30.0)
    assert h.startswith("tema")


# ---------------- nota absoluta ----------------
def _tr(texts):
    segs, t = [], 0.0
    for i in range(40):
        s = texts[i % len(texts)]
        w = [{"w": x, "s": t + j * 0.45, "e": t + j * 0.45 + 0.4} for j, x in enumerate(s.split())]
        segs.append({"s": t, "e": w[-1]["e"], "text": s, "words": w})
        t = w[-1]["e"] + 0.6
    return {"language": "es", "segments": segs}


def test_score_is_absolute_not_rescaled():
    o = pipeline.Options(num_clips=2, min_len=20, max_len=45)
    weak = pipeline.select_heuristic(None, _tr(["vamos a ver que tal queda esto ahora mismo"]), o)
    strong = pipeline.select_heuristic(None, _tr(["Mira esto nunca hagas esto es un error.", "por qué nadie te lo dice?",
                                                  "jajaja no puede ser!", "El secreto: 3 de cada 10 fallan."]), o)
    assert all(0 <= c.score <= 100 for c in weak + strong)
    assert max(c.score for c in strong) > max(c.score for c in weak)
    assert max(c.score for c in weak) < 70          # antes siempre salía 70-95


# ---------------- trozo guardado ----------------
def test_live_src_reads_clip_src_and_legacy_and_broken(tmp_path):
    d = tmp_path / "clip_src"
    d.mkdir()
    (d / "01.mkv").write_bytes(b"x")
    (d / "01.json").write_text(json.dumps({"off": 5.0, "dur": 30.0, "file": "01.mkv"}))
    f, off, dur = pipeline._live_src(tmp_path, 1)
    assert f.name == "01.mkv" and off == 5.0 and dur == 30.0
    old = tmp_path / "live_src"
    old.mkdir()
    (old / "02.mp4").write_bytes(b"x")
    (old / "02.json").write_text(json.dumps({"off": 1.0, "dur": 9.0}))           # formato antiguo: sin "file"
    assert pipeline._live_src(tmp_path, 2)[0].name == "02.mp4"
    (d / "03.json").write_text("{roto")
    assert pipeline._live_src(tmp_path, 3) is None
    assert pipeline._live_src(tmp_path, 9) is None


def test_keep_clip_source_moves_file(tmp_path):
    part = tmp_path / "trozo_01.mkv"
    part.write_bytes(b"x")
    c = pipeline.Clip(index=1, start=0, end=1, title="t", hook="h", score=1, reason="", caption="", hashtags=[])
    pipeline._keep_clip_source(tmp_path, c, part, 12.5, {"duration": 40.0})
    assert not part.exists() and (tmp_path / "clip_src" / "01.mkv").exists()
    assert pipeline._live_src(tmp_path, 1)[1:] == (12.5, 40.0)


# ---------------- rerender sin volver a descargar ----------------
@pytest.fixture
def job(tmp_path, monkeypatch):
    wd = tmp_path / "job"
    (wd / "clip_src").mkdir(parents=True)
    (wd / "edit").mkdir()
    (wd / "clips").mkdir()
    (wd / "clip_src" / "01.mkv").write_bytes(b"x")
    (wd / "clip_src" / "01.json").write_text(json.dumps({"off": 100.0, "dur": 60.0, "file": "01.mkv"}))
    json.dump([{"w": f"p{i}", "s": 100 + i * 0.5, "e": 100 + i * 0.5 + 0.4} for i in range(120)], (wd / "edit" / "01.json").open("w"))
    clip = {"index": 1, "start": 110.0, "end": 140.0, "title": "t", "hook": "H", "score": 50, "reason": "r", "caption": "c",
            "hashtags": ["#a"], "file": "01_t.mp4", "thumb": "", "review": {}, "duration": 30, "keywords": []}
    (wd / "result.json").write_text(json.dumps({"title": "T", "language": "es", "source": {}, "clips": [clip]}))
    (wd / "job.json").write_text(json.dumps({"source": "https://youtube.com/watch?v=x", "opts": {}}))
    seen = {}

    def fake_render(src, c, tr, o, outdir, meta, progress, p0, p1, scene=None):
        seen["src"], seen["start"], seen["end"] = Path(src).name, c.start, c.end
        c.file, c.thumb, c.out_duration = "01_t.mp4", "", c.end - c.start
        return c

    monkeypatch.setattr(pipeline, "render_clip", fake_render)
    monkeypatch.setattr(pipeline, "probe", lambda p: {"width": 1280, "height": 720, "fps": 30, "duration": 60, "has_audio": True})
    return wd, seen


def test_rerender_inside_saved_piece_does_not_download(job, monkeypatch):
    wd, seen = job
    monkeypatch.setattr(pipeline, "download", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debe descargar")))
    pipeline.rerender_clip(wd, 1, {"hook": "NUEVO"})
    assert seen["src"] == "01.mkv" and (seen["start"], seen["end"]) == (10.0, 40.0)   # tiempos relativos al trozo
    assert json.loads((wd / "result.json").read_text())["clips"][0]["hook"] == "NUEVO"


def test_rerender_outside_piece_falls_back_to_clipped_range(job, monkeypatch):
    wd, seen = job
    msgs = []
    monkeypatch.setattr(pipeline, "download", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bloqueado")))
    pipeline.rerender_clip(wd, 1, {"start": 90.0, "end": 170.0}, lambda p, m: msgs.append(m))
    assert (seen["start"], seen["end"]) == (0.0, 60.0)          # recortado a [off, off+dur] relativo
    assert any("Solo hay video guardado" in m for m in msgs)


def test_rerender_outside_piece_downloads_when_possible(job, monkeypatch, tmp_path):
    wd, seen = job
    got = {}

    def fake_dl(url, workdir, o, progress, section=None, stem="x", label=""):
        got["section"] = section
        f = workdir / "editar_01.mkv"
        f.write_bytes(b"x")
        return f, "t"

    monkeypatch.setattr(pipeline, "download", fake_dl)
    pipeline.rerender_clip(wd, 1, {"start": 90.0, "end": 170.0})
    assert got["section"] == (88.5, 171.5) and seen["src"] == "editar_01.mkv"
