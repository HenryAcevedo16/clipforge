"""Reglas editables: carga, glosario, plantillas de gancho, resaltado y guía para la IA."""
import json
from pathlib import Path

import pytest

import pipeline
import rules


@pytest.fixture
def rdir(tmp_path, monkeypatch):
    base, user = tmp_path / "reglas", tmp_path / "reglas" / "mis_reglas"
    user.mkdir(parents=True)
    monkeypatch.setattr(rules, "DIR", base)
    rules._cache.clear()
    rules._warned.clear()
    yield base, user
    rules._cache.clear()
    monkeypatch.undo()
    pipeline.load_rules()


def words(text, t0=0.0):
    return [{"w": w, "s": t0 + k * 0.5, "e": t0 + k * 0.5 + 0.4} for k, w in enumerate(text.split())]


def tr_of(text):
    ws = words(text)
    return {"language": "es", "segments": [{"s": 0, "e": ws[-1]["e"], "text": text, "words": ws}]}


# ---------------- base == valores de la app ----------------
def test_base_files_match_code_defaults():
    rules._cache.clear()
    assert set(x.lower() for x in rules.read_list("palabras_impacto.txt")) == pipeline._DEFAULTS["HOOK_WORDS"]
    assert set(rules.read_list("muletillas_inicio.txt")) == pipeline._DEFAULTS["FILLER_START"]
    assert set(rules.read_list("colas_gancho.txt")) == pipeline._DEFAULTS["HOOK_TAIL"]
    assert tuple(rules.read_list("relleno_cta.txt")) == pipeline._DEFAULTS["CTA_MARKERS"]
    assert "|".join(rules.read_regexes("risas.txt")) == pipeline._DEFAULTS["LAUGH"]


# ---------------- glosario ----------------
def test_glossary_single_word_keeps_times_and_punct(rdir):
    base, user = rdir
    (base / "glosario.txt").write_text("claud -> Claude\n", encoding="utf-8")
    tr = tr_of("Hola, claud. Funciona")
    t0 = [(w["s"], w["e"]) for w in tr["segments"][0]["words"]]
    pipeline.apply_glossary(tr)
    ws = tr["segments"][0]["words"]
    assert [w["w"] for w in ws] == ["Hola,", "Claude.", "Funciona"]
    assert [(w["s"], w["e"]) for w in ws] == t0
    assert tr["segments"][0]["text"] == "Hola, Claude. Funciona"


def test_glossary_multiword_merges_with_start_and_end(rdir):
    base, user = rdir
    (base / "glosario.txt").write_text("chat gepeté -> ChatGPT\n", encoding="utf-8")
    tr = tr_of("uso chat gepeté hoy")
    pipeline.apply_glossary(tr)
    ws = tr["segments"][0]["words"]
    assert [w["w"] for w in ws] == ["uso", "ChatGPT", "hoy"]
    assert (ws[1]["s"], ws[1]["e"]) == (0.5, 1.4)       # empieza donde la primera palabra (0.5) y acaba donde la última (1.4)


def test_glossary_idempotent_and_user_wins(rdir):
    base, user = rdir
    (base / "glosario.txt").write_text("novo clip -> Novo Clip\n", encoding="utf-8")
    (user / "glosario.txt").write_text("novo clip -> NovoClip\n", encoding="utf-8")
    tr = tr_of("el novo clip es bueno")
    pipeline.apply_glossary(tr)
    once = json.dumps(tr)
    pipeline.apply_glossary(tr)
    assert json.dumps(tr) == once and "NovoClip" in once


def test_glossary_applies_on_cache_without_rewriting_file(rdir, tmp_path, monkeypatch):
    base, user = rdir
    (base / "glosario.txt").write_text("claud -> Claude\n", encoding="utf-8")
    cache = tmp_path / "transcript.json"
    cache.write_text(json.dumps(tr_of("hola claud")), encoding="utf-8")
    before = cache.read_text(encoding="utf-8")
    out = pipeline.transcribe(Path("x.mp4"), tmp_path, pipeline.Options())
    assert out["segments"][0]["words"][1]["w"] == "Claude"
    assert cache.read_text(encoding="utf-8") == before            # la caché queda sin glosario


# ---------------- archivos rotos / sobrescribir ----------------
def test_broken_or_empty_files_fall_back_to_defaults(rdir, capsys):
    base, user = rdir
    (base / "palabras_impacto.txt").write_text("# nada\n", encoding="utf-8")
    (base / "risas.txt").write_text("(sin cerrar\n", encoding="utf-8")
    (base / "glosario.txt").write_text("sin flecha\n", encoding="utf-8")
    pipeline.load_rules()
    assert pipeline.HOOK_WORDS == pipeline._DEFAULTS["HOOK_WORDS"]
    assert pipeline.LAUGH_RE.pattern == pipeline._DEFAULTS["LAUGH"]
    assert rules.read_glossary() == []
    out = capsys.readouterr().out
    assert "expresión inválida" in out and "sin «->»" in out
    capsys.readouterr()
    rules.read_regexes("risas.txt")                                # el aviso sale una sola vez
    assert capsys.readouterr().out == ""


