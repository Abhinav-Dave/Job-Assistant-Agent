import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Dialog({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="dialog"
      className={cn("rounded-lg border border-slate-200 bg-white p-4 shadow-lg", className)}
      {...props}
    />
  );
}
