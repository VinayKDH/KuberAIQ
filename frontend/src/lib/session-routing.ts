import { ROUTES } from "@/lib/constants";

export interface SessionGate {
  needs_payment?: boolean;
  needs_onboarding?: boolean;
}

export function postLoginRoute(state: SessionGate): string {
  if (state.needs_payment) return ROUTES.SUBSCRIBE;
  if (state.needs_onboarding) return ROUTES.ONBOARDING;
  return ROUTES.DASHBOARD;
}

export interface MeGate extends SessionGate {
  subscription_active?: boolean;
}

export function resolveProtectedRoute(
  me: MeGate,
  pathname: string,
): string | null {
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