def test_user_rules_add_remove_and_reload_on_change(rdir):
    base, user = rdir
    (base / "palabras_impacto.txt").write_text("secreto\nerror\n", encoding="utf-8")
    (user / "palabras_impacto.txt").write_text("brutal\n-error\n", encoding="utf-8")
    pipeline.load_rules()
    assert pipeline.HOOK_WORDS == {"secreto", "brutal"}
    p = user / "palabras_impacto.txt"
    p.write_text("-secreto\nloco\n", encoding="utf-8-sig")        # con BOM, como el Bloc de notas
    import os, time
    os.utime(p, (time.time() + 5, time.time() + 5))
    pipeline.load_rules()
    assert pipeline.HOOK_WORDS == {"error", "loco"}


# ---------------- plantillas de gancho ----------------
def test_hook_options_max3_first_is_current_no_leftovers(rdir):
    base, user = rdir
    (base / "ganchos.txt").write_text("pregunta | ¿{frase}\nnumero | {numero}: lo que nadie cuenta\ntema | Lo que nadie dice de {tema}\n"
                                      "tema | Mira esto sobre {tema}\nnumero | {sinvariable} x\n", encoding="utf-8")
    opts = pipeline._hook_options("POR QUÉ ESTO FALLA", "el error del dinero pasó 3 veces", 1)
    assert opts[0] == "POR QUÉ ESTO FALLA" and 1 < len(opts) <= 3
    assert len(set(opts)) == len(opts) and not any("{" in o for o in opts)
    q = pipeline._hook_options("POR QUÉ ESTO FALLA", "sin ni ya no", 0)
    assert q[0] == "POR QUÉ ESTO FALLA" and all(o.endswith("?") for o in q[1:])      # solo aplica la plantilla de pregunta


def test_hook_options_without_applicable_templates_is_just_current(rdir):
    base, user = rdir
    (base / "ganchos.txt").write_text("numero | {numero} cosas\n", encoding="utf-8")
    assert pipeline._hook_options("HOLA MUNDO", "nada de cifras aquí", 1) == ["HOLA MUNDO"]


def test_select_heuristic_fills_hook_options(rdir):
    base, user = rdir
    (base / "ganchos.txt").write_text("tema | Lo que nadie dice de {tema}\n", encoding="utf-8")
    (base / "palabras_impacto.txt").write_text("error\nsecreto\n", encoding="utf-8")
    segs, t = [], 0.0
    for i in range(30):
        ws = words("Mira el error secreto que nadie cuenta de verdad.", t)
        segs.append({"s": t, "e": ws[-1]["e"], "text": " ".join(w["w"] for w in ws), "words": ws})
        t = ws[-1]["e"] + 0.5
    cl = pipeline.select_heuristic(None, {"language": "es", "segments": segs}, pipeline.Options(num_clips=1, min_len=20, max_len=40))
    assert cl and cl[0].hook_options[0] == cl[0].hook and len(cl[0].hook_options) >= 2


# ---------------- resaltado ----------------
def test_highlight_always_and_never(rdir):
    base, user = rdir
    (base / "resaltado.txt").write_text("+increíble\n-quiero\n", encoding="utf-8")
    (user / "resaltado.txt").write_text("-increíble\n+dinero\n", encoding="utf-8")
    always, never = rules.read_highlight()
    assert "dinero" in always and "increíble" in never and "increíble" not in always and "quiero" in never
    (base / "palabras_impacto.txt").write_text("quiero\nsecreto\n", encoding="utf-8")
    pipeline.load_rules()
    assert "quiero" not in pipeline._auto_keywords("quiero el secreto")


# ---------------- guía para la IA ----------------
def test_guide_truncated_comments_dropped_and_user_replaces(rdir):
    base, user = rdir
    (base / "guia_ia.md").write_text("# comentario\n" + "\n".join(f"Regla {i}: " + "x" * 80 for i in range(60)), encoding="utf-8")
    g = rules.read_guide()
    assert 0 < len(g) <= 1500 and "comentario" not in g and not g.endswith("x" * 81)
    (user / "guia_ia.md").write_text("Mi estilo: corto.\n", encoding="utf-8")
    assert rules.read_guide() == "Mi estilo: corto."
    (user / "guia_ia.md").write_text("# solo comentarios\n", encoding="utf-8")
    assert rules.read_guide().startswith("Regla 0")                # la del usuario está vacía: se usa la base


def test_guide_only_comments_gives_empty_and_prompt_unchanged(rdir):
    base, user = rdir
    (base / "guia_ia.md").write_text("# nada\n", encoding="utf-8")
    assert rules.read_guide() == ""


def test_hook_options_no_double_inverted_mark(rdir):
    base, user = rdir
    (base / "ganchos.txt").write_text("pregunta | ¿{frase}\n", encoding="utf-8")
    o = pipeline._hook_options("¿QUÉ PASA AQUÍ?", "texto cualquiera", 0)
    assert "¿¿" not in " ".join(o) and "¿QUÉ PASA AQUÍ?" in o


def test_hook_topic_is_a_noun_not_a_question_or_impact_word(rdir):
    base, user = rdir
    (base / "ganchos.txt").write_text("tema | Lo que nadie dice de {tema}\n", encoding="utf-8")
    (base / "palabras_impacto.txt").write_text("qué\nincreíble\nnadie\n", encoding="utf-8")
    pipeline.load_rules()
    o = pipeline._hook_options("MIRA ESTO", "qué increíble el dinero, el dinero cambia todo y nadie lo ve", 0)
    assert any("DINERO" in x for x in o[1:]) and not any(("QUÉ" in x.split()[-1:] or "INCREÍBLE" in x) for x in o[1:])
    assert pipeline._hook_options("MIRA ESTO", "qué increíble nadie", 0) == ["MIRA ESTO"]      # sin tema válido no hay plantilla de tema
