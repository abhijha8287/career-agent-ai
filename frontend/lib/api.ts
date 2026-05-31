import type { Job } from "@/types/domain";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CandidateProfile = {
  id: string;
  full_name: string;
  email: string;
  skills: string[];
  preferred_locations: string[];
  years_experience: number;
  profile_summary?: string | null;
  resume_text?: string | null;
  resume_filename?: string | null;
};

export type ResumeVersion = {
  label: string;
  focus: string;
  resume_markdown: string;
};

export type GeneratedMaterials = {
  resume_markdown: string;
  cover_letter: string;
  recruiter_message: string;
  linkedin_message: string;
  follow_up_email: string;
  ats_score: number;
  keywords: string[];
  matched_keywords: string[];
  missing_keywords: string[];
  versions: ResumeVersion[];
};

export async function searchJobs(
  query: string,
  location: string,
  source?: string,
  candidateProfile?: CandidateProfile | null
): Promise<Job[]> {
  const response = await fetch(`${API_URL}/api/jobs/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      location,
      source: source || null,
      limit: 12,
      candidate_profile: candidateProfile
    }),
    cache: "no-store"
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Unable to search jobs");
  }

  return response.json();
}

export async function uploadResume(file: File): Promise<CandidateProfile> {
  const form = new FormData();
  form.append("resume", file);

  const response = await fetch(`${API_URL}/api/candidates/resume`, {
    method: "POST",
    body: form
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Unable to upload resume");
  }

  return response.json();
}

export async function syncJobs(): Promise<Array<{ source: string; fetched: number; stored: number; error?: string | null }>> {
  const response = await fetch(`${API_URL}/api/jobs/sync`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Unable to sync jobs");
  }

  return response.json();
}

export async function generateMaterials(candidateProfile: CandidateProfile, job: Job): Promise<GeneratedMaterials> {
  const response = await fetch(`${API_URL}/api/materials/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_id: candidateProfile.id,
      job_id: job.id.includes(":") ? null : job.id,
      candidate_profile: candidateProfile,
      job
    }),
    cache: "no-store"
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Unable to generate resume materials");
  }

  return response.json();
}
