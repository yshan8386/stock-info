import type { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`rounded-md border border-line bg-panel p-5 shadow-sm shadow-line/40 ${className}`} {...props} />;
}
