import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart3, FileText, TrendingUp, Shield, Loader2, Zap, Database, Search, Brain } from 'lucide-react';
import { getAgUiEndpoint } from '@/lib/url-utils';

// ツール名 → ステップID のマッピング
const TOOL_TO_STEP: Record<string, string> = {
  analyze_financial_data: 'financial',
  analyze_generation_data: 'financial',
  analyze_sfa_pipeline: 'pipeline',
  analyze_kpi_performance: 'kpi',
  search_documents: 'documents',
  analyze_esg_metrics: 'esg',
  analyze_project_milestones: 'projects',
  get_user_feedback_context: 'synthesis',
};

interface AnalysisStep {
  id: string;
  icon: React.ElementType;
  label: string;
  detail: string;
  status: 'waiting' | 'running' | 'done';
}

const INITIAL_STEPS: AnalysisStep[] = [
  { id: 'financial', icon: BarChart3,   label: '財務データを分析中',        detail: 'セグメント別売上・利益・EBITDA推移',          status: 'waiting' },
  { id: 'pipeline',  icon: TrendingUp,  label: 'SFAパイプラインを分析中',   detail: '営業案件60件の進捗・着地見込み',              status: 'waiting' },
  { id: 'kpi',       icon: Zap,         label: 'KPI達成状況を確認中',       detail: '中計KPI 16指標の達成率分析',                  status: 'waiting' },
  { id: 'documents', icon: Search,       label: '社内文書を検索中',          detail: '事業計画・議事録・報告書50件をスキャン',      status: 'waiting' },
  { id: 'esg',       icon: Shield,       label: 'ESG指標を集計中',           detail: 'CO2削減量・再エネ供給量・カーボンクレジット', status: 'waiting' },
  { id: 'projects',  icon: Database,     label: 'プロジェクト進捗を確認中',  detail: '大型プロジェクト8件のマイルストーン',         status: 'waiting' },
  { id: 'synthesis', icon: Brain,        label: '統合レポートを生成中',      detail: 'データを横断分析し、経営示唆を導出',         status: 'waiting' },
];

const AGENT_PROMPT = `環境エネルギー本部の2025年度 経営レポートを作成してください。
以下の観点で統合的に分析してください:

1. **エグゼクティブサマリー**: 全体の概況を3-5文で。主要KPIを表形式で。ハイライト3-4点。
2. **セグメント別財務分析**: 主要セグメント（太陽光・風力・バイオマス・省エネ・電力小売等）の売上・利益率と前年対比。
3. **SFAパイプライン**: ファネル概況（ステージ別の件数・金額）、注目案件、リスクフラグ。
4. **リスクと機会・提言**: 事業リスク、成長機会、経営層へのアクション提案。

各分析ツールを呼び出してデータを取得し、それを基にレポートを作成してください。

（現在: 2026年）`;

