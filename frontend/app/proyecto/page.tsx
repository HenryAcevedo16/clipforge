"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ProjectDetail } from "@/components/projects/ProjectDetail";

// La app se sirve como páginas estáticas, así que el id del proyecto va en la dirección: /proyecto/?id=…
function Inner() {
  const id = useSearchParams().get("id") ?? "";
  return <ProjectDetail id={id} />;
}

export default function Page() {
  return (
    <Suspense>
      <Inner />
    </Suspense>
  );
}
