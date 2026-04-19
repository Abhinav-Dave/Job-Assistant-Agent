import { cn } from "@/lib/utils";

export function Progress({
  className,
  value = 0,
}: {
  className?: string;
  value?: number;
}) {
  return (
    <div
      className={cn("h-2 w-full overflow-hidden rounded-full bg-slate-100", className)}
    >
      <div
        className="h-full bg-slate-800 transition-all"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
