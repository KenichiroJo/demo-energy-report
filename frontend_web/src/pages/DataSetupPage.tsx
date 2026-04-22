import { useState, useCallback, type ChangeEvent, type DragEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Upload, Database, FileSpreadsheet, FileText,
  ArrowRight, Check, X,
  Sparkles, TrendingUp, Target, Zap, Shield, Briefcase,
  MessageSquare, Lock,
} from 'lucide-react';

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  rows?: number;
}

// エージェントの機能（Capabilities）
const CAPABILITIES = [
  {
    icon: TrendingUp,
    title: '財務・収益性分析',
    desc: 'セグメント別の売上・利益・EBITDA・予算達成率を即時集計',
  },
  {
    icon: Target,
    title: 'SFA / パイプライン分析',
    desc: '案件進捗、失注理由、競合出現頻度を可視化',
  },
  {
    icon: Zap,
    title: 'KPI達成状況',
    desc: '中期経営計画16指標の達成率と差分を自動算出',
  },
  {
    icon: Shield,
    title: 'ESG指標モニタリング',
    desc: 'CO2削減量、再エネ供給、カーボンクレジットを横断分析',
  },
  {
    icon: Briefcase,
    title: 'プロジェクト進捗',
    desc: '大型プロジェクトのマイルストーンとリスクを統合管理',
  },
  {
    icon: MessageSquare,
    title: '対話型深掘り',
    desc: '「前年対比は？」等の追加質問にリアルタイムで応答',
  },
];

const DATA_SOURCES = [
  {
    id: 'databricks',
    name: 'Databricks',
    description: 'データレイクハウスから財務・発電データを接続',
    icon: Database,
    available: false,
  },
  {
    id: 'sharepoint',
    name: 'SharePoint',
    description: '社内文書・議事録・報告書を検索接続',
    icon: FileText,
    available: false,
  },
  {
    id: 'salesforce',
    name: 'Salesforce / SFA',
    description: '営業パイプライン・案件データを接続',
    icon: FileSpreadsheet,
    available: false,
  },
] as const;

const DEMO_DATASETS = [
  { name: '財務データ（月次×セグメント別）', rows: 240, file: 'financial.json' },
  { name: 'SFA パイプライン（営業案件）', rows: 60, file: 'sfa.json' },
  { name: '社内文書メタデータ', rows: 50, file: 'documents.json' },
] as const;

