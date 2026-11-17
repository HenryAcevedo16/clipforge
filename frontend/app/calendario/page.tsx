import type { Metadata } from "next";
import { Suspense } from "react";
import { CalendarView } from "@/components/calendar/CalendarView";

export const metadata: Metadata = { title: "Calendario" };

export default function Page() {
  // useSearchParams (para "Programar" desde un clip) exige Suspense en esta versión de Next.
  return (
    <Suspense>
      <CalendarView />
    </Suspense>
  );
}
