import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

/** Skeleton for a row of metric cards (e.g., dashboard overview). */
export function MetricCardsSkeleton({ count = 4 }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-4 rounded-full" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-16" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** Skeleton for a data table (e.g., documents, tickets). */
export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <div className="rounded-md border">
      {/* Header */}
      <div className="flex items-center gap-4 border-b px-4 py-3">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex items-center gap-4 border-b px-4 py-3 last:border-0">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Skeleton for a chat message list. */
export function ChatSkeleton({ messages = 4 }) {
  return (
    <div className="flex flex-col gap-4 p-4">
      {Array.from({ length: messages }).map((_, i) => (
        <div
          key={i}
          className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"}`}
        >
          <div className={`flex max-w-[70%] flex-col gap-2 ${i % 2 === 0 ? "items-end" : "items-start"}`}>
            <Skeleton className="h-4 w-20" />
            <Skeleton className={`h-16 ${i % 2 === 0 ? "w-48" : "w-64"} rounded-lg`} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Full-page centered spinner. */
export function PageSpinner() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );
}
