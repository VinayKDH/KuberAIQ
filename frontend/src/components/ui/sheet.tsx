"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SheetContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SheetContext = React.createContext<SheetContextValue | null>(null);

function useSheet() {
  const ctx = React.useContext(SheetContext);
  if (!ctx) throw new Error("Sheet components must be used within Sheet");
  return ctx;
}

interface SheetProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

function Sheet({ open: controlledOpen, onOpenChange, children }: SheetProps) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = React.useCallback(
    (value: boolean) => {
      setInternalOpen(value);
      onOpenChange?.(value);
    },
    [onOpenChange],
  );

  return (
    <SheetContext.Provider value={{ open, setOpen }}>{children}</SheetContext.Provider>
  );
}

function SheetTrigger({ children }: { children: React.ReactElement }) {
  const { setOpen } = useSheet();
  const childProps = children.props as { onClick?: (e: React.MouseEvent) => void };
  return React.cloneElement(children, {
    onClick: (e: React.MouseEvent) => {
      childProps.onClick?.(e);
      setOpen(true);
    },
  } as React.HTMLAttributes<HTMLElement>);
}

function SheetContent({
  side = "left",
  className,
  children,
}: React.HTMLAttributes<HTMLDivElement> & { side?: "left" | "right" }) {
  const { open, setOpen } = useSheet();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div className="fixed inset-0 bg-black/80" onClick={() => setOpen(false)} aria-hidden />
      <div
        className={cn(
          "fixed z-50 flex h-full flex-col gap-4 border bg-background p-6 shadow-lg transition ease-in-out w-3/4 max-w-sm",
          side === "left" ? "left-0" : "right-0",
          className,
        )}
      >
        {children}
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-4 top-4"
          onClick={() => setOpen(false)}
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </Button>
      </div>
    </div>
  );
}

function SheetHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-2 text-center sm:text-left", className)} {...props} />;
}

function SheetTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold text-foreground", className)} {...props} />;
}

export { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle };
