import { useState, useCallback, type ChangeEvent, type DragEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Upload, Database, FileSpreadsheet, FileText, ArrowRight, Check, X } from 'lucide-react';

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  rows?: number;
}

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
  { name: 'SFA パイプライン（営業案件）', rows: 30, file: 'sfa.json' },
  { name: '社内文書メタデータ', rows: 20, file: 'documents.json' },
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
    navigate('/chat');
  }, [navigate]);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return 'デモデータ';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-6">
      <div className="w-full max-w-3xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-accent text-accent-foreground">
            <Database className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">データセットアップ</h1>
          <p className="text-muted-foreground max-w-lg mx-auto">
            分析に使用するデータをアップロードするか、データソースを接続してください。
            セットアップ完了後、AIアシスタントとの対話分析に進みます。
          </p>
        </div>

        {/* Upload Area */}
        <div
          className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
            isDragging
              ? 'border-accent bg-accent/5'
              : 'border-border hover:border-accent/50'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
          <p className="text-sm font-medium mb-1">
            CSV / Excel / JSON ファイルをドラッグ＆ドロップ
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            または下のボタンからファイルを選択
          </p>
          <label>
            <input
              type="file"
              className="hidden"
              multiple
              accept=".csv,.xlsx,.xls,.json,.tsv"
              onChange={handleFileInput}
            />
            <Button variant="outline" size="sm" asChild>
              <span>ファイルを選択</span>
            </Button>
          </label>
        </div>

        {/* Uploaded Files */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">
              アップロード済みデータ
            </h3>
            <div className="space-y-1.5">
              {uploadedFiles.map((file, i) => (
                <div
                  key={`${file.name}-${i}`}
                  className="flex items-center gap-3 rounded-lg border bg-card p-3"
                >
                  <FileSpreadsheet className="h-5 w-5 text-accent shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatSize(file.size)}
                      {file.rows ? ` · ${file.rows} 行` : ''}
                    </p>
                  </div>
                  <Check className="h-4 w-4 text-green-500 shrink-0" />
                  {!demoLoaded && (
                    <button
                      onClick={() => removeFile(i)}
                      className="text-muted-foreground hover:text-destructive shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Data Source Connection */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">
            データソース接続（Enterprise）
          </h3>
          <div className="grid gap-3 sm:grid-cols-3">
            {DATA_SOURCES.map((source) => (
              <button
                key={source.id}
                disabled={!source.available}
                className="flex flex-col items-start gap-2 rounded-lg border bg-card p-4 text-left opacity-60 cursor-not-allowed"
              >
                <source.icon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">{source.name}</p>
                  <p className="text-xs text-muted-foreground">{source.description}</p>
                </div>
                <span className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                  Coming Soon
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Demo Data */}
        <div className="rounded-lg border bg-card/50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium">デモデータで試す</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                環境エネルギー事業のサンプルデータ（財務・SFA・文書）を読み込みます
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={loadDemoData}
              disabled={demoLoaded}
            >
              {demoLoaded ? '読み込み済み' : 'デモデータを使用'}
            </Button>
          </div>
          {!demoLoaded && (
            <div className="flex flex-wrap gap-2">
              {DEMO_DATASETS.map((d) => (
                <span
                  key={d.file}
                  className="text-[11px] bg-muted text-muted-foreground px-2 py-1 rounded-md"
                >
                  {d.name}（{d.rows}行）
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Proceed Button */}
        <div className="flex justify-center pt-2">
          <Button
            size="lg"
            disabled={!canProceed}
            onClick={handleProceed}
            className="gap-2 min-w-[240px]"
          >
            分析を開始する
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
