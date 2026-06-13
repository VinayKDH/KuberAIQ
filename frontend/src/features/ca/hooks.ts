import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { storeSession } from "@/lib/auth";
import {
  acceptCaInvite,
  clearCaContext,
  fetchAdvisors,
  fetchCaClients,
  fetchCaDashboard,
  inviteAdvisor,
  revokeAdvisor,
  switchCaContext,
} from "./api";
import type { InviteAdvisorPayload } from "./types";

export function useCaClients() {
  return useQuery({
    queryKey: QUERY_KEYS.CA_CLIENTS,
    queryFn: fetchCaClients,
  });
}

export function useCaDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.CA_DASHBOARD,
    queryFn: fetchCaDashboard,
  });
}

export function useAcceptCaInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: acceptCaInvite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_CLIENTS });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CA_DASHBOARD });
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
