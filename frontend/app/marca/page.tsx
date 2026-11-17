import type { Metadata } from "next";
import { BrandKit } from "@/components/brand/BrandKit";

export const metadata: Metadata = { title: "Kit de marca" };

export default function Page() {
  return <BrandKit />;
}
