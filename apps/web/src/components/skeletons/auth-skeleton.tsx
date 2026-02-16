"use client";

import { Skeleton } from "@/components/ui/skeleton";

export function AuthSkeleton() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background/70 to-background px-6 py-12">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_minmax(320px,420px)]">
        <section className="space-y-8">
          <div className="flex flex-wrap gap-3">
            <Skeleton className="h-10 w-48 rounded-full" />
            <Skeleton className="h-10 w-32 rounded-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-2/3" />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="space-y-3 rounded-xl border border-dashed p-4">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            ))}
          </div>
        </section>
        <div className="relative flex w-full items-center justify-center px-2 py-8 sm:px-6">
          <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card/60 p-8 shadow-lg backdrop-blur">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <div className="space-y-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      </div>
    </div>
  );
}
