import type { Metadata } from "next";
import { Accounts } from "@/components/accounts/Accounts";

export const metadata: Metadata = { title: "Cuentas de redes" };

export default function Page() {
  return <Accounts />;
}