export function DataSetupPage() {
  const navigate = useNavigate();
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [demoLoaded, setDemoLoaded] = useState(false);

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    const newFiles: UploadedFile[] = Array.from(files).map((f) => ({
      name: f.name,
      size: f.size,
      type: f.type || 'unknown',
    }));
    setUploadedFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
    },
    [handleFiles],
  );

  const removeFile = useCallback((index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const loadDemoData = useCallback(() => {
    setDemoLoaded(true);
    setUploadedFiles(
      DEMO_DATASETS.map((d) => ({
        name: d.file,
        size: 0,
        type: 'application/json',
        rows: d.rows,
      })),
    );
  }, []);

  const canProceed = uploadedFiles.length > 0 || demoLoaded;

  const handleProceed = useCallback(() => {
    navigate('/analyzing');
  }, [navigate]);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return 'デモデータ';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="min-h-svh bg-background">
      {/* ========== ヘッダーバナー ========== */}
      <header className="border-b bg-card">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs">
              AI
            </div>
            <span className="text-sm font-bold tracking-tight">Insight Navigator</span>
            <span className="hidden sm:inline text-[10px] text-muted-foreground px-1.5 py-0.5 rounded bg-muted/50">
              Powered by DataRobot
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-4 text-xs text-muted-foreground">
            <span>v1.0 Demo Build</span>
          </div>
        </div>
      </header>

      {/* ========== メインコンテンツ ========== */}
      <div className="mx-auto max-w-6xl px-6 py-10 space-y-12">

        {/* ========== ヒーロー ========== */}
        <section className="text-center space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border bg-primary/5 px-3 py-1 text-[11px] font-medium text-primary">
            <Sparkles className="h-3 w-3" />
            <span>AI Agent for Executive Reporting</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight leading-tight">
            多角的分析レポート
            <span className="text-primary">エージェント</span>
          </h1>
          <p className="text-base text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            財務・営業・ESG・社内文書を<strong className="text-foreground">横断的に分析</strong>し、
            経営判断に資する<strong className="text-foreground">統合レポート</strong>を自動生成。
            <br />
            対話形式で深掘りできる、次世代の経営レポーティング基盤です。
          </p>
        </section>

        {/* ========== 機能一覧 ========== */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-sm font-bold">このエージェントができること</h2>
            <div className="flex-1 h-px bg-border" />
            <span className="text-[11px] text-muted-foreground">6 capabilities</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {CAPABILITIES.map((cap) => (
              <div
                key={cap.title}
                className="rounded-xl border bg-card p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary mb-3">
                  <cap.icon className="h-4.5 w-4.5" />
                </div>
                <h3 className="text-sm font-bold mb-1">{cap.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{cap.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ========== データ準備セクション ========== */}
        <section className="space-y-5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold">分析データを準備</h2>
            <div className="flex-1 h-px bg-border" />
            <span className="text-[11px] text-muted-foreground">Step 1 of 2</span>
          </div>

          {/* デモで試す (メインCTA) */}
          <div className="rounded-xl border-2 border-primary/30 bg-primary/5 p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="inline-flex items-center gap-1 rounded-md bg-primary px-2 py-0.5 text-[10px] font-bold text-primary-foreground">
                    <Sparkles className="h-2.5 w-2.5" />
                    RECOMMENDED
                  </span>
                  <h3 className="text-base font-bold">デモデータで今すぐ試す</h3>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  環境エネルギー事業のサンプルデータ（財務240行 + SFA60件 + 社内文書50件）を読み込み、
                  AIエージェントが実際に多角的分析を実行します。
                </p>
              </div>
              <Button
                size="default"
                onClick={loadDemoData}
                disabled={demoLoaded}
                className="shrink-0"
              >
                {demoLoaded ? (
                  <>
                    <Check className="h-4 w-4 mr-1.5" />
                    読み込み済み
                  </>
                ) : (
                  'デモデータを使用'
                )}
              </Button>
            </div>
            <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-primary/10">
              {DEMO_DATASETS.map((d) => (
                <span
                  key={d.file}
                  className="inline-flex items-center gap-1 text-[11px] bg-card text-muted-foreground px-2 py-1 rounded-md border"
                >
                  <FileSpreadsheet className="h-3 w-3" />
                  {d.name}（{d.rows}行）
                </span>
              ))}
            </div>
          </div>

          {/* アップロード済みファイル */}
          {uploadedFiles.length > 0 && demoLoaded && (
            <div className="space-y-2">
              <h3 className="text-xs font-medium text-muted-foreground">
                読み込み済みデータ
              </h3>
              <div className="space-y-1.5">
                {uploadedFiles.map((file, i) => (
                  <div
                    key={`${file.name}-${i}`}
                    className="flex items-center gap-3 rounded-lg border bg-card p-3"
                  >
                    <FileSpreadsheet className="h-4 w-4 text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatSize(file.size)}
                        {file.rows ? ` · ${file.rows} 行` : ''}
                      </p>
                    </div>
                    <Check className="h-4 w-4 text-primary shrink-0" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* データソース接続 + カスタムアップロード */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* 本番接続 */}
            <div className="rounded-xl border bg-card p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                  <h3 className="text-xs font-bold">Enterprise 本番接続</h3>
                </div>
                <span className="text-[9px] font-bold bg-gradient-to-r from-primary to-primary/70 text-primary-foreground px-1.5 py-0.5 rounded">
                  PRODUCTION
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                本番環境では、以下のエンタープライズシステムに直接接続して最新データで分析できます。
              </p>
              <div className="space-y-1.5">
                {DATA_SOURCES.map((source) => (
                  <div
                    key={source.id}
                    className="flex items-center gap-2.5 rounded-md border bg-muted/30 p-2.5"
                  >
                    <source.icon className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{source.name}</p>
                      <p className="text-[10px] text-muted-foreground truncate">{source.description}</p>
                    </div>
                    <span className="text-[9px] font-medium text-muted-foreground border rounded px-1.5 py-0.5 shrink-0">
                      本番環境のみ
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* カスタムアップロード */}
            <div
              className={`rounded-xl border-2 border-dashed p-4 transition-colors ${
                isDragging
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/30'
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              <div className="flex items-center gap-2 mb-3">
                <Upload className="h-3.5 w-3.5 text-muted-foreground" />
                <h3 className="text-xs font-bold">カスタムデータをアップロード</h3>
              </div>
              <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                自社のCSV / Excel / JSONファイルをアップロードして分析できます。
              </p>
              <label>
                <input
                  type="file"
                  className="hidden"
                  multiple
                  accept=".csv,.xlsx,.xls,.json,.tsv"
                  onChange={handleFileInput}
                />
                <Button variant="secondary" size="sm" asChild className="w-full">
                  <span>
                    <Upload className="h-3.5 w-3.5 mr-1.5" />
                    ファイルを選択
                  </span>
                </Button>
              </label>
              {uploadedFiles.length > 0 && !demoLoaded && (
                <div className="mt-3 space-y-1">
                  {uploadedFiles.map((file, i) => (
                    <div
                      key={`${file.name}-${i}`}
                      className="flex items-center gap-2 rounded-md bg-muted/30 px-2 py-1.5"
                    >
                      <FileSpreadsheet className="h-3 w-3 text-primary shrink-0" />
                      <span className="text-[11px] truncate flex-1">{file.name}</span>
                      <button
                        onClick={() => removeFile(i)}
                        className="text-muted-foreground hover:text-destructive shrink-0"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ========== 分析開始 ========== */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold">AI分析を実行</h2>
            <div className="flex-1 h-px bg-border" />
            <span className="text-[11px] text-muted-foreground">Step 2 of 2</span>
          </div>

          <div className="rounded-xl border bg-card p-6 text-center">
            {!canProceed ? (
              <p className="text-xs text-muted-foreground mb-4">
                上記のデータを準備してから分析を開始できます
              </p>
            ) : (
              <p className="text-sm text-foreground mb-4">
                準備完了です。AIエージェントが<strong>8つの分析ツール</strong>を連携させ、統合レポートを生成します。
              </p>
            )}
            <Button
              size="lg"
              disabled={!canProceed}
              onClick={handleProceed}
              className="gap-2 min-w-[260px]"
            >
              <Sparkles className="h-4 w-4" />
              AIエージェントで分析を開始
              <ArrowRight className="h-4 w-4" />
            </Button>
            {canProceed && (
              <p className="text-[10px] text-muted-foreground mt-3">
                処理時間: 約60〜90秒 ・ 8つの分析ツールを自動連携
              </p>
            )}
          </div>
        </section>

        {/* フッター */}
        <footer className="border-t pt-6 pb-4">
          <p className="text-center text-[10px] text-muted-foreground">
            Insight Navigator ・ Built with DataRobot AI Platform, LangGraph &amp; GPT-5
          </p>
        </footer>

      </div>
    </div>
  );
}
