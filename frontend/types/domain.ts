export type Job = {
  id: string;
  source: string;
  external_job_id?: string | null;
  title: string;
  company: string;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  employment_type: string;
  required_skills: string[];
  preferred_skills: string[];
  apply_url: string;
  cleaned_description: string;
  company_details: Record<string, unknown>;
  last_seen_at?: string | null;
  budget?: string | null;
  author?: string | null;
  posted_date?: string | null;
  link?: string | null;
  match_score?: number | null;
  semantic_match_score?: number | null;
  skill_match_score?: number | null;
  experience_fit_score?: number | null;
  location_fit_score?: number | null;
};

export type Application = {
  id: string;
  job_id: string;
  stage: "saved" | "applied" | "assessment" | "interview" | "offer" | "rejected";
  mode: string;
};
