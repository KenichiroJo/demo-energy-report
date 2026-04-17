import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  TrendingUp,
  FileText,
  Shield,
  ChevronDown,
  ChevronUp,
  MessageCircle,
  X,
  Download,
  RotateCcw,
  ArrowUp,
  Loader2,
  Sparkles,
  Bot,
  User,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Markdown } from '@/components/ui/markdown';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getAgUiEndpoint } from '@/lib/url-utils';

// ---------------------------------------------------------------------------
// レポートセクション定義
// ---------------------------------------------------------------------------
interface ReportSection {
  id: string;
  icon: React.ElementType;
  title: string;
  content: string;
  drillDownPrompt: string;
}

const REPORT_SECTIONS: ReportSection[] = [
  {
    id: 'summary',
    icon: BarChart3,
    title: 'エグゼクティブサマリー',
    content: `## 概況

2025年度上期の環境エネルギー事業は、**売上高 1,847百万円**（前年同期比 +8.2%）、**営業利益 312百万円**（同 +12.5%）と堅調に推移しました。

### 主要KPI

| 指標 | 実績 | 前年同期比 |
|------|------|-----------|
| 売上高 | 1,847百万円 | +8.2% |
| 営業利益 | 312百万円 | +12.5% |
| 設備容量 | 425MW | +15MW |
| 設備利用率 | 78.3% | +2.1pt |
| CO2削減量 | 18,200t | +9.8% |

### ハイライト
- 太陽光セグメントが通期計画を上回るペースで推移
- 風力新規案件の受注が好調（SFAパイプライン +23%）
- バイオマスの設備利用率が改善傾向`,
    drillDownPrompt: 'エグゼクティブサマリーの詳細を教えてください。特に前年との比較について深掘りしたいです。',
  },
  {
    id: 'financial',
    icon: TrendingUp,
    title: 'セグメント別財務分析',
    content: `## セグメント別業績

### 太陽光発電
- **売上高**: 823百万円（構成比 44.6%）— 新規メガソーラー稼働寄与
- **営業利益率**: 19.2%（前期 17.8%）— O&Mコスト最適化が奏功

### 風力発電
- **売上高**: 512百万円（構成比 27.7%）— 洋上風力プロジェクト準備段階
- **営業利益率**: 15.1%（前期 14.3%）— 稼働率向上

### バイオマス
- **売上高**: 298百万円（構成比 16.1%）— 燃料調達価格安定
- **営業利益率**: 12.8%（前期 11.2%）— 熱効率改善

### 省エネルギー
- **売上高**: 214百万円（構成比 11.6%）— ESCO案件が堅調
- **営業利益率**: 22.4%（前期 21.0%）— ストック収入増

### 注目ポイント
> 太陽光と風力で全体売上の **72.3%** を占め、成長ドライバーとして機能。省エネルギーは利益率最高セグメント。`,
    drillDownPrompt: 'セグメント別の月次推移を詳しく分析してください。特に利益率の変動要因を知りたいです。',
  },
  {
    id: 'pipeline',
    icon: FileText,
    title: 'SFAパイプライン・案件状況',
    content: `## 営業パイプライン

### ファネル概況

| ステージ | 件数 | 金額（百万円） | 期待金額 |
|----------|------|---------------|---------|
| リード | 8件 | 1,240 | 248 |
| 提案中 | 7件 | 980 | 490 |
| 交渉中 | 6件 | 1,520 | 1,064 |
| 最終段階 | 4件 | 860 | 774 |
| 受注確定 | 5件 | 720 | 720 |

### パイプライン総額: **5,320百万円**（期待金額ベース: **3,296百万円**）

### 注目案件
1. **洋上風力 A海域プロジェクト** — 交渉中 / 450百万円 / 確度75%
2. **メガソーラー B地区** — 最終段階 / 280百万円 / 確度90%
3. **バイオマス C発電所 燃料転換** — 提案中 / 180百万円 / 確度50%

### リスクフラグ
- 交渉中案件のうち2件が3ヶ月以上停滞 → 要フォロー
- リード段階の大型案件（500百万円超）に受注確度20%の案件あり`,
    drillDownPrompt: 'SFAパイプラインの詳細を教えてください。停滞案件の具体的なリスクと対策を分析してください。',
  },
  {
    id: 'risk',
    icon: Shield,
    title: 'リスクと機会・提言',
    content: `## リスクと機会

### ⚠️ リスク

| リスク項目 | 影響度 | 対応状況 |
|-----------|--------|---------|
| 系統接続制約の強化 | 高 | 蓄電池併設で対応検討中 |
| 燃料価格変動（バイオマス） | 中 | 長期契約により一定のヘッジ |
| 為替リスク（設備輸入） | 中 | 円安基調で注視 |
| 人材不足（洋上風力技術者） | 高 | 採用・育成計画策定中 |

### 🚀 機会

- **GX推進法による補助金拡充** — 太陽光・洋上風力に追い風
- **企業PPA需要の急増** — 法人顧客からの引き合い+40%
- **蓄電池コスト低下** — 新規ビジネスモデルの構築可能性
- **カーボンクレジット市場** — CO2削減量の収益化ポテンシャル

## 提言

1. **洋上風力案件の早期クローズ** — A海域プロジェクトの交渉加速を推奨
2. **PPA営業体制の強化** — 法人需要獲得のため専任チーム組成を検討
3. **蓄電池事業の検討** — 系統制約対応と新規収益源の両面で戦略的に重要
4. **人材投資** — 洋上風力技術者の確保が中長期成長のボトルネック`,
    drillDownPrompt: 'リスクと機会についてさらに詳しく分析してください。特にGX推進法の影響と蓄電池事業の可能性について教えてください。',
  },
];

