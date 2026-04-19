export function ConfidenceBadge({ value }: { value: number }) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
      {value.toFixed(2)}
    </span>
  );
}
