import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Button({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm",
        className
      )}
      {...props}
    />
  );
}
