import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  MessageSquare,
  FileText,
  ShieldCheck,
  BarChart3,
  Zap,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "AI-Powered Chat",
    description:
      "Get instant answers from your knowledge base using advanced RAG technology.",
  },
  {
    icon: FileText,
    title: "Source Transparency",
    description:
      "Every response includes document references so you know exactly where answers come from.",
  },
  {
    icon: ShieldCheck,
    title: "Smart Escalation",
    description:
      "Low-confidence queries are automatically routed to human agents for review.",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    description:
      "Track query trends, confidence metrics, and escalation rates in real time.",
  },
];

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* ── Navbar ──────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <MessageSquare className="h-5 w-5 text-primary" />
            <span>SupportIQ</span>
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link to="/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="flex flex-1 flex-col items-center justify-center px-4 py-20 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-6">
          <Zap className="h-8 w-8 text-primary" />
        </div>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          Customer Support,{" "}
          <span className="text-primary">Supercharged by AI</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
          SupportIQ uses Retrieval-Augmented Generation to deliver instant,
          accurate, source-backed answers from your documents — with seamless
          human fallback when needed.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Button size="lg" asChild>
            <Link to="/register">
              Start Free <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link to="/login">Sign In</Link>
          </Button>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────── */}
      <section className="border-t bg-muted/40 py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            Everything you need for smarter support
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted-foreground">
            Upload your documents, let AI handle the repetitive queries, and
            focus your agents on what matters.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="flex flex-col items-center rounded-xl border bg-background p-6 text-center shadow-sm"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer className="border-t py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} SupportIQ. Built as a university
            capstone project.
          </p>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Zap className="h-3.5 w-3.5" />
            Powered by RAG
          </div>
        </div>
      </footer>
    </div>
  );
}
