import Link from "next/link";

export default function HomePage() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-semibold">AI Job Application Assistant</h1>
      <p className="mt-2 text-muted-foreground text-slate-600">
        Scaffold — wire auth redirect (PRD): logged in → /dashboard, else → /login.
      </p>
      <ul className="mt-6 list-disc pl-6 space-y-2">
        <li>
          <Link className="text-blue-600 underline" href="/login">
            /login
          </Link>
        </li>
        <li>
          <Link className="text-blue-600 underline" href="/register">
            /register
          </Link>
        </li>
        <li>
          <Link className="text-blue-600 underline" href="/dashboard">
            /dashboard
          </Link>{" "}
          (protected)
        </li>
      </ul>
    </main>
  );
}
