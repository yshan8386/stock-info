import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function Input({ label, error, className = "", ...props }: InputProps) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-muted">{label}</span>
      <input
        className={`w-full rounded-md border border-line bg-white px-3 py-3 text-text outline-none transition placeholder:text-muted/70 focus:border-accent focus:ring-2 focus:ring-accentSoft ${className}`}
        {...props}
      />
      {error ? <span className="mt-1 block text-sm text-red-600">{error}</span> : null}
    </label>
  );
}
