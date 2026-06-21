"use client";

import { useState } from "react";

import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminUsers } from "@/features/admin/hooks";
import { ADMIN_COPY, DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { formatDate } from "@/lib/format";

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, isError } = useAdminUsers({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    search: search || undefined,
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.USERS_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.USERS_SUBTITLE}</p>
      </div>

      <Input
        placeholder={ADMIN_COPY.SEARCH_PLACEHOLDER}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm border-zinc-700 bg-zinc-950"
      />

      {isError ? <p className="text-red-400">{ADMIN_COPY.ERROR}</p> : null}

      <div className="rounded-lg border border-zinc-800">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead>Email</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Joined</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-zinc-500">
                  {ADMIN_COPY.LOADING}
                </TableCell>
              </TableRow>
            ) : data?.items.length ? (
              data.items.map((user) => (
                <TableRow key={user.id} className="border-zinc-800">
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name ?? "—"}</TableCell>
                  <TableCell>{user.role}</TableCell>
                  <TableCell>{user.company_name ?? "—"}</TableCell>
                  <TableCell>{user.is_active ? "Active" : "Inactive"}</TableCell>
                  <TableCell className="text-zinc-400">{formatDate(user.created_at)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="text-zinc-500">
                  {ADMIN_COPY.NO_DATA}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
