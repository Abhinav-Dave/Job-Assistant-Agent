import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Tooltip({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("relative inline-block", className)} {...props}>
      {children}
    </span>
  );
}
