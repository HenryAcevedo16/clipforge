"use client";
import { Modal } from "@heroui/react";
import type { ReactNode } from "react";

/** Diálogo con Modal de HeroUI (foco atrapado, Esc, fondo inerte). En celular HeroUI lo ajusta al ancho de la pantalla. */
export function Dialog({ open, onClose, title, children, footer, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; footer?: ReactNode; wide?: boolean }) {
  return (
    <Modal isOpen={open} onOpenChange={(o) => !o && onClose()}>
      <Modal.Backdrop>
        <Modal.Container placement="auto">
          <Modal.Dialog className={wide ? "sm:max-w-2xl" : "sm:max-w-lg"}>
            <Modal.CloseTrigger aria-label="Cerrar" />
            <Modal.Header>
              <Modal.Heading className="text-lg font-bold [overflow-wrap:anywhere]">{title}</Modal.Heading>
            </Modal.Header>
            <Modal.Body className="[overflow-wrap:anywhere]">{children}</Modal.Body>
            {footer && <Modal.Footer className="flex-wrap justify-end gap-2">{footer}</Modal.Footer>}
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}
