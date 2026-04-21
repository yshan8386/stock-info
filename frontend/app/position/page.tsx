import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";

export default function PositionPage() {
  return (
    <Card className="mx-auto max-w-2xl text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-md bg-infoSoft text-info">
        <Icon name="briefcase" className="h-8 w-8" />
      </div>
      <h1 className="mt-6 text-2xl font-bold">투자 현황은 준비 중입니다</h1>
      <div className="mt-6 grid gap-3 text-left text-muted">
        <p>포트폴리오 조회</p>
        <p>보유 종목 시세 확인</p>
        <p>거래 기록과 매매 일지</p>
        <p>수익률 추이 차트</p>
      </div>
    </Card>
  );
}
