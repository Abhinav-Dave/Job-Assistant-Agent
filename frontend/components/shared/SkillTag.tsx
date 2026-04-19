export function SkillTag({
  label,
  matched,
}: {
  label: string;
  matched?: boolean;
}) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs ${
        matched ? "bg-green-100 text-green-900" : "bg-red-100 text-red-900"
      }`}
    >
      {label}
    </span>
  );
}
