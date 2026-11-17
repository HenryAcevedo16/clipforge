import type { Metadata } from "next";
import { ProjectsList } from "@/components/projects/ProjectsList";

export const metadata: Metadata = { title: "Mis proyectos" };

export default function Page() {
  return <ProjectsList />;
}
