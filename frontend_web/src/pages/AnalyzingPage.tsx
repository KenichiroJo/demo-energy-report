import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, FileText, TrendingUp, Shield, Loader2 } from 'lucide-react';

const ANALYSIS_STEPS = [
  { icon: BarChart3, label: '財務データを分析中...', detail: 'セグメント別売上・利益推移' },
  { icon: TrendingUp, label: 'SFAパイプラインを分析中...', detail: '案件進捗・着地見込み' },
  { icon: FileText, label: '社内文書を検索中...', detail: '事業計画・議事録・報告書' },
  { icon: Shield, label: 'リスクと機会を評価中...', detail: '統合的なリスク分析' },
] as const;

export function AnalyzingPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    ANALYSIS_STEPS.forEach((_, index) => {
      // ステップ開始
      timers.push(
        setTimeout(() => {
          setCurrentStep(index);
        }, index * 1200),
      );
      // ステップ完了
      timers.push(
        setTimeout(() => {
          setCompletedSteps((prev) => [...prev, index]);
        }, index * 1200 + 900),
      );
    });

    // 全ステップ完了後にレポートページへ遷移
    timers.push(
      setTimeout(() => {
        navigate('/report', { replace: true });
      }, ANALYSIS_STEPS.length * 1200 + 400),
    );

    return () => timers.forEach(clearTimeout);
  }, [navigate]);

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-6">
      <div className="w-full max-w-md space-y-8 text-center">
        {/* Spinning icon */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10">
          <Loader2 className="h-8 w-8 text-accent animate-spin" />
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold tracking-tight">経営レポートを生成中</h1>
          <p className="text-sm text-muted-foreground">
            AIがデータを多角的に分析しています...
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-3 text-left">
          {ANALYSIS_STEPS.map((step, index) => {
            const isCompleted = completedSteps.includes(index);
            const isCurrent = currentStep === index && !isCompleted;

            return (
              <div
                key={step.label}
                className={`flex items-center gap-3 rounded-lg border p-3 transition-all duration-300 ${
                  isCompleted
                    ? 'border-accent/30 bg-accent/5'
                    : isCurrent
                      ? 'border-accent bg-accent/10'
                      : 'border-border/50 opacity-40'
                }`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md transition-colors ${
                    isCompleted
                      ? 'bg-accent text-accent-foreground'
                      : isCurrent
                        ? 'bg-accent/20 text-accent'
                        : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {isCurrent ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <step.icon className="h-4 w-4" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{step.label}</p>
                  <p className="text-xs text-muted-foreground">{step.detail}</p>
                </div>
                {isCompleted && (
                  <span className="text-xs font-medium text-accent">完了</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500 ease-out"
            style={{
              width: `${((completedSteps.length) / ANALYSIS_STEPS.length) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
