import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { storeSession } from "@/lib/auth";
import {
  acceptCaInvite,
  bulkCompleteCaFilings,
  clearCaContext,
  completeCaClientFiling,
  createCaClientTask,
  deleteCaClientTask,
  exportCaFilingCsv,
  fetchAdvisors,
  fetchCaClients,
  fetchCaClientTasks,
  fetchCaCompliancePack,
  fetchCaDashboard,
  fetchCaBulkGstr1,
  fetchCaBulkGstr3b,
  inviteAdvisor,
  revokeAdvisor,
  skipCaClientFiling,
  switchCaContext,
  updateCaClientTask,
} from "./api";
import type { InviteAdvisorPayload } from "./types";

export function useCaClients() {
  return useQuery({
    queryKey: QUERY_KEYS.CA_CLIENTS,
    queryFn: fetchCaClients,
  });
}

export function useCaDashboard(advisorId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.CA_DASHBOARD(advisorId),
    queryFn: () => fetchCaDashboard(advisorId),
  });
}

export function useAcceptCaInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: acceptCaInvite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_CLIENTS });
      queryClient.invalidateQueries({ queryKey: ["ca", "dashboard"] });
    },
  });
}

export function useSwitchCaContext() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: switchCaContext,
    onSuccess: (tokens) => {
      storeSession(tokens);
      queryClient.invalidateQueries();
    },
  });
}

export function useClearCaContext() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: clearCaContext,
    onSuccess: (tokens) => {
      storeSession(tokens);
      queryClient.invalidateQueries();
    },
  });
}

export function useAdvisors() {
  return useQuery({
    queryKey: QUERY_KEYS.ADVISORS,
    queryFn: fetchAdvisors,
  });
}

export function useInviteAdvisor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: InviteAdvisorPayload) => inviteAdvisor(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ADVISORS });
    },
  });
}

export function useRevokeAdvisor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: revokeAdvisor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ADVISORS });
    },
  });
}

export function useCaBulkGstr1() {
  return useMutation({
    mutationFn: fetchCaBulkGstr1,
  });
}

export function useCaBulkGstr3b() {
  return useMutation({
    mutationFn: fetchCaBulkGstr3b,
  });
}

export function useCaCompleteFiling() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      companyId,
      obligationId,
      periodKey,
    }: {
      companyId: string;
      obligationId: string;
      periodKey?: string | null;
    }) => completeCaClientFiling(companyId, obligationId, periodKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ca", "dashboard"] });
    },
  });
}

export function useCaSkipFiling() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      companyId,
      obligationId,
      periodKey,
    }: {
      companyId: string;
      obligationId: string;
      periodKey?: string | null;
    }) => skipCaClientFiling(companyId, obligationId, periodKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ca", "dashboard"] });
    },
  });
}

export function useCaBulkCompleteFilings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: bulkCompleteCaFilings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ca", "dashboard"] });
    },
  });
}

export function useCaExportFilingCsv() {
  return useMutation({
    mutationFn: exportCaFilingCsv,
  });
}

export function useCaClientTasks(companyId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.CA_CLIENT_TASKS(companyId),
    queryFn: () => fetchCaClientTasks(companyId),
  });
}

export function useCaCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, title }: { companyId: string; title: string }) =>
      createCaClientTask(companyId, { title }),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_CLIENT_TASKS(vars.companyId) });
    },
  });
}

export function useCaUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      companyId,
      taskId,
      ...body
    }: {
      companyId: string;
      taskId: string;
      title?: string;
      status?: string;
    }) => updateCaClientTask(companyId, taskId, body),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_CLIENT_TASKS(vars.companyId) });
    },
  });
}

export function useCaDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, taskId }: { companyId: string; taskId: string }) =>
      deleteCaClientTask(companyId, taskId),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_CLIENT_TASKS(vars.companyId) });
    },
  });
}

export function useCaCompliancePack() {
  return useMutation({
    mutationFn: ({
      companyId,
      companyName,
      from,
      to,
    }: {
      companyId: string;
      companyName: string;
      from: string;
      to: string;
    }) =>
      fetchCaCompliancePack(companyId, from, to).then((data) => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `compliance-pack-${companyName.replace(/\s+/g, "-").toLowerCase()}.json`;
        link.click();
        URL.revokeObjectURL(url);
      }),
  });
}
