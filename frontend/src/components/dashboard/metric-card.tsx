import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatINR } from "@/lib/format";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  description?: string;
  variant?: "default" | "warning" | "danger";
  loading?: boolean;
  formatAsCurrency?: boolean;
}

const variantStyles = {
  default: "text-foreground",
  warning: "text-amber-600 dark:text-amber-400",
  danger: "text-destructive",
};

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  variant = "default",
  loading,
  formatAsCurrency = true,
}: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-32" />
        ) : (
          <div className={cn("text-2xl font-bold", variantStyles[variant])}>
            {formatAsCurrency ? formatINR(value) : value.toLocaleString("en-IN")}
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