// ---------------------------------------------------------------------------
// レポートページ本体
// ---------------------------------------------------------------------------
export function ReportPage() {
  const navigate = useNavigate();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['ai-report', ...REPORT_SECTIONS.map((s) => s.id)]),
  );
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<
    { role: 'user' | 'assistant'; text: string }[]
  >([]);
  const [chatInput, setChatInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const threadIdRef = useRef<string>(`report-${crypto.randomUUID()}`);
  const chatHistoryRef = useRef<{ id: string; role: string; content: string; name: string }[]>([]);

  // エージェント生成コンテンツをsessionStorageから読み込み
  const [agentReport, setAgentReport] = useState<string | null>(null);
  const [reportTimestamp, setReportTimestamp] = useState<string | null>(null);
  useEffect(() => {
    const content = sessionStorage.getItem('agent-report-content');
    const ts = sessionStorage.getItem('agent-report-timestamp');
    if (content) setAgentReport(content);
    if (ts) setReportTimestamp(ts);
  }, []);

  const toggleSection = useCallback((id: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  // AG-UI SSE でバックエンドにメッセージ送信
  const sendToAgent = useCallback(async (userText: string) => {
    setIsStreaming(true);

    const userMsgId = `msg-${crypto.randomUUID()}`;
    chatHistoryRef.current.push({
      id: userMsgId,
      role: 'user',
      content: userText,
      name: 'user',
    });

    const payload = {
      thread_id: threadIdRef.current,
      run_id: crypto.randomUUID(),
      state: '',
      messages: chatHistoryRef.current,
      tools: [],
      context: [],
      forwarded_props: '',
    };

    // アシスタントメッセージのプレースホルダーを追加
    setChatMessages((prev) => [...prev, { role: 'assistant', text: '' }]);

    let assistantText = '';

    const updateAssistantText = (text: string) => {
      assistantText = text;
      setChatMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: 'assistant', text };
        return updated;
      });
    };

    // XMLHttpRequest でSSEストリーミング（プロキシ経由での互換性が高い）
    await new Promise<void>((resolve) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', getAgUiEndpoint(), true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.withCredentials = true;
      xhr.responseType = 'text';

      let lastIndex = 0;

      xhr.onprogress = () => {
        const newData = xhr.responseText.substring(lastIndex);
        lastIndex = xhr.responseText.length;

        const lines = newData.split('\n');
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);
            if (event.type === 'TEXT_MESSAGE_CONTENT' && event.delta) {
              updateAssistantText(assistantText + event.delta);
            }
          } catch {
            // JSON parse error - skip partial lines
          }
        }
      };

      xhr.onload = () => {
        // 成功完了 - 残りのデータも処理
        if (xhr.status === 200) {
          const remaining = xhr.responseText.substring(lastIndex);
          const lines = remaining.split('\n');
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;
            try {
              const event = JSON.parse(jsonStr);
              if (event.type === 'TEXT_MESSAGE_CONTENT' && event.delta) {
                updateAssistantText(assistantText + event.delta);
              }
            } catch {
              // skip
            }
          }
        }

        if (!assistantText) {
          updateAssistantText('応答を取得できませんでした。再度お試しください。');
        }

        // 会話履歴に追加
        chatHistoryRef.current.push({
          id: `msg-${crypto.randomUUID()}`,
          role: 'assistant',
          content: assistantText,
          name: 'assistant',
        });

        setIsStreaming(false);
        resolve();
      };

      xhr.onerror = () => {
        console.error('SSE stream error:', xhr.status, xhr.statusText);
        if (assistantText) {
          // 部分的なデータがあればそれを保持
          chatHistoryRef.current.push({
            id: `msg-${crypto.randomUUID()}`,
            role: 'assistant',
            content: assistantText,
            name: 'assistant',
          });
        } else {
          updateAssistantText('ネットワークエラーが発生しました。ページを更新して再度お試しください。');
        }
        setIsStreaming(false);
        resolve();
      };

      xhr.ontimeout = () => {
        if (assistantText) {
          chatHistoryRef.current.push({
            id: `msg-${crypto.randomUUID()}`,
            role: 'assistant',
            content: assistantText,
            name: 'assistant',
          });
        } else {
          updateAssistantText('応答がタイムアウトしました。');
        }
        setIsStreaming(false);
        resolve();
      };

      // 5分タイムアウト（エージェントの処理時間を考慮）
      xhr.timeout = 300000;

      xhr.send(JSON.stringify(payload));
    });
  }, []);

  const openChatWithPrompt = useCallback((prompt: string) => {
    setChatOpen(true);
    setChatMessages([{ role: 'user', text: prompt }]);
    chatHistoryRef.current = [];
    sendToAgent(prompt);
  }, [sendToAgent]);

  const sendChatMessage = useCallback(() => {
    if (!chatInput.trim() || isStreaming) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', text: msg }]);
    sendToAgent(msg);
  }, [chatInput, isStreaming, sendToAgent]);

  // チャットメッセージ末尾への自動スクロール
  const chatEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  return (
    <div className="flex h-svh w-full overflow-hidden bg-background">
      {/* ========== メインレポートエリア ========== */}
      <div className="flex flex-1 flex-col min-w-0 h-full">
        {/* ヘッダー */}
        <header className="flex items-center justify-between border-b bg-card/80 backdrop-blur-sm px-6 py-3 shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm shadow-sm">
              E
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">環境エネルギー本部 経営レポート</h1>
              <p className="text-xs text-muted-foreground">
                2025年度上期 ・ AI生成: {reportTimestamp ? new Date(reportTimestamp).toLocaleString('ja-JP') : new Date().toLocaleDateString('ja-JP')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              再分析
            </Button>
            <Button variant="ghost" size="sm" className="gap-1.5">
              <Download className="h-3.5 w-3.5" />
              PDF出力
            </Button>
            <Button
              size="sm"
              variant={chatOpen ? 'secondary' : 'default'}
              onClick={() => setChatOpen(!chatOpen)}
              className="gap-1.5"
            >
              <MessageCircle className="h-3.5 w-3.5" />
              AIに質問
            </Button>
          </div>
        </header>

        {/* レポート本文 */}
        <ScrollArea className="flex-1 min-h-0">
          <div className="mx-auto max-w-4xl px-6 py-8 space-y-4">
            {/* ===== AI生成レポート（メインセクション） ===== */}
            {agentReport && (
              <div className="rounded-xl border-2 border-primary/20 bg-card shadow-sm overflow-hidden transition-shadow hover:shadow-md">
                <button
                  onClick={() => toggleSection('ai-report')}
                  className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-bold">AI 統合分析レポート</span>
                    {reportTimestamp && (
                      <span className="ml-2 text-[10px] text-muted-foreground">
                        生成: {new Date(reportTimestamp).toLocaleString('ja-JP')}
                      </span>
                    )}
                  </div>
                  <span className="shrink-0 rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                    Agent Generated
                  </span>
                  {expandedSections.has('ai-report') ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </button>
                {expandedSections.has('ai-report') && (
                  <div className="border-t px-5 py-5">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <Markdown content={agentReport} />
                    </div>
                    <div className="mt-4 pt-3 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openChatWithPrompt('このレポートの内容をさらに深掘りしてください。特に前年対比の変動要因と、来期に向けたアクション提案を詳しく教えてください。')}
                        className="gap-1.5 text-primary/70 hover:text-primary"
                      >
                        <MessageCircle className="h-3.5 w-3.5" />
                        このレポートについて質問する
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ===== 定型レポートセクション（参考データ） ===== */}
            {agentReport && (
              <div className="flex items-center gap-3 pt-4 pb-1 px-1">
                <div className="h-px flex-1 bg-border" />
                <span className="text-[11px] text-muted-foreground shrink-0">参考: セグメント別定型レポート</span>
                <div className="h-px flex-1 bg-border" />
              </div>
            )}

            {REPORT_SECTIONS.map((section) => {
              const isExpanded = expandedSections.has(section.id);
              return (
                <div
                  key={section.id}
                  className="rounded-xl border bg-card shadow-sm overflow-hidden transition-shadow hover:shadow-md"
                >
                  {/* セクションヘッダー */}
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/5 text-primary">
                      <section.icon className="h-4 w-4" />
                    </div>
                    <span className="flex-1 text-sm font-bold">{section.title}</span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>

                  {/* セクション本文 */}
                  {isExpanded && (
                    <div className="border-t px-5 py-4">
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <Markdown content={section.content} />
                      </div>
                      <div className="mt-4 pt-3 border-t">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openChatWithPrompt(section.drillDownPrompt)}
                          className="gap-1.5 text-primary/70 hover:text-primary"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          このセクションを深掘り
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* ========== チャットサイドパネル（固定） ========== */}
      {chatOpen && (
        <div className="flex w-[480px] shrink-0 flex-col h-full border-l bg-card shadow-[-4px_0_24px_rgba(0,0,0,0.04)]">
          {/* パネルヘッダー */}
          <div className="flex items-center justify-between border-b px-5 py-3.5 shrink-0 bg-card">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div>
                <span className="text-sm font-bold">AIアシスタント</span>
                {isStreaming && (
                  <span className="ml-2 text-[10px] text-muted-foreground animate-pulse">分析中...</span>
                )}
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* メッセージエリア */}
          <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4">
            {chatMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/5 mb-4">
                  <Sparkles className="h-7 w-7 text-primary/40" />
                </div>
                <p className="text-sm font-medium text-foreground/80 mb-1">
                  レポートの内容について質問できます
                </p>
                <p className="text-xs text-muted-foreground mb-6">
                  セクションの「深掘り」ボタンからも開始できます
                </p>
                <div className="space-y-2 w-full max-w-xs">
                  {REPORT_SECTIONS.slice(0, 3).map((s) => (
                    <button
                      key={s.id}
                      onClick={() => openChatWithPrompt(s.drillDownPrompt)}
                      className="w-full rounded-lg border bg-background p-3 text-left text-xs leading-relaxed hover:bg-muted/30 hover:border-primary/20 transition-all"
                    >
                      <span className="text-muted-foreground">{s.drillDownPrompt.slice(0, 50)}...</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* アバター */}
                    <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full mt-0.5 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-primary/10 text-primary'
                    }`}>
                      {msg.role === 'user'
                        ? <User className="h-3.5 w-3.5" />
                        : <Bot className="h-3.5 w-3.5" />
                      }
                    </div>
                    {/* メッセージバブル */}
                    <div className={`min-w-0 max-w-[calc(100%-3rem)] ${msg.role === 'user' ? 'text-right' : ''}`}>
                      <div
                        className={`inline-block rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground rounded-tr-md'
                            : 'bg-muted/60 text-foreground rounded-tl-md'
                        }`}
                      >
                        {msg.role === 'assistant' && msg.text ? (
                          <div className="prose prose-sm dark:prose-invert max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                            <Markdown content={msg.text} />
                          </div>
                        ) : msg.role === 'assistant' && !msg.text ? (
                          <div className="flex items-center gap-2 py-1">
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">考え中...</span>
                          </div>
                        ) : (
                          msg.text
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>

          {/* 入力エリア */}
          <div className="border-t p-4 shrink-0 bg-card">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendChatMessage();
                    }
                  }}
                  placeholder="質問を入力..."
                  disabled={isStreaming}
                  className="w-full rounded-xl border bg-background px-4 py-2.5 pr-12 text-sm outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 disabled:opacity-50 transition-all"
                />
                <Button
                  size="sm"
                  onClick={sendChatMessage}
                  disabled={!chatInput.trim() || isStreaming}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 h-7 w-7 rounded-lg p-0"
                >
                  {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ArrowUp className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
