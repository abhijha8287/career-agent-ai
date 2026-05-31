# Database Schema

## candidates

- `id` UUID primary key
- `email` unique
- `full_name`
- `linkedin_url`
- `github_url`
- `portfolio_url`
- `skills` JSONB
- `preferred_roles` JSONB
- `preferred_locations` JSONB
- `salary_expectation`
- `work_mode`
- `opportunity_type`
- `visa_sponsorship_required`
- `years_experience`
- `profile_summary`
- `created_at`

## jobs

- `id` UUID primary key
- `source`
- `external_job_id`
- `title`
- `company`
- `location`
- `salary_min`
- `salary_max`
- `employment_type`
- `required_skills` JSONB
- `preferred_skills` JSONB
- `responsibilities` JSONB
- `benefits` JSONB
- `deadline`
- `apply_url`
- `original_description`
- `cleaned_description`
- `company_details` JSONB
- `raw_payload` JSONB
- `last_seen_at`
- `created_at`
- `updated_at`

Unique constraint:

- `(source, external_job_id, company, apply_url)`

## applications

- `id` UUID primary key
- `candidate_id`
- `job_id`
- `stage`
- `match_score`
- `scores` JSONB
- `resume_version_url`
- `cover_letter_url`
- `log` JSONB
- `created_at`
- `updated_at`

## recommended future tables

- `resume_versions`
- `cover_letters`
- `connector_runs`
- `notifications`
- `calendar_events`
- `email_threads`
- `skill_trends`
- `assistant_messages`
- `audit_events`
