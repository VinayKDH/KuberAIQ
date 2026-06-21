import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function AdminMetricCard({
  title,
  value,
  hint,
  className,
}: {
  title: string;
  value: string | number;
  hint?: string;
  className?: string;
}) {
  return (
    <Card className={cn("border-zinc-800 bg-zinc-950 text-zinc-100", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
        {hint ? <p className="mt-1 text-xs text-zinc-500">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}