export function AnalyzingPage() {
  const navigate = useNavigate();
  const [steps, setSteps] = useState<AnalysisStep[]>(INITIAL_STEPS);
  const [statusText, setStatusText] = useState('エージェントを起動中...');
  const [agentContent, setAgentContent] = useState('');
  const [hasError, setHasError] = useState(false);
  const completedStepsRef = useRef(new Set<string>());
  const xhrRef = useRef<XMLHttpRequest | null>(null);

  const markStep = useCallback((stepId: string, status: 'running' | 'done') => {
    setSteps(prev => prev.map(s =>
      s.id === stepId ? { ...s, status } : s
    ));
    if (status === 'done') {
      completedStepsRef.current.add(stepId);
    }
  }, []);

  useEffect(() => {
    const threadId = `report-${crypto.randomUUID()}`;
    const runId = crypto.randomUUID();

    const payload = {
      thread_id: threadId,
      run_id: runId,
      state: '',
      messages: [{ id: `msg-${crypto.randomUUID()}`, role: 'user', content: AGENT_PROMPT, name: 'user' }],
      tools: [],
      context: [],
      forwarded_props: '',
    };

    const xhr = new XMLHttpRequest();
    xhrRef.current = xhr;
    xhr.open('POST', getAgUiEndpoint(), true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.withCredentials = true;
    xhr.responseType = 'text';
    xhr.timeout = 600000; // 10分

    let lastIndex = 0;
    let fullText = '';
    let currentToolSteps = new Set<string>();
    let synthesisStarted = false;

    const processLine = (line: string) => {
      if (!line.startsWith('data: ')) return;
      const jsonStr = line.slice(6).trim();
      if (!jsonStr) return;

      try {
        const event = JSON.parse(jsonStr);

        switch (event.type) {
          case 'RUN_STARTED':
            setStatusText('エージェントがデータソースに接続中...');
            markStep('financial', 'running');
            break;

          case 'TOOL_CALL_START': {
            const toolName = event.toolCallName || '';
            const stepId = TOOL_TO_STEP[toolName];
            if (stepId && !completedStepsRef.current.has(stepId)) {
              markStep(stepId, 'running');
              currentToolSteps.add(stepId);
              const step = INITIAL_STEPS.find(s => s.id === stepId);
              if (step) setStatusText(step.label + '...');
            }
            break;
          }

          case 'TOOL_CALL_END':
          case 'TOOL_CALL_RESULT': {
            // 現在実行中のツールステップを完了にする
            for (const stepId of currentToolSteps) {
              markStep(stepId, 'done');
            }
            currentToolSteps.clear();
            break;
          }

          case 'TEXT_MESSAGE_START':
            if (!synthesisStarted) {
              synthesisStarted = true;
              // まだ未完了のツール系ステップをすべて完了にする
              for (const s of INITIAL_STEPS) {
                if (s.id !== 'synthesis' && !completedStepsRef.current.has(s.id)) {
                  markStep(s.id, 'done');
                }
              }
              markStep('synthesis', 'running');
              setStatusText('データを統合し、レポートを生成中...');
            }
            break;

          case 'TEXT_MESSAGE_CONTENT':
            if (event.delta) {
              fullText += event.delta;
              setAgentContent(fullText);
            }
            break;

          case 'RUN_FINISHED':
            markStep('synthesis', 'done');
            setStatusText('レポート生成完了');
            break;

          case 'RUN_ERROR':
            setHasError(true);
            setStatusText(`エラー: ${event.message || '不明なエラー'}`);
            break;
        }
      } catch {
        // partial JSON line
      }
    };

    xhr.onprogress = () => {
      const newData = xhr.responseText.substring(lastIndex);
      lastIndex = xhr.responseText.length;
      for (const line of newData.split('\n')) {
        processLine(line);
      }
    };

    xhr.onload = () => {
      // 残りのデータを処理
      const remaining = xhr.responseText.substring(lastIndex);
      for (const line of remaining.split('\n')) {
        processLine(line);
      }

      if (fullText) {
        // sessionStorageにレポートコンテンツを保存
        sessionStorage.setItem('agent-report-content', fullText);
        sessionStorage.setItem('agent-report-timestamp', new Date().toISOString());
        // 全ステップを完了に
        setSteps(prev => prev.map(s => ({ ...s, status: 'done' })));
        setStatusText('レポート生成完了');
        // 少し待ってから遷移
        setTimeout(() => navigate('/report', { replace: true }), 800);
      } else if (!hasError) {
        setHasError(true);
        setStatusText('レポートの生成に失敗しました');
      }
    };

    xhr.onerror = () => {
      setHasError(true);
      setStatusText('ネットワークエラーが発生しました');
    };

    xhr.ontimeout = () => {
      setHasError(true);
      setStatusText('タイムアウト: 応答に時間がかかりすぎています');
    };

    xhr.send(JSON.stringify(payload));

    return () => {
      if (xhrRef.current && xhrRef.current.readyState !== XMLHttpRequest.DONE) {
        xhrRef.current.abort();
      }
    };
  }, [navigate, markStep]);

  const completedCount = steps.filter(s => s.status === 'done').length;
  const progress = completedCount / steps.length;

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-6">
      <div className="w-full max-w-lg space-y-8 text-center">
        {/* Spinning icon */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/5">
          {hasError ? (
            <Shield className="h-8 w-8 text-destructive" />
          ) : completedCount === steps.length ? (
            <BarChart3 className="h-8 w-8 text-primary" />
          ) : (
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
          )}
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold tracking-tight">
            {completedCount === steps.length ? '経営レポート生成完了' : '経営レポートを生成中'}
          </h1>
          <p className="text-sm text-muted-foreground">
            {statusText}
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-2.5 text-left">
          {steps.map((step) => (
            <div
              key={step.id}
              className={`flex items-center gap-3 rounded-lg border p-3 transition-all duration-500 ${
                step.status === 'done'
                  ? 'border-primary/20 bg-primary/5'
                  : step.status === 'running'
                    ? 'border-primary/40 bg-primary/10 shadow-sm'
                    : 'border-border/40 opacity-40'
              }`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-500 ${
                  step.status === 'done'
                    ? 'bg-primary text-primary-foreground'
                    : step.status === 'running'
                      ? 'bg-primary/20 text-primary'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {step.status === 'running' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <step.icon className="h-4 w-4" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{step.label}</p>
                <p className="text-xs text-muted-foreground truncate">{step.detail}</p>
              </div>
              {step.status === 'done' && (
                <span className="text-xs font-medium text-primary shrink-0">完了</span>
              )}
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {completedCount} / {steps.length} ステップ完了
          </p>
        </div>

        {/* エラー時のリトライ */}
        {hasError && (
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-muted/50 transition-colors"
          >
            <Loader2 className="h-3.5 w-3.5" />
            再試行
          </button>
        )}
      </div>
    </div>
  );
}
