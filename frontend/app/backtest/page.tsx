import { Card } from "@/components/ui/Card";

export default function BacktestPage() {
  return (
    <Card className="mx-auto max-w-2xl text-center">
      <div className="text-5xl">🚧</div>
      <h1 className="mt-6 text-2xl font-bold">백테스트는 준비 중입니다</h1>
      <div className="mt-6 grid gap-3 text-left text-muted">
        <p>과거 데이터로 투자 전략 검증</p>
        <p>수익률, MDD, 샤프 비율 등 지표 제공</p>
        <p>여러 전략 비교</p>
        <p>결과 저장 및 공유</p>
      </div>
    </Card>
  );
}

