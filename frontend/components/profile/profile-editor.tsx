"use client";

import { useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { usePhase10App } from "@/context/phase10-app-context";
import type { UserProfile } from "@/types";

type EditableProfileKey =
  | "full_name"
  | "email"
  | "phone"
  | "linkedin_url"
  | "portfolio_url"
  | "address_line1"
  | "address_line2"
  | "city"
  | "province"
  | "country"
  | "postal_code"
  | "location";

interface EditableField {
  key: EditableProfileKey;
  label: string;
  placeholder?: string;
  multiline?: boolean;
}

const editableFields: EditableField[] = [
  { key: "full_name", label: "Full Name" },
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone Number" },
  { key: "linkedin_url", label: "LinkedIn URL" },
  { key: "portfolio_url", label: "Portfolio URL" },
  { key: "address_line1", label: "Address Line 1" },
  { key: "address_line2", label: "Address Line 2" },
  { key: "city", label: "City" },
  { key: "province", label: "Province / State" },
  { key: "country", label: "Country" },
  { key: "postal_code", label: "Postal / ZIP Code" },
  {
    key: "location",
    label: "Location Summary",
    placeholder: "Toronto, ON",
  },
];

const progressWidthClassByStep: Record<number, string> = {
  0: "w-0",
  5: "w-[5%]",
  10: "w-[10%]",
  15: "w-[15%]",
  20: "w-[20%]",
  25: "w-1/4",
  30: "w-[30%]",
  35: "w-[35%]",
  40: "w-2/5",
  45: "w-[45%]",
  50: "w-1/2",
  55: "w-[55%]",
  60: "w-3/5",
  65: "w-[65%]",
  70: "w-[70%]",
  75: "w-3/4",
  80: "w-4/5",
  85: "w-[85%]",
  90: "w-[90%]",
  95: "w-[95%]",
  100: "w-full",
};

export function ProfileEditor() {
  const { profile, updateProfileField } = usePhase10App();

  const profileCompleteness = useMemo(() => {
    const requiredKeys: Array<keyof typeof profile> = [
      "full_name",
      "email",
      "phone",
      "address_line1",
      "city",
      "province",
      "country",
      "postal_code",
      "linkedin_url",
    ];
    const filled = requiredKeys.filter((key) => {
      const value = profile[key];
      return typeof value === "string" ? value.trim().length > 0 : value !== null;
    });
    return Math.round((filled.length / requiredKeys.length) * 100);
  }, [profile]);

  const progressWidthClass = useMemo(() => {
    const clamped = Math.min(100, Math.max(0, profileCompleteness));
    const stepped = Math.round(clamped / 5) * 5;
    return progressWidthClassByStep[stepped] ?? "w-0";
  }, [profileCompleteness]);

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-3 rounded-xl border border-slate-200 bg-gradient-to-r from-white to-slate-100 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className="bg-indigo-100 text-indigo-800">Phase 10 Static Preview</Badge>
          <Badge className="bg-slate-100 text-slate-700">
            Phase 11 source: backend private profile on login
          </Badge>
        </div>
        <h1 className="text-2xl font-semibold text-slate-900">Profile Editor & Onboarding</h1>
        <p className="text-sm leading-6 text-slate-600">
          Update core profile fields used for mapping suggestions. Work experience and education are
          displayed below because they are critical for long-form application autofill.
        </p>
      </header>

      <Card className="space-y-2">
        <p className="text-sm font-medium text-slate-700">Profile readiness</p>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
          <div className={`h-full rounded-full bg-emerald-500 transition-all ${progressWidthClass}`} />
        </div>
        <p className="text-sm text-slate-600">{profileCompleteness}% of core autofill fields configured.</p>
      </Card>

      <section className="grid gap-4 md:grid-cols-2">
        {editableFields.map((field) => {
          const value = profile[field.key] as UserProfile[EditableProfileKey];
          const normalizedValue = value ?? "";
          return (
            <Card key={field.key.toString()} className="space-y-2">
              <label className="text-sm font-medium text-slate-700" htmlFor={field.key.toString()}>
                {field.label}
              </label>
              {field.multiline ? (
                <Textarea
                  id={field.key.toString()}
                  value={normalizedValue}
                  placeholder={field.placeholder}
                  onChange={(event) => updateProfileField(field.key, event.target.value)}
                />
              ) : (
                <Input
                  id={field.key.toString()}
                  value={normalizedValue}
                  placeholder={field.placeholder}
                  onChange={(event) => updateProfileField(field.key, event.target.value)}
                />
              )}
            </Card>
          );
        })}
      </section>

      <Card className="space-y-3">
        <p className="text-sm font-medium text-slate-700">Skills</p>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill) => (
            <Badge key={skill}>{skill}</Badge>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          Skills editing remains read-only in Phase 10 static mode. It becomes API-backed in Phase 11.
        </p>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
              Work Experience
            </h2>
            <Badge className="bg-slate-100 text-slate-700">{profile.work_history.length} entries</Badge>
          </div>
          {profile.work_history.map((item) => (
            <article key={item.id} className="rounded-md border border-slate-200 p-3">
              <p className="text-sm font-semibold text-slate-900">{item.role}</p>
              <p className="text-sm text-slate-600">{item.company}</p>
              <p className="text-xs text-slate-500">
                {item.start_date} - {item.is_current ? "Present" : item.end_date ?? "N/A"}
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
                {item.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            </article>
          ))}
          {profile.work_history.length === 0 && (
            <p className="text-sm text-slate-500">No work experience added yet.</p>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Education</h2>
            <Badge className="bg-slate-100 text-slate-700">{profile.education.length} entries</Badge>
          </div>
          {profile.education.map((item) => (
            <article key={item.id} className="rounded-md border border-slate-200 p-3">
              <p className="text-sm font-semibold text-slate-900">{item.institution}</p>
              <p className="text-sm text-slate-600">
                {item.degree} — {item.field_of_study}
              </p>
              <p className="text-xs text-slate-500">
                Graduation: {item.graduation_year ?? "N/A"} {item.gpa ? `• GPA ${item.gpa}` : ""}
              </p>
            </article>
          ))}
          {profile.education.length === 0 && (
            <p className="text-sm text-slate-500">No education entries added yet.</p>
          )}
        </Card>
      </section>
    </main>
  );
}
