"use client";

import { Download, FileUp, RefreshCw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import {
  CandidateProfile,
  GeneratedMaterials,
  downloadMaterialPdf,
  generateMaterials,
  searchJobs,
  syncJobs,
  uploadResume
} from "@/lib/api";
import type { Job } from "@/types/domain";
import { JobCard } from "@/components/job-card";

const fallbackJobs: Job[] = [
  {
    id: "sample-1",
    source: "sample",
    title: "AI Product Engineer",
    company: "VectorWorks Labs",
    location: "Remote",
    salary_min: 120000,
    salary_max: 170000,
    employment_type: "full_time",
    required_skills: ["Python", "React", "OpenAI", "PostgreSQL"],
    preferred_skills: ["AWS", "Celery"],
    apply_url: "https://example.com",
    cleaned_description: "Upload a resume, choose a source, then search or sync to load personalized live jobs.",
    company_details: { status: "sample" }
  }
];

export function JobExplorer() {
  const [query, setQuery] = useState("engineer");
  const [location, setLocation] = useState("");
  const [source, setSource] = useState("");
  const [jobs, setJobs] = useState<Job[]>(fallbackJobs);
  const [status, setStatus] = useState("Ready");
  const [resumeStatus, setResumeStatus] = useState("Upload a resume to personalize ranking.");
  const [candidateProfile, setCandidateProfile] = useState<CandidateProfile | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [materials, setMaterials] = useState<GeneratedMaterials | null>(null);
  const [materialStatus, setMaterialStatus] = useState("Click the document icon on a job to generate tailored materials.");
  const [activeVersion, setActiveVersion] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [pdfStatus, setPdfStatus] = useState("");

  const sourceLabel = source ? source[0].toUpperCase() + source.slice(1) : "All sources";

  async function runSearch(
    nextQuery = query,
    nextLocation = location,
    nextSource = source,
    nextProfile = candidateProfile
  ) {
    setIsLoading(true);
      setStatus(`Searching ${nextSource || "all sources"}...`);
    try {
      const results = await searchJobs(nextQuery, nextLocation, nextSource, nextProfile);
      setJobs(results.length > 0 ? results : fallbackJobs);
      setStatus(
        results.length > 0
          ? `${results.length} live jobs loaded from ${nextSource || "available sources"}`
          : `No ${nextSource || "stored"} jobs matched. Try an empty query, run sync, or check connector config.`
      );
    } catch (error) {
      setJobs(fallbackJobs);
      const message = error instanceof Error ? error.message : "Unable to load jobs";
      setStatus(message === "Failed to fetch" ? "Backend is offline. Showing a sample job." : message);
    } finally {
      setIsLoading(false);
    }
  }

  async function runSync() {
    setIsLoading(true);
      setStatus("Syncing configured ATS and Reddit feeds...");
    try {
      const results = await syncJobs();
      const stored = results.reduce((total, item) => total + item.stored, 0);
      const errors = results.filter((item) => item.error);
      setStatus(errors.length > 0 ? `Synced ${stored} jobs with ${errors.length} source errors` : `Synced ${stored} jobs`);
      await runSearch();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to sync jobs");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResumeUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    setIsLoading(true);
    setResumeStatus("Parsing resume and building profile...");
    try {
      const profile = await uploadResume(file);
      setCandidateProfile(profile);
      setResumeStatus(`Resume loaded: ${profile.skills.slice(0, 6).join(", ") || "profile text extracted"}`);
      await runSearch(query, location, source, profile);
    } catch (error) {
      setResumeStatus(error instanceof Error ? error.message : "Unable to upload resume");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGenerateMaterials(job: Job) {
    setSelectedJob(job);
    setActiveVersion(0);
    if (!candidateProfile) {
      setMaterialStatus("Upload a resume first, then click the document icon on the job.");
      return;
    }
    setIsLoading(true);
    setMaterialStatus(`Generating ATS resume versions for ${job.title}...`);
    try {
      const generated = await generateMaterials(candidateProfile, job);
      setMaterials(generated);
      setMaterialStatus(`Generated resume_v1, resume_v2, resume_v3 and cover letter for ${job.company}.`);
    } catch (error) {
      setMaterials(null);
      setMaterialStatus(error instanceof Error ? error.message : "Unable to generate materials");
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePdfDownload(kind: "resume" | "cover") {
    if (!materials || !selectedJob) {
      return;
    }
    const activeResume = materials.versions[activeVersion];
    const candidateName = candidateProfile?.full_name || "Candidate";
    const baseName = `${candidateName}-${selectedJob.company}-${selectedJob.title}-${kind}`
      .replace(/[^a-z0-9]+/gi, "-")
      .replace(/(^-|-$)/g, "")
      .toLowerCase();
    const isResume = kind === "resume";
    const title = isResume ? `${candidateName} - Tailored Resume` : `${candidateName} - Cover Letter`;
    const subtitle = `${selectedJob.title} at ${selectedJob.company}`;
    const body = isResume ? activeResume.resume_markdown : materials.cover_letter;
    setPdfStatus(`Preparing ${isResume ? "resume" : "cover letter"} PDF...`);
    try {
      await downloadMaterialPdf(title, subtitle, body, `${baseName}.pdf`);
      setPdfStatus(`${isResume ? "Resume" : "Cover letter"} PDF downloaded.`);
    } catch (error) {
      setPdfStatus(error instanceof Error ? error.message : "Unable to download PDF");
    }
  }

  useEffect(() => {
    void runSearch();
  }, []);

  return (
    <section className="mx-auto grid max-w-7xl gap-5 px-5 py-8 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="min-w-0">
        <div className="mb-4 rounded-md border border-line bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <h2 className="text-xl font-semibold">Ranked Opportunities</h2>
            <p className="mt-1 text-sm text-ink/65">{status}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="rounded-md border border-line bg-paper px-3 py-1.5 text-xs font-medium text-ink/75 transition hover:border-moss hover:text-moss"
                onClick={() => {
                  setSource("reddit");
                  setQuery("");
                  setLocation("");
                  void runSearch("", "", "reddit");
                }}
                type="button"
              >
                Reddit latest
              </button>
              <button
                className="rounded-md border border-line bg-paper px-3 py-1.5 text-xs font-medium text-ink/75 transition hover:border-moss hover:text-moss"
                onClick={() => {
                  setSource("reddit");
                  setQuery("hiring");
                  setLocation("remote");
                  void runSearch("hiring", "remote", "reddit");
                }}
                type="button"
              >
                Reddit remote hiring
              </button>
            </div>
          </div>
          <div className="grid w-full gap-2 md:grid-cols-[minmax(140px,1fr)_150px_160px_42px_42px] xl:max-w-2xl">
            <input
              className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-moss"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search role"
            />
            <input
              className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-moss"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              aria-label="Search location"
            />
            <select
              className="rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-moss"
              value={source}
              onChange={(event) => {
                const nextSource = event.target.value;
                setSource(nextSource);
                if (nextSource === "reddit") {
                  setQuery("");
                  setLocation("");
                }
              }}
              aria-label="Source"
            >
              <option value="">All sources</option>
              <option value="greenhouse">Greenhouse</option>
              <option value="lever">Lever</option>
              <option value="ashby">Ashby</option>
              <option value="workable">Workable</option>
              <option value="recruitee">Recruitee</option>
              <option value="personio">Personio</option>
              <option value="reddit">Reddit</option>
              <option value="workday">Workday</option>
              <option value="successfactors">SuccessFactors</option>
              <option value="icims">iCIMS</option>
              <option value="taleo">Taleo</option>
            </select>
            <button
              className="grid size-[42px] place-items-center rounded-md bg-signal text-white shadow-sm transition hover:bg-signal/90 disabled:opacity-60"
              onClick={() => void runSearch()}
              disabled={isLoading}
              aria-label="Search stored jobs"
              title="Search stored jobs"
            >
              <Search size={18} />
            </button>
            <button
              className="grid size-[42px] place-items-center rounded-md border border-line bg-white text-moss shadow-sm transition hover:border-moss disabled:opacity-60"
              onClick={() => void runSync()}
              disabled={isLoading}
              aria-label="Sync ATS jobs"
              title="Sync ATS jobs"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job, index) => (
            <JobCard
              key={job.id}
              job={job}
              score={Math.max(70, 94 - index * 4)}
              onGenerate={handleGenerateMaterials}
              isGenerating={isLoading}
            />
          ))}
        </div>
      </div>

      <aside className="space-y-4">
        <section className="min-w-0 rounded-md border border-line bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <FileUp size={18} />
            <h2 className="font-semibold">Resume Ranking</h2>
          </div>
          <p className="mt-3 text-sm leading-6 text-ink/70">{resumeStatus}</p>
          <label className="mt-4 flex cursor-pointer items-center justify-center rounded-md border border-dashed border-moss bg-paper px-3 py-4 text-sm font-medium text-moss transition hover:bg-white">
            Upload PDF, DOCX, or TXT
            <input
              className="hidden"
              type="file"
              accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(event) => void handleResumeUpload(event.target.files?.[0])}
            />
          </label>
          {candidateProfile && (
            <div className="mt-4 space-y-2 text-xs text-ink/65">
              <p>File: {candidateProfile.resume_filename}</p>
              <p>Skills: {candidateProfile.skills.slice(0, 10).join(", ") || "Detected from resume text"}</p>
            </div>
          )}
        </section>
        <section className="rounded-md border border-line bg-white p-4 shadow-sm">
          <h2 className="font-semibold">Live Ingestion</h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-ink/75">
            <p>Jobs are loaded from PostgreSQL through the backend search API.</p>
            <p>Current filter: {sourceLabel}</p>
            <p>The sync button runs configured Greenhouse, Lever, Ashby, Workable, Recruitee, Personio, and Reddit connectors.</p>
            <p>Celery Beat keeps the same sync running every 30 minutes when Redis is available.</p>
          </div>
        </section>
        <section className="rounded-md border border-line bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-semibold">Resume Generation</h2>
            {materials && <span className="rounded-md bg-moss px-2 py-1 text-xs font-semibold text-white">{materials.ats_score}</span>}
          </div>
          <p className="mt-3 text-sm leading-6 text-ink/70">{materialStatus}</p>
          {selectedJob && (
            <p className="mt-2 text-xs text-ink/55">
              Selected: {selectedJob.title} at {selectedJob.company}
            </p>
          )}
          {materials && (
            <div className="mt-4 min-w-0 space-y-4">
              <div className="flex flex-wrap gap-2">
                {materials.versions.map((version, index) => (
                  <button
                    key={version.label}
                    className={`rounded-md border px-3 py-1.5 text-xs font-medium transition ${
                      activeVersion === index
                        ? "border-moss bg-moss text-white"
                        : "border-line bg-paper text-ink/75 hover:border-moss"
                    }`}
                    onClick={() => setActiveVersion(index)}
                    type="button"
                  >
                    {version.label}
                  </button>
                ))}
              </div>
              <div className="min-w-0 rounded-md border border-line bg-paper p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-signal">
                    {materials.versions[activeVersion]?.focus}
                  </p>
                  <button
                    className="inline-flex items-center gap-1 rounded-md border border-line bg-white px-2 py-1 text-xs font-medium text-moss transition hover:border-moss disabled:opacity-60"
                    onClick={() => void handlePdfDownload("resume")}
                    disabled={isLoading}
                    type="button"
                  >
                    <Download size={13} /> PDF
                  </button>
                </div>
                <DocumentPreview content={materials.versions[activeVersion]?.resume_markdown || ""} maxHeight="max-h-96" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold">Cover Letter</h3>
                  <button
                    className="inline-flex items-center gap-1 rounded-md border border-line bg-white px-2 py-1 text-xs font-medium text-moss transition hover:border-moss disabled:opacity-60"
                    onClick={() => void handlePdfDownload("cover")}
                    disabled={isLoading}
                    type="button"
                  >
                    <Download size={13} /> PDF
                  </button>
                </div>
                <DocumentPreview content={materials.cover_letter} maxHeight="max-h-72" />
              </div>
              {pdfStatus && <p className="text-xs text-ink/55">{pdfStatus}</p>}
              <div className="min-w-0 space-y-2 text-xs text-ink/65">
                <p className="break-words [overflow-wrap:anywhere]">
                  Matched: {materials.matched_keywords.slice(0, 8).join(", ") || "No direct keyword matches yet"}
                </p>
                <p className="break-words [overflow-wrap:anywhere]">
                  Gaps: {materials.missing_keywords.slice(0, 8).join(", ") || "No major gaps"}
                </p>
              </div>
            </div>
          )}
        </section>
      </aside>
    </section>
  );
}

function DocumentPreview({ content, maxHeight }: { content: string; maxHeight: string }) {
  const lines = content.split("\n");
  return (
    <div
      className={`mt-3 ${maxHeight} max-w-full overflow-y-auto overflow-x-hidden rounded-md border border-line bg-white p-4 text-sm leading-6 text-ink/80 shadow-sm`}
    >
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={index} className="h-3" />;
        }
        if (trimmed.startsWith("# ")) {
          return (
            <h3 key={index} className="break-words text-lg font-semibold leading-6 text-ink [overflow-wrap:anywhere]">
              {trimmed.slice(2)}
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h4 key={index} className="mt-3 break-words text-xs font-semibold uppercase tracking-wide text-moss [overflow-wrap:anywhere]">
              {trimmed.slice(3)}
            </h4>
          );
        }
        if (trimmed.startsWith("- ")) {
          return (
            <div key={index} className="mt-1 flex gap-2">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-signal" />
              <p className="min-w-0 break-words text-sm [overflow-wrap:anywhere]">{trimmed.slice(2)}</p>
            </div>
          );
        }
        return (
          <p key={index} className="mt-2 break-words text-sm [overflow-wrap:anywhere]">
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}
