export function ScoreGauge({ score = 0 }: { score?: number }) {
  return (
    <div className="text-2xl font-bold tabular-nums">{score}</div>
  );
}
