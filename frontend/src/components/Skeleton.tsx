"use client";

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-3 w-1/4" />
      <div className="space-y-2 mt-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
      <div className="flex gap-1 mt-2">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
    </div>
  );
}

export function StoryboardSkeleton() {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-4 w-1/3 mt-2" />
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-3 w-1/4 mt-2" />
          <div className="mt-3 space-y-2">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
