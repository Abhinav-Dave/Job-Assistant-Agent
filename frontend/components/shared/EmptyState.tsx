export function EmptyState({ title }: { title: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
      <p className="text-slate-600">{title}</p>
    </div>
  );
}
