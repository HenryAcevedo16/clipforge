"use client";
/**
 * CUENTAS DE REDES — [REQUIERE BACKEND NUEVO]
 * Todo es simulado: no se piden contraseñas ni tokens. En la versión real, "Conectar" abre la ventana OFICIAL de cada
 * red (OAuth) y el backend guarda los tokens cifrados. Aquí solo se guarda un nombre de ejemplo en el navegador.
 */
import { Card } from "@heroui/react";
import { AlertTriangle, CalendarClock, Link2, Plug, ShieldCheck, Unplug } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { api, type Network, type SocialAccount } from "@/lib/api";
import { NETWORK_META } from "@/lib/brand";
import { useResource } from "@/lib/hooks/useResource";
import { timeAgo } from "@/lib/time";
import { Badge } from "../ui/Badge";
import { Button, buttonClass } from "../ui/Button";
import { Dialog } from "../ui/Dialog";
import { PageHeader } from "../ui/PageHeader";
import { PreviewNotice } from "../ui/PreviewNotice";
import { EmptyState, ErrorState, LoadingLabel, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";
import { NetworkIcon } from "./NetworkIcon";

const NETWORKS: Network[] = ["tiktok", "youtube", "instagram"];

export function Accounts() {
  const res = useResource(() => api.listAccounts(), []);
  const toast = useToast();
  const [connecting, setConnecting] = useState<Network | null>(null);
  const [disconnecting, setDisconnecting] = useState<SocialAccount | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const accounts = res.data ?? [];
  const needsReconnect = accounts.filter((a) => a.status === "reconnect");

  const connect = async () => {
    if (!connecting) return;
    setBusy("connect");
    try {
      const a = await api.connectAccount(connecting);
      await res.reload(true);
      toast(`Conectaste ${a.handle} (simulado).`);
      setConnecting(null);
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pudimos conectar la cuenta.", "bad");
    } finally {
      setBusy(null);
    }
  };

  const reconnect = async (a: SocialAccount) => {
    setBusy(a.id);
    try {
      await api.reconnectAccount(a.id);
      await res.reload(true);
      toast(`${a.handle} está conectada otra vez.`);
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pudimos reconectar la cuenta.", "bad");
    } finally {
      setBusy(null);
    }
  };

  const disconnect = async () => {
    if (!disconnecting) return;
    setBusy("disconnect");
    try {
      await api.disconnectAccount(disconnecting.id);
      await res.reload(true);
      toast("Cuenta desconectada.");
      setDisconnecting(null);
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pudimos desconectarla.", "bad");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <PageHeader title="Cuentas de redes" description="Conecta las cuentas donde quieres publicar. Solo podrás programar clips en las que estén conectadas." />
      <PreviewNotice>Vista previa: estas conexiones son de muestra, no se conecta ninguna cuenta real todavía. Publicar de verdad exige crear una app de desarrollador en cada red.</PreviewNotice>

      {res.loading && (
        <>
          <LoadingLabel text="Cargando tus cuentas…" />
          <div className="flex flex-col gap-4" aria-hidden>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-36" />
            ))}
          </div>
        </>
      )}

      {!res.loading && res.error && <ErrorState title="No pudimos cargar tus cuentas" message={res.error} onRetry={() => res.reload()} />}

      {!res.loading && !res.error && (
        <div className="flex flex-col gap-5">
          {accounts.length === 0 && <EmptyState icon={<Link2 />} title="Aún no conectas ninguna cuenta" text="Conecta TikTok, YouTube Shorts o Instagram Reels para programar tus clips desde el Calendario." />}

          {needsReconnect.length > 0 && (
            <div role="alert" className="flex items-start gap-3 rounded-3xl border border-warn/35 bg-warn-soft p-4">
              <AlertTriangle className="mt-0.5 size-5 shrink-0 text-warn" aria-hidden />
              <p className="text-ink-2">
                <strong className="text-ink">{needsReconnect.length === 1 ? "Una cuenta necesita reconectarse." : `${needsReconnect.length} cuentas necesitan reconectarse.`}</strong> Mientras tanto no se publicará nada en {needsReconnect.length === 1 ? "ella" : "ellas"}.
              </p>
            </div>
          )}

          {NETWORKS.map((n) => {
            const m = NETWORK_META[n];
            const list = accounts.filter((a) => a.network === n);
            return (
              <Card key={n} aria-labelledby={`h-${n}`} className="gap-0 border border-line p-0">
                <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-line p-4 sm:p-5">
                  <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-shell ring-1 ring-line" style={{ color: m.color }}>
                    <NetworkIcon network={n} className="size-6" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h2 id={`h-${n}`} className="text-lg font-bold">
                      {m.label}
                    </h2>
                    <p className="text-sm text-ink-2">{m.will}</p>
                  </div>
                  <Button onClick={() => setConnecting(n)} icon={<Plug className="size-4" aria-hidden />} className="max-sm:w-full">
                    Conectar {list.length ? "otra cuenta" : "cuenta"}
                  </Button>
                </div>

                {list.length === 0 ? (
                  <p className="p-4 text-sm text-ink-3 sm:px-5">No hay cuentas conectadas en {m.label}.</p>
                ) : (
                  <ul className="divide-y divide-line">
                    {list.map((a) => (
                      <li key={a.id} className="flex flex-wrap items-center gap-x-4 gap-y-3 p-4 sm:px-5">
                        <div className="min-w-0 flex-1 basis-56">
                          <p className="truncate font-bold" title={a.displayName}>{a.displayName}</p>
                          <p className="truncate text-sm text-ink-3" title={a.handle}>
                            {a.handle} · conectada {timeAgo(a.connectedAt)}
                          </p>
                        </div>
                        <Badge tone={a.status === "connected" ? "ok" : "warn"} icon={a.status === "reconnect" ? <AlertTriangle className="size-3" aria-hidden /> : undefined}>
                          {a.status === "connected" ? "Conectada" : "Requiere reconexión"}
                        </Badge>
                        <div className="flex gap-2 max-sm:w-full">
                          {a.status === "reconnect" && (
                            <Button size="sm" variant="primary" loading={busy === a.id} onClick={() => reconnect(a)} className="max-sm:flex-1">
                              Reconectar
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" onClick={() => setDisconnecting(a)} icon={<Unplug className="size-4" aria-hidden />} className="max-sm:flex-1" aria-label={`Desconectar ${a.handle} de ${m.label}`}>
                            Desconectar
                          </Button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            );
          })}

          {accounts.some((a) => a.status === "connected") && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-line bg-shell p-4">
              <p className="text-ink-2">¿Todo listo? Elige un clip y programa su publicación.</p>
              <Link href="/calendario" className={buttonClass({ variant: "primary" })}>
                <CalendarClock className="size-4" aria-hidden />
                Ir al Calendario
              </Link>
            </div>
          )}
        </div>
      )}

      <Dialog
        open={!!connecting}
        onClose={() => setConnecting(null)}
        title={connecting ? `Conectar ${NETWORK_META[connecting].label}` : ""}
        footer={
          <>
            <Button variant="ghost" onClick={() => setConnecting(null)}>
              Cancelar
            </Button>
            <Button variant="primary" onClick={connect} loading={busy === "connect"}>
              Simular conexión
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-3 text-ink-2">
          <p>
            En la versión final se abrirá la <strong className="text-ink">ventana oficial de {connecting && NETWORK_META[connecting].label}</strong> para que autorices a NovoClip.
          </p>
          <p className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-ok" aria-hidden />
            Nunca te pedimos tu contraseña. Puedes desconectar la cuenta cuando quieras.
          </p>
          <p className="rounded-xl bg-raised-2 px-3 py-2 text-sm">Por ahora esto es una demostración: se crea una cuenta de ejemplo.</p>
        </div>
      </Dialog>

      <Dialog
        open={!!disconnecting}
        onClose={() => setDisconnecting(null)}
        title="¿Desconectar esta cuenta?"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDisconnecting(null)}>
              Volver
            </Button>
            <Button variant="danger" onClick={disconnect} loading={busy === "disconnect"}>
              Sí, desconectar
            </Button>
          </>
        }
      >
        <p className="text-ink-2 [overflow-wrap:anywhere]">
          Se quitará <strong className="text-ink">{disconnecting?.handle}</strong>. Las publicaciones programadas que solo iban a esa cuenta se cancelarán.
        </p>
      </Dialog>
    </div>
  );
}
