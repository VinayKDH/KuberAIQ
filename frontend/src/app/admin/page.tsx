import { redirect } from "next/navigation";

import { ROUTES } from "@/lib/constants";

export default function AdminIndexPage() {
  redirect(ROUTES.ADMIN_DASHBOARD);
}
