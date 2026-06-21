"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminAuditLogs } from "@/features/admin/hooks";
import { ADMIN_COPY, DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { formatDate } from "@/lib/format";

export default function AdminAuditPage() {
  const { data, isLoading, isError } = useAdminAuditLogs({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.AUDIT_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.AUDIT_SUBTITLE}</p>
      </div>

      {isError ? <p className="text-red-400">{ADMIN_COPY.ERROR}</p> : null}

      <div className="rounded-lg border border-zinc-800">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead>Time</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Entity</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>IP</TableHead>
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
              data.items.map((log) => (
                <TableRow key={log.id} className="border-zinc-800">
                  <TableCell className="text-zinc-400">{formatDate(log.created_at)}</TableCell>
                  <TableCell>{log.company_name ?? log.company_id.slice(0, 8)}</TableCell>
                  <TableCell>
                    {log.entity_type}
                    {log.entity_id ? ` · ${log.entity_id.slice(0, 8)}` : ""}
                  </TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell className="text-zinc-400">
                    {log.actor_user_id ? log.actor_user_id.slice(0, 8) : "—"}
                  </TableCell>
                  <TableCell className="text-zinc-500">{log.ip_address ?? "—"}</TableCell>
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
