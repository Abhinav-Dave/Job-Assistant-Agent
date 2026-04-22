import type {
  AutofillResultPayload,
  JobApplication,
  UserProfile,
} from "@/types";

export const mockProfile: UserProfile = {
  id: "user-1",
  email: "jane@example.com",
  full_name: "Jane Smith",
  phone: "+1 416-555-0100",
  location: "Toronto, ON",
  address_line1: "123 Example Street",
  address_line2: "Unit 7",
  city: "Toronto",
  province: "Ontario",
  country: "Canada",
  postal_code: "A1A 1A1",
  linkedin_url: "https://linkedin.com/in/janesmith",
  portfolio_url: "https://github.com/janesmith",
  skills: ["Python", "FastAPI", "PostgreSQL", "Docker", "React"],
  preferences: {
    desired_roles: ["Backend Engineer", "Full Stack Engineer"],
    target_industries: ["SaaS", "AI Tooling"],
    remote_preference: "hybrid",
    salary_min: 110000,
  },
  work_history: [
    {
      id: "work-1",
      company: "Acme Corp",
      role: "Software Engineer",
      start_date: "2022-01",
      end_date: null,
      is_current: true,
      bullets: ["Built APIs", "Reduced latency by 25%"],
      display_order: 0,
    },
    {
      id: "work-2",
      company: "Cloud Orbit",
      role: "Backend Developer Intern",
      start_date: "2021-05",
      end_date: "2021-12",
      is_current: false,
      bullets: [
        "Implemented service health probes across internal APIs.",
        "Automated monthly report generation with Python pipelines.",
      ],
      display_order: 1,
    },
  ],
  education: [
    {
      id: "edu-1",
      institution: "University of Toronto",
      degree: "Bachelor of Science",
      field_of_study: "Computer Science",
      graduation_year: 2021,
      gpa: "3.8",
      display_order: 0,
    },
    {
      id: "edu-2",
      institution: "Coursera / DeepLearning.AI",
      degree: "Certificate",
      field_of_study: "Machine Learning Specialization",
      graduation_year: 2023,
      gpa: null,
      display_order: 1,
    },
  ],
  onboarding_complete: true,
};

export const mockApplications: JobApplication[] = [
  {
    id: "app-1",
    company: "Northstar AI",
    role: "Backend Engineer",
    source_url: "https://jobs.northstar.ai/jobs/123",
    status: "interviewing",
    updated_at: "2026-04-22T08:45:00Z",
    notes: "Recruiter screen completed; awaiting technical loop.",
    history: [
      {
        id: "hist-1",
        status: "saved",
        note: "Saved from dashboard",
        created_at: "2026-04-18T12:00:00Z",
      },
      {
        id: "hist-2",
        status: "applied",
        note: "Applied via company portal",
        created_at: "2026-04-19T16:20:00Z",
      },
      {
        id: "hist-3",
        status: "interviewing",
        note: "Recruiter intro done",
        created_at: "2026-04-21T09:00:00Z",
      },
    ],
  },
  {
    id: "app-2",
    company: "Vector Labs",
    role: "Platform Engineer",
    source_url: "https://careers.vectorlabs.dev/openings/89",
    status: "applied",
    updated_at: "2026-04-21T13:10:00Z",
    notes: "No response yet.",
    history: [
      {
        id: "hist-4",
        status: "saved",
        note: "Saved from referral list",
        created_at: "2026-04-20T11:15:00Z",
      },
      {
        id: "hist-5",
        status: "applied",
        note: "Submitted with tailored resume",
        created_at: "2026-04-20T18:40:00Z",
      },
    ],
  },
  {
    id: "app-3",
    company: "Atlas Health",
    role: "Software Engineer II",
    source_url: "https://jobs.atlashealth.com/positions/se2",
    status: "saved",
    updated_at: "2026-04-22T05:30:00Z",
    notes: "Need to customize project examples before applying.",
    history: [
      {
        id: "hist-6",
        status: "saved",
        note: "Imported from scraping queue",
        created_at: "2026-04-22T05:30:00Z",
      },
    ],
  },
];

export const mockAutofillSuccess: AutofillResultPayload = {
  page_url: "https://jobs.northstar.ai/jobs/123/apply",
  total_fields: 11,
  mapped_fields: 8,
  fill_rate: 0.73,
  mappings: [
    {
      field_id: "first_name",
      field_label: "First Name",
      profile_key: "full_name:first",
      suggested_value: "Jane",
      confidence: 0.95,
      action: "auto_fill",
    },
    {
      field_id: "last_name",
      field_label: "Last Name",
      profile_key: "full_name:last",
      suggested_value: "Smith",
      confidence: 0.95,
      action: "auto_fill",
    },
    {
      field_id: "email",
      field_label: "Email",
      profile_key: "email",
      suggested_value: "jane@example.com",
      confidence: 0.95,
      action: "auto_fill",
    },
    {
      field_id: "phone",
      field_label: "Phone",
      profile_key: "phone",
      suggested_value: "+1 416-555-0100",
      confidence: 0.9,
      action: "auto_fill",
    },
    {
      field_id: "address1",
      field_label: "Address Line 1",
      profile_key: "address_line1",
      suggested_value: "123 Example Street",
      confidence: 0.9,
      action: "auto_fill",
    },
    {
      field_id: "postal",
      field_label: "Postal Code",
      profile_key: "postal_code",
      suggested_value: "A1A 1A1",
      confidence: 0.89,
      action: "auto_fill",
    },
    {
      field_id: "linkedin",
      field_label: "LinkedIn URL",
      profile_key: "linkedin_url",
      suggested_value: "https://linkedin.com/in/janesmith",
      confidence: 0.91,
      action: "auto_fill",
    },
    {
      field_id: "portfolio",
      field_label: "Portfolio",
      profile_key: "portfolio_url",
      suggested_value: "https://github.com/janesmith",
      confidence: 0.69,
      action: "suggest",
    },
  ],
  unfilled_fields: ["Work Authorization", "Resume Upload", "Why this company?"],
  diagnostic: "low_confidence",
  diagnostic_detail:
    "Some mappings are suggestions only. Confirm values before extension execution.",
};

export const mockAutofillNoFields: AutofillResultPayload = {
  page_url: "https://jobs.blocked.example/apply",
  total_fields: 0,
  mapped_fields: 0,
  fill_rate: 0,
  mappings: [],
  unfilled_fields: [],
  diagnostic: "no_fields_detected",
  diagnostic_detail:
    "No form fields were detected. This can happen on auth-gated or script-heavy pages.",
};

export const mockAutofillAtsNotReady: AutofillResultPayload = {
  page_url: "https://workday.example/careers/job/apply",
  total_fields: 2,
  mapped_fields: 0,
  fill_rate: 0,
  mappings: [],
  unfilled_fields: ["Application form fields not yet available"],
  diagnostic: "ats_page_not_ready",
  diagnostic_detail:
    "ATS appears to require additional in-browser steps (Apply/Continue) before fields are ready.",
};
