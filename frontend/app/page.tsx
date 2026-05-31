import { Bell, Bot, BriefcaseBusiness, ChartNoAxesCombined, KanbanSquare, Search, ShieldCheck } from "lucide-react";
import { JobExplorer } from "@/components/job-explorer";
import { StatCard } from "@/components/stat-card";

const stages = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f4f5f1]">
      <nav className="sticky top-0 z-20 border-b border-line bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-md bg-ink text-white shadow-sm">
              <BriefcaseBusiness size={19} />
            </div>
            <div>
              <span className="text-base font-semibold">JobHunter AI</span>
              <p className="text-xs text-ink/55">Personalized job intelligence</p>
            </div>
          </div>
          <div className="hidden items-center gap-6 text-sm text-ink/70 md:flex">
            <a href="#search">Search</a>
            <a href="#pipeline">Pipeline</a>
            <a href="#analytics">Analytics</a>
            <a href="#assistant">Assistant</a>
          </div>
        </div>
      </nav>

      <section className="border-b border-line bg-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[minmax(0,1fr)_420px]">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-md border border-line bg-paper px-3 py-1.5 text-xs font-medium text-moss">
              <ShieldCheck size={14} />
              Resume-aware ranking with transparent scores
            </div>
            <h1 className="max-w-3xl text-3xl font-semibold leading-tight text-ink md:text-5xl">
              Find better jobs with your resume in the loop.
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-ink/70 md:text-lg">
              Upload your resume, search across job boards and communities, and rank roles by semantic fit,
              skills, experience, and location.
            </p>
            <div id="search" className="mt-6 grid max-w-2xl gap-3 rounded-md border border-line bg-paper p-2 md:grid-cols-[1fr_180px_46px]">
              <input className="rounded-md border border-line bg-white px-3 py-3 text-sm outline-none focus:border-moss" defaultValue="AI engineer" aria-label="Role" />
              <input className="rounded-md border border-line bg-white px-3 py-3 text-sm outline-none focus:border-moss" defaultValue="Remote" aria-label="Location" />
              <button className="grid place-items-center rounded-md bg-signal text-white shadow-sm transition hover:bg-signal/90" aria-label="Search jobs">
                <Search size={20} />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 self-start">
            <StatCard label="Sources" value="11" detail="ATS, Reddit, freelance" />
            <StatCard label="Ranking" value="4-part" detail="Semantic, skills, exp, location" />
            <StatCard label="Resume" value="PDF" detail="DOCX and TXT supported" />
            <StatCard label="Sync" value="30m" detail="Scheduled ingestion" />
          </div>
        </div>
      </section>

      <JobExplorer />

      <section className="border-y border-line bg-white">
        <div className="mx-auto grid max-w-7xl gap-4 px-5 py-8 md:grid-cols-2">
          <section className="rounded-md border border-line bg-white p-4">
            <div className="flex items-center gap-2">
              <Bot size={18} />
              <h2 id="assistant" className="font-semibold">Career Agent</h2>
            </div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-ink/75">
              <p>Top gap for AI roles: production RAG evaluation and cloud deployment.</p>
              <p>Suggested project: build a measurable document assistant with usage analytics.</p>
              <p>New remote roles will trigger approval-ready application packages.</p>
            </div>
          </section>
          <section className="rounded-md border border-line bg-white p-4">
            <div className="flex items-center gap-2">
              <Bell size={18} />
              <h2 className="font-semibold">Notifications</h2>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-ink/75">
              <li>Email: new high-fit jobs</li>
              <li>Push: interview invitations</li>
              <li>SMS: expiring opportunities</li>
            </ul>
          </section>
        </div>
      </section>

      <section id="pipeline" className="border-y border-line bg-white">
        <div className="mx-auto max-w-7xl px-5 py-8">
          <div className="mb-4 flex items-center gap-2">
            <KanbanSquare size={20} />
            <h2 className="text-xl font-semibold">Application Tracker</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {stages.map((stage, index) => (
              <div key={stage} className="min-h-32 rounded-md border border-line bg-paper p-3">
                <p className="text-sm font-semibold">{stage}</p>
                <p className="mt-3 text-2xl font-semibold text-moss">{[8, 14, 5, 7, 1, 1][index]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="analytics" className="mx-auto max-w-7xl px-5 py-8">
        <div className="mb-4 flex items-center gap-2">
          <ChartNoAxesCombined size={20} />
          <h2 className="text-xl font-semibold">Analytics Dashboard</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          <StatCard label="Conversion" value="19.4%" detail="Interview rate" />
          <StatCard label="Resume Lift" value="+31" detail="ATS score change" />
          <StatCard label="Market Skill" value="RAG" detail="Fastest rising keyword" />
          <StatCard label="Salary Signal" value="$142k" detail="Median target range" />
        </div>
      </section>
    </main>
  );
}
