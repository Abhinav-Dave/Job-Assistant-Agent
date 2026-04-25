"use client";

import { useEffect, useMemo, useState } from "react";
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
  const {
    profile,
    authLoading,
    dataLoading,
    globalError,
    profileSaveState,
    resumeFile,
    updateProfileField,
    updateWorkHistoryItem,
    addWorkHistoryItem,
    deleteWorkHistoryItem,
    updateEducationItem,
    addEducationItem,
    deleteEducationItem,
    setResumeFile,
    saveProfile,
  } = usePhase10App();
  const [editingWorkIds, setEditingWorkIds] = useState<Record<string, boolean>>({});
  const [editingEducationIds, setEditingEducationIds] = useState<Record<string, boolean>>({});
  const [workBulletsDraft, setWorkBulletsDraft] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!profile) {
      return;
    }
    setWorkBulletsDraft((current) => {
      const next = { ...current };
      for (const item of profile.work_history) {
        if (!(item.id in next)) {
          next[item.id] = item.bullets.join("\n");
        }
      }
      return next;
    });
  }, [profile]);

  const profileCompleteness = useMemo(() => {
    if (!profile) {
      return 0;
    }
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

  if (authLoading || dataLoading) {
    return (
      <main className="space-y-4 p-6 md:p-8">
        <h1 className="text-2xl font-semibold text-slate-900">Profile Editor</h1>
        <p className="text-sm text-slate-600">Loading authenticated profile...</p>
      </main>
    );
  }

  if (!profile) {
    return (
      <main className="space-y-4 p-6 md:p-8">
        <h1 className="text-2xl font-semibold text-slate-900">Profile Editor</h1>
        <p className="text-sm text-rose-700">
          {globalError ?? "Profile is unavailable. Please log in and try again."}
        </p>
      </main>
    );
  }

  return (
    <main className="space-y-6 p-6 md:p-8">
      <header className="space-y-3 rounded-xl border border-slate-200 bg-gradient-to-r from-white to-slate-100 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className="bg-indigo-100 text-indigo-800">Profile</Badge>
          <Badge className="bg-slate-100 text-slate-700">
            Source: `GET /api/users/me`
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
          For Workday phone country-code fields, ensure your phone starts with `+1` (or your country
          code) before saving.
        </p>
        <div className="rounded-md border border-slate-200 p-3">
          <p className="text-sm font-medium text-slate-700">Resume file (required for scoring jobs)</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setResumeFile(file);
              }}
            />
            {resumeFile ? (
              <span className="text-xs text-slate-600">Selected: {resumeFile.name}</span>
            ) : (
              <span className="text-xs text-slate-500">No resume selected yet.</span>
            )}
          </div>
        </div>
      </Card>

      <Card className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={() => void saveProfile()}
            disabled={profileSaveState.isSaving}
          >
            {profileSaveState.isSaving ? "Saving..." : "Save profile to backend"}
          </button>
          {profileSaveState.error ? (
            <p className="text-sm text-rose-700">{profileSaveState.error}</p>
          ) : (
            <p className="text-xs text-slate-500">
              Persists core fields via `PATCH /api/users/me`.
            </p>
          )}
        </div>
      </Card>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
              Work Experience
            </h2>
            <div className="flex items-center gap-2">
              <Badge className="bg-slate-100 text-slate-700">{profile.work_history.length} entries</Badge>
              <button
                type="button"
                className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100"
                onClick={addWorkHistoryItem}
              >
                Add entry
              </button>
            </div>
          </div>
          {profile.work_history.map((item) => (
            <article key={item.id} className="rounded-md border border-slate-200 p-3">
              {(editingWorkIds[item.id] ?? false) ? (
                <>
                  <div className="grid gap-2 md:grid-cols-2">
                    <div>
                      <label className="text-xs text-slate-500">Role</label>
                      <Input
                        value={item.role}
                        onChange={(event) =>
                          updateWorkHistoryItem(item.id, "role", event.target.value)
                        }
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Company</label>
                      <Input
                        value={item.company}
                        onChange={(event) =>
                          updateWorkHistoryItem(item.id, "company", event.target.value)
                        }
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Start (YYYY-MM)</label>
                      <Input
                        value={item.start_date}
                        onChange={(event) =>
                          updateWorkHistoryItem(item.id, "start_date", event.target.value)
                        }
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">End (YYYY-MM or blank)</label>
                      <Input
                        value={item.end_date ?? ""}
                        onChange={(event) =>
                          updateWorkHistoryItem(
                            item.id,
                            "end_date",
                            event.target.value.trim() ? event.target.value : null
                          )
                        }
                      />
                    </div>
                  </div>
                  <label className="mt-3 block text-xs text-slate-500">Bullets (one per line)</label>
                  <Textarea
                    value={workBulletsDraft[item.id] ?? ""}
                    onChange={(event) =>
                      setWorkBulletsDraft((current) => ({
                        ...current,
                        [item.id]: event.target.value,
                      }))
                    }
                  />
                </>
              ) : (
                <div className="space-y-1 text-sm text-slate-700">
                  <p>
                    <span className="font-medium">{item.role || "Untitled role"}</span>{" "}
                    at {item.company || "Unknown company"}
                  </p>
                  <p className="text-xs text-slate-500">
                    {item.start_date || "Start n/a"} - {item.end_date || "Present"}
                  </p>
                  <ul className="list-disc pl-5">
                    {item.bullets.map((bullet, index) => (
                      <li key={`${item.id}-bullet-${index}`}>{bullet}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="mt-3 flex justify-end">
                {(editingWorkIds[item.id] ?? false) ? (
                  <button
                    type="button"
                    className="mr-2 rounded-md border border-emerald-300 px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50"
                    onClick={() => {
                      const draft = workBulletsDraft[item.id] ?? "";
                      updateWorkHistoryItem(item.id, "bullets", draft.split("\n"));
                      setEditingWorkIds((current) => ({ ...current, [item.id]: false }));
                    }}
                  >
                    Save entry
                  </button>
                ) : (
                  <button
                    type="button"
                    className="mr-2 rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                    onClick={() => {
                      setWorkBulletsDraft((current) => ({
                        ...current,
                        [item.id]: item.bullets.join("\n"),
                      }));
                      setEditingWorkIds((current) => ({ ...current, [item.id]: true }));
                    }}
                  >
                    ✏ Edit
                  </button>
                )}
                <button
                  type="button"
                  className="rounded-md border border-rose-300 px-2 py-1 text-xs text-rose-700 hover:bg-rose-50"
                  onClick={() => deleteWorkHistoryItem(item.id)}
                >
                  🗑 Delete
                </button>
              </div>
            </article>
          ))}
          {profile.work_history.length === 0 && (
            <p className="text-sm text-slate-500">No work experience added yet.</p>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Education</h2>
            <div className="flex items-center gap-2">
              <Badge className="bg-slate-100 text-slate-700">{profile.education.length} entries</Badge>
              <button
                type="button"
                className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100"
                onClick={addEducationItem}
              >
                Add entry
              </button>
            </div>
          </div>
          {profile.education.map((item) => (
            <article key={item.id} className="rounded-md border border-slate-200 p-3">
              {(editingEducationIds[item.id] ?? false) ? (
                <div className="grid gap-2 md:grid-cols-2">
                  <div>
                    <label className="text-xs text-slate-500">Institution</label>
                    <Input
                      value={item.institution}
                      onChange={(event) =>
                        updateEducationItem(item.id, "institution", event.target.value)
                      }
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">Degree</label>
                    <Input
                      value={item.degree}
                      onChange={(event) => updateEducationItem(item.id, "degree", event.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">Field of study</label>
                    <Input
                      value={item.field_of_study ?? ""}
                      onChange={(event) =>
                        updateEducationItem(
                          item.id,
                          "field_of_study",
                          event.target.value.trim() ? event.target.value : null
                        )
                      }
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">Graduation year</label>
                    <Input
                      value={item.graduation_year ?? ""}
                      onChange={(event) =>
                        updateEducationItem(
                          item.id,
                          "graduation_year",
                          event.target.value.trim() ? Number(event.target.value) : null
                        )
                      }
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">GPA</label>
                    <Input
                      value={item.gpa ?? ""}
                      onChange={(event) =>
                        updateEducationItem(
                          item.id,
                          "gpa",
                          event.target.value.trim() ? event.target.value : null
                        )
                      }
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-1 text-sm text-slate-700">
                  <p>
                    <span className="font-medium">{item.degree || "Degree"}</span> —{" "}
                    {item.institution || "Institution"}
                  </p>
                  <p className="text-xs text-slate-500">
                    {item.field_of_study || "Field n/a"} • {item.graduation_year || "Year n/a"} • GPA{" "}
                    {item.gpa || "n/a"}
                  </p>
                </div>
              )}
              <div className="mt-3 flex justify-end">
                {(editingEducationIds[item.id] ?? false) ? (
                  <button
                    type="button"
                    className="mr-2 rounded-md border border-emerald-300 px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50"
                    onClick={() =>
                      setEditingEducationIds((current) => ({ ...current, [item.id]: false }))
                    }
                  >
                    Save entry
                  </button>
                ) : (
                  <button
                    type="button"
                    className="mr-2 rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                    onClick={() =>
                      setEditingEducationIds((current) => ({ ...current, [item.id]: true }))
                    }
                  >
                    ✏ Edit
                  </button>
                )}
                <button
                  type="button"
                  className="rounded-md border border-rose-300 px-2 py-1 text-xs text-rose-700 hover:bg-rose-50"
                  onClick={() => deleteEducationItem(item.id)}
                >
                  🗑 Delete
                </button>
              </div>
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
