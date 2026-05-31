type StatCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-moss">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-sm text-ink/65">{detail}</p>
    </section>
  );
}
