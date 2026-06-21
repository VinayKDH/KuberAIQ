import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_HEADER } from "@/lib/constants";

const API_UPSTREAM = (
  process.env.API_UPSTREAM_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
).replace(/\/$/, "");

const ADMIN_API_KEY = process.env.ADMIN_API_KEY ?? "";

async function proxyAdmin(request: NextRequest, pathSegments: string[]) {
  const sessionKey = request.headers.get(ADMIN_SESSION_HEADER);
  if (!ADMIN_API_KEY || !sessionKey || sessionKey !== ADMIN_API_KEY) {
    return NextResponse.json(
      { error: { message: "Unauthorized admin session" } },
      { status: 401 },
    );
  }

  const path = pathSegments.join("/");
  const target = new URL(`${API_UPSTREAM}/api/v1/${path}`);
  request.nextUrl.searchParams.forEach((value, key) => {
    target.searchParams.set(key, value);
  });

  const headers = new Headers();
  headers.set("X-Admin-Api-Key", ADMIN_API_KEY);
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  const upstream = await fetch(target.toString(), init);
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyAdmin(request, context.params.path);
}

export async function POST(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyAdmin(request, context.params.path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyAdmin(request, context.params.path);
}

export async function PUT(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyAdmin(request, context.params.path);
}

export async function DELETE(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyAdmin(request, context.params.path);
}
