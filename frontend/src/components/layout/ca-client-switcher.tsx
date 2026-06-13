"use client";

import { useRouter } from "next/navigation";
import { useCaClients, useClearCaContext, useSwitchCaContext } from "@/features/ca/hooks";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { CA_COPY, ROUTES } from "@/lib/constants";
import { getStoredUser } from "@/lib/auth";

export function CaClientSwitcher() {
  const router = useRouter();
  const user = getStoredUser();
  const { data } = useCaClients();
  const switchMutation = useSwitchCaContext();
  const clearMutation = useClearCaContext();

  if (!user || user.role !== "CA") return null;

  const activeClients =
    data?.items.filter((item) => item.status === "ACTIVE") ?? [];

  const handleSwitch = async (companyId: string) => {
    await switchMutation.mutateAsync(companyId);
    router.push(ROUTES.COMPLIANCE);
  };

  const handleClear = async () => {
    await clearMutation.mutateAsync();
    router.push(ROUTES.CA_CLIENTS);
  };

  return (
    <div className="hidden items-center gap-2 md:flex">
      <span className="text-xs text-muted-foreground">{CA_COPY.SWITCHER_LABEL}</span>
      <Select
        value={user.company_id ?? ""}
        placeholder={CA_COPY.SWITCHER_PLACEHOLDER}
        options={activeClients.map((client) => ({
          value: client.company_id,
          label: client.company_name ?? client.company_id,
        }))}
        onValueChange={handleSwitch}
        className="w-44"
      />
      {user.company_id && (
        <Button variant="ghost" size="sm" onClick={handleClear} disabled={clearMutation.isPending}>
          {CA_COPY.CLEAR_CLIENT}
        </Button>
      )}
    </div>
  );
}
