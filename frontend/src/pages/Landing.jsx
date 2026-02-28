import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import { loginUser, registerUser } from "@/services/authApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  MessageSquare,
  FileText,
  ShieldCheck,
  BarChart3,
  Zap,
} from "lucide-react";
import { toast } from "sonner";

// ── Zod schemas ──────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

const registerSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Enter a valid email"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
    role: z.enum(["customer", "agent", "admin"]).default("customer"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

// ── Feature data ─────────────────────────────────────────────

const features = [
  {
    icon: MessageSquare,
    title: "AI-Powered Chat",
    description: "Instant answers from your knowledge base using RAG.",
  },
  {
    icon: FileText,
    title: "Source Transparency",
    description: "Every response cites the exact document and page.",
  },
  {
    icon: ShieldCheck,
    title: "Smart Escalation",
    description: "Low-confidence queries auto-route to human agents.",
  },
  {
    icon: BarChart3,
    title: "Analytics",
    description: "Query trends, confidence metrics, and more.",
  },
];

// ── Sign-in form ─────────────────────────────────────────────

function SignInForm() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(loginSchema) });

  const mutation = useMutation({
    mutationFn: ({ email, password }) => loginUser(email, password),
    onSuccess: (data) => {
      login(data.access_token, data.user);
      toast.success("Welcome back!");
      const role = data.user.role;
      navigate(role === "admin" ? "/admin" : role === "agent" ? "/agent" : "/chat");
    },
    onError: (err) =>
      toast.error(err.response?.data?.detail || "Login failed"),
  });

  return (
    <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="login-email">Email</Label>
        <Input id="login-email" type="email" placeholder="you@example.com" {...register("email")} />
        {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="login-password">Password</Label>
        <Input id="login-password" type="password" placeholder="••••••••" {...register("password")} />
        {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
      </div>
      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending ? "Signing in…" : "Sign In"}
      </Button>
    </form>
  );
}

// ── Register form ────────────────────────────────────────────

function RegisterForm({ onSuccess }) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({ resolver: zodResolver(registerSchema), defaultValues: { role: "customer" } });

  const selectedRole = watch("role");

  const mutation = useMutation({
    mutationFn: ({ name, email, password, role }) => registerUser(name, email, password, role),
    onSuccess: () => {
      toast.success("Account created! Sign in to continue.");
      onSuccess?.();
    },
    onError: (err) =>
      toast.error(err.response?.data?.detail || "Registration failed"),
  });

  return (
    <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="reg-name">Full Name</Label>
        <Input id="reg-name" placeholder="John Doe" {...register("name")} />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-email">Email</Label>
        <Input id="reg-email" type="email" placeholder="you@example.com" {...register("email")} />
        {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-password">Password</Label>
        <Input id="reg-password" type="password" placeholder="••••••••" {...register("password")} />
        {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-confirm">Confirm Password</Label>
        <Input id="reg-confirm" type="password" placeholder="••••••••" {...register("confirmPassword")} />
        {errors.confirmPassword && (
          <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="reg-role">Role</Label>
        <Select value={selectedRole} onValueChange={(v) => setValue("role", v)}>
          <SelectTrigger id="reg-role" className="w-full">
            <SelectValue placeholder="Select a role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="customer">Customer</SelectItem>
            <SelectItem value="agent">Agent</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-[11px] text-muted-foreground">For demo/testing — production would restrict this</p>
      </div>
      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending ? "Creating account…" : "Create Account"}
      </Button>
    </form>
  );
}

// ── Landing page ─────────────────────────────────────────────

export default function Landing() {
  const location = useLocation();
  const defaultTab = location.pathname === "/register" ? "register" : "signin";
  const [tab, setTab] = useState(defaultTab);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Navbar ── */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <a href="/" className="flex items-center gap-2 font-semibold">
            <MessageSquare className="h-5 w-5 text-primary" />
            <span>SupportIQ</span>
          </a>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setTab("signin");
                document.getElementById("auth-section")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Sign In
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setTab("register");
                document.getElementById("auth-section")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* ── Hero + Auth side-by-side ── */}
      <section className="flex flex-1 items-center px-4 py-16 lg:py-24">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-12 lg:grid-cols-2 lg:gap-20">
          {/* Left — copy */}
          <div className="order-2 lg:order-1">
            <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
              Customer Support,{" "}
              <span className="text-primary">Supercharged&nbsp;by&nbsp;AI</span>
            </h1>
            <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
              SupportIQ uses Retrieval-Augmented Generation to deliver instant,
              accurate, source-backed answers from your documents — with
              seamless human fallback when needed.
            </p>
            <div className="mt-10 grid grid-cols-2 gap-4">
              {features.map(({ icon: Icon, title, description }) => (
                <div key={title} className="flex gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — auth card */}
          <div className="order-1 lg:order-2" id="auth-section">
            <Card className="mx-auto w-full max-w-md shadow-lg">
              <CardHeader className="text-center pb-2">
                <div className="mx-auto mb-2 flex h-11 w-11 items-center justify-center rounded-full bg-primary">
                  <MessageSquare className="h-5 w-5 text-primary-foreground" />
                </div>
                <CardTitle className="text-xl">Welcome to SupportIQ</CardTitle>
                <CardDescription>
                  {tab === "signin"
                    ? "Sign in to your account"
                    : "Create a new account to get started"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={tab} onValueChange={setTab}>
                  <TabsList className="mb-4 w-full">
                    <TabsTrigger value="signin" className="flex-1">
                      Sign In
                    </TabsTrigger>
                    <TabsTrigger value="register" className="flex-1">
                      Register
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="signin">
                    <SignInForm />
                  </TabsContent>
                  <TabsContent value="register">
                    <RegisterForm onSuccess={() => setTab("signin")} />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t py-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} SupportIQ &mdash; University capstone project
          </p>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Zap className="h-3 w-3" />
            Powered by RAG
          </div>
        </div>
      </footer>
    </div>
  );
}
