"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createCaClientTask, fetchCaClientTasks, updateCaClientTask } from "@/features/ca/api";
import { CA_WORKSPACE_COPY } from "@/lib/constants";
import { formatDate } from "@/lib/format";

interface CaClientTasksPanelProps {
  companyId: string;
}

export function CaClientTasksPanel({ companyId }: CaClientTasksPanelProps) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["ca", "tasks", companyId],
    queryFn: () => fetchCaClientTasks(companyId),
  });

  const createMutation = useMutation({
    mutationFn: (taskTitle: string) => createCaClientTask(companyId, { title: taskTitle }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ca", "tasks", companyId] });
      setTitle("");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      updateCaClientTask(companyId, taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ca", "tasks", companyId] });
    },
  });

  const tasks = data?.items ?? [];

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{CA_WORKSPACE_COPY.TASKS_TITLE}</p>
      <div className="flex gap-2">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={CA_WORKSPACE_COPY.TASK_PLACEHOLDER}
        />
        <Button
          size="sm"
          disabled={!title.trim() || createMutation.isPending}
          onClick={() => createMutation.mutate(title.trim())}
        >
          {CA_WORKSPACE_COPY.TASK_ADD}
        </Button>
      </div>
      {isLoading && <p className="text-sm text-muted-foreground">Loading tasks…</p>}
      {!isLoading && tasks.length === 0 && (
        <p className="text-sm text-muted-foreground">No tasks yet.</p>
      )}
      {!isLoading && tasks.length > 0 && (
        <ul className="space-y-2 text-sm">
          {tasks.map((task) => (
            <li
              key={task.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2"
            >
              <div>
                <p className="font-medium">{task.title}</p>
                {task.due_date && (
                  <p className="text-muted-foreground">Due {formatDate(task.due_date)}</p>
                )}
              </div>
              {task.status === "pending" ? (
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={updateMutation.isPending}
                  onClick={() =>
                    updateMutation.mutate({ taskId: task.id, status: "done" })
                  }
                >
                  Mark done
                </Button>
              ) : (
                <span className="text-muted-foreground capitalize">{task.status}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
