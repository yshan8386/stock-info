import { Card } from "@/components/ui/Card";

export default function ProfileSettingsPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">프로필 설정</h1>
      <Card className="text-muted">프로필 변경과 비밀번호 변경은 다음 단계에서 연결합니다.</Card>
    </div>
  );
}

