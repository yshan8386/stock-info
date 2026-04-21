import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export function Button({ className = "", variant = "primary", ...props }: ButtonProps) {
  const styles =
    variant === "primary"
      ? "bg-text text-white shadow-sm hover:bg-accent"
      : "border border-line bg-panel text-text hover:border-accent hover:bg-accentSoft";
  return (
    <button
      className={`rounded-md px-4 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${className}`}
      {...props}
    />
  );
}
