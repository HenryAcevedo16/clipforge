"use client";
/**
 * KIT DE MARCA
 * ✅ Ya soportado por el backend: solo el estilo de subtítulos (caption_style: viral/caja/karaoke/neon/minimal/none).
 * ❌ REQUIERE BACKEND NUEVO: guardar plantillas, logo y marca de agua, tipografía propia, colores propios.
 *    Hoy las plantillas viven en el navegador (localStorage). Cada grupo del editor avisa "Aún no se aplica en los clips".
 */
import { Card } from "@heroui/react";
import { ArrowLeft, Check, ImagePlus, Palette, Plus, Star, Trash2, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type BrandTemplate, type SubtitleStyleId, type WatermarkPosition } from "@/lib/api";
import { uid } from "@/lib/api/storage";
import { FONT_META, FONT_ORDER, POSITIONS, STYLE_META, STYLE_ORDER } from "@/lib/brand";
import { useResource } from "@/lib/hooks/useResource";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Range, Switch } from "../ui/Controls";
import { cn } from "../ui/cn";
import { Dialog } from "../ui/Dialog";
import { Field, inputClass } from "../ui/Field";
import { PageHeader } from "../ui/PageHeader";
import { PreviewNotice } from "../ui/PreviewNotice";
import { EmptyState, ErrorState, LoadingLabel, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";
import { ClipPreview } from "./ClipPreview";

const MAX_LOGO = 1.5 * 1024 * 1024; // el prototipo guarda el logo en localStorage; el real lo subiría al servidor

const blank = (): BrandTemplate => ({
  id: `tpl_${uid(6)}`,
  name: "",
  isDefault: false,
  captionStyle: "viral",
  fontId: "arial-black",
  colors: { text: "#FFFFFF", highlight: "#FFE600" },
  logo: null,
  watermark: { enabled: false, position: "br", size: 16, opacity: 80 },
  createdAt: Date.now(),
});

const Soon = () => <Badge tone="neutral">Aún no se aplica en los clips</Badge>;

function Group({ title, badge, children }: { title: string; badge?: React.ReactNode; children: React.ReactNode }) {
  return (
    <Card className="min-w-0 gap-0 border border-line p-5">
      <fieldset className="min-w-0">
        <legend className="sr-only">{title}</legend>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-extrabold" aria-hidden>
            {title}
          </h3>
          {badge}
        </div>
        <div className="flex flex-col gap-5">{children}</div>
      </fieldset>
    </Card>
  );
}

export function BrandKit() {
  const res = useResource(() => api.listTemplates(), []);
  const toast = useToast();
  const [draft, setDraft] = useState<BrandTemplate | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [logoError, setLogoError] = useState<string | null>(null);

  const list = res.data ?? [];
  const original = list.find((t) => t.id === draft?.id);
  const dirty = !!draft && (isNew || JSON.stringify(original) !== JSON.stringify(draft));

  // En escritorio abre la primera plantilla sola; en celular se queda en la lista.
  useEffect(() => {
    if (draft || !res.data?.length) return;
    if (window.matchMedia("(min-width: 1024px)").matches) setDraft(structuredClone(res.data.find((t) => t.isDefault) ?? res.data[0]));
  }, [res.data, draft]);

  const select = (t: BrandTemplate) => {
    setDraft(structuredClone(t));
    setIsNew(false);
    setNameError(null);
    setLogoError(null);
  };
  const create = () => {
    setDraft(blank());
    setIsNew(true);
    setNameError(null);
    setLogoError(null);
  };
  const patch = (p: Partial<BrandTemplate>) => setDraft((d) => (d ? { ...d, ...p } : d));

  const save = async () => {
    if (!draft) return;
    if (!draft.name.trim()) return setNameError("Ponle un nombre a la plantilla para poder reconocerla.");
    setSaving(true);
    try {
      await api.saveTemplate({ ...draft, name: draft.name.trim() });
      await res.reload(true);
      setIsNew(false);
      toast("Plantilla guardada.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pudimos guardar la plantilla.", "bad");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!draft) return;
    try {
      if (!isNew) await api.deleteTemplate(draft.id);
      setConfirmDel(false);
      setDraft(null);
      setIsNew(false);
      await res.reload(true);
      toast("Plantilla eliminada.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pudimos eliminarla.", "bad");
    }
  };

  const onLogo = (f: File | undefined) => {
    if (!f) return;
    if (!/^image\/(png|jpe?g|webp|svg\+xml)$/.test(f.type)) return setLogoError("Usa una imagen PNG, JPG, WebP o SVG.");
    if (f.size > MAX_LOGO) return setLogoError("El logo pesa más de 1.5 MB. Prueba con uno más liviano.");
    const r = new FileReader();
    r.onload = () => {
      setLogoError(null);
      patch({ logo: { name: f.name, dataUrl: String(r.result) }, watermark: { ...draft!.watermark, enabled: true } });
    };
    r.onerror = () => setLogoError("No pudimos leer ese archivo.");
    r.readAsDataURL(f);
  };

  const editing = !!draft;

  return (
    <div>
      <PageHeader
        title="Kit de marca"
        description="Crea plantillas para que todos tus clips salgan con el mismo estilo. La predeterminada se aplica sola."
        actions={
          <Button variant="primary" onClick={create} icon={<Plus className="size-4" aria-hidden />}>
            Nueva plantilla
          </Button>
        }
      />
      <PreviewNotice>El estilo de subtítulos y el logo con su marca de agua (esquina, tamaño y opacidad) ya se aplican a los clips: elige la plantilla en el paso 2 al crear tus clips. La tipografía y los colores propios todavía no se dibujan en el video.</PreviewNotice>

      {res.loading && (
        <>
          <LoadingLabel text="Cargando tus plantillas…" />
          <div className="grid gap-6 lg:grid-cols-[18rem_1fr]" aria-hidden>
            <div className="flex flex-col gap-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
            <Skeleton className="h-96" />
          </div>
        </>
      )}

      {!res.loading && res.error && <ErrorState title="No pudimos cargar tus plantillas" message={res.error} onRetry={() => res.reload()} />}

      {!res.loading && !res.error && list.length === 0 && !editing && (
        <EmptyState icon={<Palette />} title="Aún no tienes plantillas" text="Una plantilla guarda tu estilo de subtítulos, tu logo y tus colores. Créala una vez y úsala en todos tus clips." action={<Button variant="primary" onClick={create}>Crear mi primera plantilla</Button>} />
      )}

      {!res.loading && !res.error && (list.length > 0 || editing) && (
        <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[17rem_minmax(0,1fr)] xl:grid-cols-[17rem_minmax(0,1fr)_15rem]">
          {/* Lista */}
          <nav aria-label="Tus plantillas" className={cn("flex flex-col gap-2", editing && "max-lg:hidden")}>
            <ul className="flex flex-col gap-2">
              {list.map((t) => {
                const on = draft?.id === t.id && !isNew;
                return (
                  <li key={t.id}>
                    <button
                      type="button"
                      onClick={() => select(t)}
                      aria-current={on ? "true" : undefined}
                      className={cn(
                        "flex min-h-[4.5rem] w-full items-center gap-3 rounded-2xl border bg-raised p-3 text-left transition-[border-color,background-color,transform] duration-150 active:scale-[0.99]",
                        on ? "border-accent-hi bg-accent-soft" : "border-line hover:border-line-2",
                      )}
                    >
                      <span className="grid size-12 shrink-0 place-items-center overflow-hidden rounded-xl bg-black text-[11px] font-extrabold" style={{ color: STYLE_META[t.captionStyle].highlight }}>
                        {t.logo ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={t.logo.dataUrl} alt="" className="size-full object-contain p-1" />
                        ) : (
                          "Aa"
                        )}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span title={t.name} className="line-clamp-2 block font-bold leading-snug [overflow-wrap:anywhere]">{t.name}</span>
                        <span className="mt-0.5 flex items-center gap-1.5 text-[13px] text-ink-3">
                          {t.isDefault && <Star className="size-3.5 shrink-0 fill-warn text-warn" aria-hidden />}
                          <span className="truncate">{t.isDefault ? "Predeterminada" : STYLE_META[t.captionStyle].label}</span>
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
              {isNew && draft && (
                <li>
                  <div className="flex min-h-[4.5rem] items-center gap-3 rounded-2xl border border-dashed border-accent-hi bg-accent-soft/50 p-3 text-sm font-bold text-accent-hi">
                    <Plus className="size-5" aria-hidden />
                    Plantilla nueva (sin guardar)
                  </div>
                </li>
              )}
            </ul>
          </nav>

          {/* Editor */}
          {draft ? (
            <section aria-label="Editor de plantilla" className="min-w-0 flex flex-col gap-4">
              <button type="button" onClick={() => { setDraft(null); setIsNew(false); }} className="inline-flex min-h-11 items-center gap-1.5 self-start text-sm font-bold text-ink-2 hover:text-ink lg:hidden">
                <ArrowLeft className="size-4" aria-hidden />
                Mis plantillas
              </button>

              {/* Vista previa en celular: arriba del editor */}
              <div className="mx-auto w-36 xl:hidden" aria-hidden>
                <PreviewOf t={draft} />
              </div>

              <Field label="Nombre de la plantilla" error={nameError}>
                {(p) => <input {...p} value={draft.name} maxLength={80} onChange={(e) => { patch({ name: e.target.value }); setNameError(null); }} placeholder="Ej.: Mi podcast, Clips de ventas…" className={inputClass} />}
              </Field>

              <Group title="Estilo de subtítulos" badge={<Badge tone="ok" icon={<Check className="size-3" strokeWidth={3} aria-hidden />}>Ya funciona en tus clips</Badge>}>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {STYLE_ORDER.map((id) => (
                    <label key={id} className="relative cursor-pointer">
                      <input type="radio" name="estilo" className="peer sr-only" checked={draft.captionStyle === id} onChange={() => patch({ captionStyle: id as SubtitleStyleId, colors: { ...draft.colors, highlight: STYLE_META[id].highlight } })} />
                      <span className="flex min-h-[3.75rem] flex-col justify-center rounded-2xl border border-line bg-shell px-3.5 py-2 transition-[border-color,background-color,transform] duration-150 active:scale-[0.98] hover:border-line-2 peer-checked:border-accent-hi peer-checked:bg-accent-soft peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent-hi">
                        <span className="font-bold" style={id === "none" ? undefined : { color: STYLE_META[id].highlight }}>
                          {STYLE_META[id].label}
                        </span>
                        <span className="text-xs leading-tight text-ink-3">{STYLE_META[id].hint}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </Group>

              <Group title="Colores y tipografía" badge={<Soon />}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <ColorField label="Color del texto" value={draft.colors.text} onChange={(v) => patch({ colors: { ...draft.colors, text: v } })} />
                  <ColorField label="Color de la palabra activa" value={draft.colors.highlight} onChange={(v) => patch({ colors: { ...draft.colors, highlight: v } })} />
                </div>
                <Field label="Tipografía">
                  {(p) => (
                    <select {...p} value={draft.fontId} onChange={(e) => patch({ fontId: e.target.value as BrandTemplate["fontId"] })} className={inputClass}>
                      {FONT_ORDER.map((f) => (
                        <option key={f} value={f}>
                          {FONT_META[f].label}
                        </option>
                      ))}
                    </select>
                  )}
                </Field>
              </Group>

              <Group title="Logo y marca de agua" badge={<Soon />}>
                <div>
                  <p className="mb-1.5 text-sm font-medium text-ink-2">Logo</p>
                  {draft.logo ? (
                    <div className="flex items-center gap-3 rounded-2xl border border-line bg-shell p-3">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={draft.logo.dataUrl} alt="Tu logo" className="size-14 shrink-0 rounded-xl bg-black/40 object-contain p-1" />
                      <p className="min-w-0 flex-1 truncate text-sm text-ink-2">{draft.logo.name}</p>
                      <Button size="sm" variant="ghost" onClick={() => patch({ logo: null, watermark: { ...draft.watermark, enabled: false } })} icon={<Trash2 className="size-4" aria-hidden />}>
                        Quitar
                      </Button>
                    </div>
                  ) : (
                    <label className="relative flex min-h-24 cursor-pointer flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed border-line-2 bg-shell px-4 py-4 text-center transition-colors hover:border-accent-hi focus-within:border-accent-hi focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent-hi">
                      <input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" className="sr-only" onChange={(e) => onLogo(e.target.files?.[0])} />
                      <ImagePlus className="size-6 text-ink-2" aria-hidden />
                      <span className="font-bold">Subir logo</span>
                      <span className="text-xs text-ink-3">PNG, JPG, WebP o SVG · hasta 1.5 MB</span>
                    </label>
                  )}
                  {logoError && (
                    <p role="alert" className="mt-1.5 text-[13px] text-bad">
                      {logoError}
                    </p>
                  )}
                </div>

                <Switch checked={draft.watermark.enabled} onChange={(v) => patch({ watermark: { ...draft.watermark, enabled: v } })} label="Poner el logo como marca de agua" hint="Aparece en una esquina durante todo el clip." />

                <div className={cn("flex flex-col gap-5 transition-opacity duration-200", !draft.watermark.enabled && "pointer-events-none opacity-45")} aria-disabled={!draft.watermark.enabled}>
                  <fieldset disabled={!draft.watermark.enabled} className="min-w-0">
                    <legend className="mb-1.5 text-sm font-medium text-ink-2">Posición</legend>
                    <div className="flex flex-wrap gap-2">
                      {POSITIONS.map((o) => (
                        <label key={o.v} className="relative cursor-pointer">
                          <input type="radio" name="pos" className="peer sr-only" checked={draft.watermark.position === o.v} onChange={() => patch({ watermark: { ...draft.watermark, position: o.v as WatermarkPosition } })} />
                          <span className="flex min-h-11 items-center rounded-[10px] border border-line bg-shell px-3.5 text-sm font-bold text-ink-2 transition-[border-color,background-color,color,transform] duration-150 active:scale-[0.97] peer-checked:border-accent-hi peer-checked:bg-accent-soft peer-checked:text-ink peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent-hi">
                            {o.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Range label="Tamaño" unit="%" min={8} max={40} value={draft.watermark.size} onChange={(v) => patch({ watermark: { ...draft.watermark, size: v } })} />
                    <Range label="Opacidad" unit="%" min={10} max={100} step={5} value={draft.watermark.opacity} onChange={(v) => patch({ watermark: { ...draft.watermark, opacity: v } })} />
                  </div>
                </div>
              </Group>

              <Switch checked={draft.isDefault} onChange={(v) => patch({ isDefault: v })} label="Usar como plantilla predeterminada" hint="Todos tus clips nuevos saldrán con este estilo, sin que tengas que elegirla." />

              <div className="sticky bottom-[calc(var(--bar-h)+env(safe-area-inset-bottom))] z-10 -mx-4 flex flex-wrap items-center gap-2 border-t border-line bg-ground/95 px-4 py-3 backdrop-blur-sm sm:mx-0 sm:rounded-2xl sm:border sm:bg-raised lg:bottom-4">
                <Button variant="primary" onClick={save} loading={saving} disabled={!dirty} icon={<Upload className="size-4" aria-hidden />}>
                  Guardar plantilla
                </Button>
                {dirty && !isNew && (
                  <Button variant="ghost" onClick={() => original && select(original)}>
                    Descartar cambios
                  </Button>
                )}
                <span className="text-sm text-ink-3" role="status">
                  {saving ? "Guardando…" : dirty ? "Tienes cambios sin guardar" : "Todo guardado"}
                </span>
                <Button variant="danger" onClick={() => setConfirmDel(true)} className="ml-auto" icon={<Trash2 className="size-4" aria-hidden />}>
                  {isNew ? "Cancelar" : "Eliminar"}
                </Button>
              </div>
            </section>
          ) : (
            <div className="hidden min-h-64 place-items-center rounded-3xl border border-dashed border-line-2 text-ink-3 lg:grid">Elige una plantilla para editarla</div>
          )}

          {/* Vista previa en vivo (escritorio ancho) */}
          {draft && (
            <aside className="hidden xl:block" aria-hidden>
              <p className="mb-2 text-sm font-medium text-ink-3">Vista previa en vivo</p>
              <div className="sticky top-8">
                <PreviewOf t={draft} />
              </div>
            </aside>
          )}
        </div>
      )}

      <Dialog
        open={confirmDel}
        onClose={() => setConfirmDel(false)}
        title={isNew ? "¿Descartar esta plantilla?" : "¿Eliminar esta plantilla?"}
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirmDel(false)}>
              Volver
            </Button>
            <Button variant="danger" onClick={remove}>
              {isNew ? "Descartar" : "Sí, eliminar"}
            </Button>
          </>
        }
      >
        <p className="text-ink-2 [overflow-wrap:anywhere]">{isNew ? "Perderás lo que has escrito en esta plantilla." : `«${draft?.name}» se borrará. Los clips que ya hiciste no cambian.`}</p>
      </Dialog>
    </div>
  );
}

function PreviewOf({ t }: { t: BrandTemplate }) {
  return <ClipPreview style={t.captionStyle} fontId={t.fontId} colors={t.colors} logo={t.logo?.dataUrl} watermark={t.watermark} className="w-full" />;
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <Field label={label}>
      {(p) => (
        <div className="flex items-center gap-3">
          <input {...p} type="color" value={value} onChange={(e) => onChange(e.target.value.toUpperCase())} className="size-11 shrink-0 cursor-pointer rounded-[10px] border border-line bg-raised p-1" />
          <span className="tnum text-sm text-ink-2">{value}</span>
        </div>
      )}
    </Field>
  );
}
