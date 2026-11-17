import type { Metadata } from "next";
import { Settings } from "@/components/settings/Settings";

export const metadata: Metadata = { title: "Ajustes" };

export default function Page() {
  return <Settings />;
}
