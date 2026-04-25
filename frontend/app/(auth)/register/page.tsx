"use client";

import Link from "next/link";
import { useState } from "react";
import { supabase } from "@/lib/supabase";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });
    if (error) {
      setErrorMessage(error.message);
      setIsSubmitting(false);
      return;
    }
    setSuccessMessage(
      "Registration submitted. Verify your email if required, then sign in to continue."
    );
    setIsSubmitting(false);
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center p-6">
      <div className="w-full space-y-4 rounded-xl border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-semibold">Register</h1>
        <p className="text-sm text-slate-600">
          Create an account to connect profile data with mapping preview and extension execution.
        </p>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <label className="block space-y-1 text-sm text-slate-700">
            <span>Full name</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              required
            />
          </label>
          <label className="block space-y-1 text-sm text-slate-700">
            <span>Email</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="block space-y-1 text-sm text-slate-700">
            <span>Password</span>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>
        {errorMessage ? <p className="text-sm text-rose-700">{errorMessage}</p> : null}
        {successMessage ? <p className="text-sm text-emerald-700">{successMessage}</p> : null}
        <p className="text-sm text-slate-600">
          Already have an account?{" "}
          <Link className="text-blue-700 underline" href="/login">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
