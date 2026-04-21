type LoadingBarProps = {
  active: boolean;
  label?: string;
};

export function LoadingBar({ active, label = "처리 중입니다" }: LoadingBarProps) {
  if (!active) return null;

  return (
    <div className="space-y-2">
      <div className="h-2 overflow-hidden rounded-md bg-accentSoft">
        <div className="h-full w-1/3 animate-[loading-bar_1.2s_ease-in-out_infinite] rounded-md bg-accent" />
      </div>
      <p className="text-sm text-muted">{label}</p>
    </div>
  );
}
