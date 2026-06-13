import { ROUTES, USER_ROLE } from "@/lib/constants";

export interface SessionGate {
  needs_payment?: boolean;
  needs_onboarding?: boolean;
  role?: string;
  user?: { role?: string; company_id?: string | null };
}

function resolveRole(state: SessionGate): string | undefined {
  return state.role ?? state.user?.role;
}

function resolveCompanyId(state: SessionGate): string | null | undefined {
  return state.user?.company_id;
}

export function postLoginRoute(state: SessionGate): string {
  if (resolveRole(state) === USER_ROLE.CA) return ROUTES.CA_CLIENTS;
  if (state.needs_payment) return ROUTES.SUBSCRIBE;
  if (state.needs_onboarding) return ROUTES.ONBOARDING;
  return ROUTES.DASHBOARD;
}

export interface MeGate extends SessionGate {
  subscription_active?: boolean;
}

const CA_HUB_ROUTES = [ROUTES.CA_CLIENTS, ROUTES.CA_DASHBOARD] as const;

const CA_CLIENT_ROUTES = [
  ROUTES.CA_CLIENTS,
  ROUTES.CA_DASHBOARD,
  ROUTES.COMPLIANCE,
  ROUTES.SETTINGS,
] as const;

function matchesRoute(pathname: string, route: string): boolean {
  return pathname === route || pathname.startsWith(`${route}/`);
}

function isCaHubPath(pathname: string): boolean {
  return CA_HUB_ROUTES.some((route) => matchesRoute(pathname, route));
}

function isCaClientPath(pathname: string): boolean {
  return CA_CLIENT_ROUTES.some((route) => matchesRoute(pathname, route));
}

export function resolveProtectedRoute(me: MeGate, pathname: string): string | null {
  const role = resolveRole(me);

  if (role === USER_ROLE.CA) {
    if (pathname === ROUTES.DASHBOARD) {
      return ROUTES.CA_DASHBOARD;
    }
    const companyId = resolveCompanyId(me);
    if (!companyId) {
      if (!isCaHubPath(pathname)) {
        return ROUTES.CA_CLIENTS;
      }
    } else if (!isCaClientPath(pathname)) {
      return ROUTES.COMPLIANCE;
    }
    return null;
  }

  if (pathname.startsWith("/ca")) {
    return ROUTES.DASHBOARD;
  }

  if (me.needs_payment && pathname !== ROUTES.SUBSCRIBE) {
    return ROUTES.SUBSCRIBE;
  }
  if (!me.needs_payment && me.needs_onboarding && pathname !== ROUTES.ONBOARDING) {
    return ROUTES.ONBOARDING;
  }
  if (
    !me.needs_payment &&
    !me.needs_onboarding &&
    (pathname === ROUTES.ONBOARDING || pathname === ROUTES.SUBSCRIBE)
  ) {
    return ROUTES.DASHBOARD;
  }
  return null;
}
