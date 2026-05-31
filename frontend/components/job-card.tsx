import { Building2, ExternalLink, FileText, MapPin, Sparkles } from "lucide-react";
import type { Job } from "@/types/domain";

export function JobCard({
  job,
  score,
  onGenerate,
  isGenerating
}: {
  job: Job;
  score: number;
  onGenerate?: (job: Job) => void;
  isGenerating?: boolean;
}) {
  const displayScore = job.match_score ?? score;
  return (
    <article className="rounded-md border border-line bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-ink">{job.title}</h3>
          <p className="mt-1 flex items-center gap-2 text-sm text-ink/70">
            <Building2 size={15} /> {job.company}
          </p>
        </div>
        <div className="min-w-16 rounded-md bg-moss px-2 py-1 text-center text-sm font-semibold text-white shadow-sm">
          {displayScore}
        </div>
      </div>
      {job.semantic_match_score !== undefined && job.semantic_match_score !== null && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-ink/65">
          <span>Semantic {job.semantic_match_score}</span>
          <span>Skills {job.skill_match_score}</span>
          <span>Experience {job.experience_fit_score}</span>
          <span>Location {job.location_fit_score}</span>
        </div>
      )}
      <p className="mt-3 flex items-center gap-2 text-sm text-ink/70">
        <MapPin size={15} /> {job.location ?? "Flexible"}
      </p>
      <p className="mt-3 line-clamp-3 text-sm leading-6 text-ink/75">{job.cleaned_description}</p>
      {(job.budget || job.author) && (
        <p className="mt-3 text-sm text-ink/70">
          {job.budget ? `Budget: ${job.budget}` : null}
          {job.budget && job.author ? " - " : null}
          {job.author ? `u/${job.author}` : null}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        {job.required_skills.slice(0, 5).map((skill) => (
          <span key={skill} className="rounded-md border border-line bg-paper px-2 py-1 text-xs text-ink/75">
            {skill}
          </span>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-signal">
          <Sparkles size={14} /> AI package ready
        </span>
        <div className="flex items-center gap-2">
          {onGenerate && (
            <button
              className="grid size-8 place-items-center rounded-md border border-line bg-paper text-moss transition hover:border-moss disabled:opacity-60"
              onClick={() => onGenerate(job)}
              disabled={isGenerating}
              type="button"
              aria-label="Generate resume and cover letter"
              title="Generate resume and cover letter"
            >
              <FileText size={15} />
            </button>
          )}
          <a
            className="grid size-8 place-items-center rounded-md border border-line bg-white text-moss transition hover:border-moss"
            href={job.link || job.apply_url}
            aria-label="Open source job"
            title="Open source job"
          >
            <ExternalLink size={15} />
          </a>
        </div>
      </div>
    </article>
  );
}
