import type { ReactNode, SVGProps } from "react";

type IconName =
  | "home"
  | "newspaper"
  | "chart"
  | "briefcase"
  | "book"
  | "settings"
  | "construction"
  | "technical"
  | "performance"
  | "fundamental"
  | "trading"
  | "strategy"
  | "arrowRight";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
};

const paths: Record<IconName, ReactNode> = {
  home: (
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
      <path d="M9 21v-7h6v7" />
    </>
  ),
  newspaper: (
    <>
      <path d="M4 5h13a3 3 0 0 1 3 3v11H7a3 3 0 0 1-3-3z" />
      <path d="M7 8h7" />
      <path d="M7 12h10" />
      <path d="M7 16h6" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20V4" />
      <path d="M4 20h16" />
      <path d="M8 16v-5" />
      <path d="M12 16V7" />
      <path d="M16 16v-3" />
    </>
  ),
  briefcase: (
    <>
      <path d="M9 7V5h6v2" />
      <path d="M4 8h16v11H4z" />
      <path d="M4 13h16" />
      <path d="M10 13v2h4v-2" />
    </>
  ),
  book: (
    <>
      <path d="M5 4h10a4 4 0 0 1 4 4v12H9a4 4 0 0 0-4-4z" />
      <path d="M5 4v16" />
      <path d="M9 8h6" />
      <path d="M9 12h5" />
    </>
  ),
  settings: (
    <>
      <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z" />
      <path d="M12 2v3" />
      <path d="M12 19v3" />
      <path d="m4.9 4.9 2.1 2.1" />
      <path d="m17 17 2.1 2.1" />
      <path d="M2 12h3" />
      <path d="M19 12h3" />
      <path d="m4.9 19.1 2.1-2.1" />
      <path d="m17 7 2.1-2.1" />
    </>
  ),
  construction: (
    <>
      <path d="M4 19h16" />
      <path d="M7 19V9l5-4 5 4v10" />
      <path d="M9 19v-5h6v5" />
      <path d="M9 10h6" />
    </>
  ),
  technical: (
    <>
      <path d="M4 17 10 7l4 6 2-3 4 7" />
      <path d="M4 21h16" />
    </>
  ),
  performance: (
    <>
      <path d="M4 18V6" />
      <path d="M4 18h16" />
      <path d="m7 14 3-3 3 2 5-6" />
    </>
  ),
  fundamental: (
    <>
      <path d="M6 4h12v16H6z" />
      <path d="M9 8h6" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </>
  ),
  trading: (
    <>
      <path d="M7 7h11l-3-3" />
      <path d="M17 17H6l3 3" />
      <path d="M18 7 6 19" />
    </>
  ),
  strategy: (
    <>
      <path d="M12 3v18" />
      <path d="M5 8h14" />
      <path d="M7 8l-2 5h6z" />
      <path d="M17 8l-2 5h6z" />
    </>
  ),
  arrowRight: (
    <>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </>
  )
};

export function Icon({ name, className = "", ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      height="24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 24 24"
      width="24"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}

export function glossaryIconName(slug: string | null | undefined): IconName {
  if (slug === "technical") return "technical";
  if (slug === "performance") return "performance";
  if (slug === "fundamental") return "fundamental";
  if (slug === "trading") return "trading";
  if (slug === "strategy") return "strategy";
  return "book";
}
