# Copyright 2026 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from datetime import datetime
from typing import Any, Optional, Union

from datarobot_genai.langgraph.agent import LangGraphAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_litellm.chat_models import ChatLiteLLM
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agent.config import Config
from agent.tools import ALL_TOOLS


class MyAgent(LangGraphAgent):
    """環境エネルギー本部 経営レポーティングエージェント。

    財務データ、SFAパイプライン、社内文書、発電実績を横断的に分析し、
    経営企画・経営層向けの構造化レポートを対話形式で提供する。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        verbose: Optional[Union[bool, str]] = True,
        timeout: Optional[int] = 90,
        *,
        llm: Optional[BaseChatModel] = None,
        workflow_tools: Optional[list[BaseTool]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            api_key=api_key,
            api_base=api_base,
            model=model,
            verbose=verbose,
            timeout=timeout,
            **kwargs,
        )
        self._nat_llm = llm
        self._workflow_tools = workflow_tools or []
        self.config = Config()
        self.default_model = self.config.llm_default_model
        if model in ("unknown", "datarobot-deployed-llm"):
            self.model = self.default_model

    # -----------------------------------------------------------------
    # LangGraph workflow: flat agent + tools (no nested subgraph)
    # -----------------------------------------------------------------

    @property
    def prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは環境エネルギー本部の経営レポーティングAIです。"
                    "ユーザーの質問に対し、財務データ・SFAパイプライン・社内文書・発電実績を統合的に分析し、"
                    "経営判断に資する回答を提供します。"
                    "会話履歴は {chat_history} で参照できます（空の場合もあります）。",
                ),
                (
                    "user",
                    f"{{topic}}\n\n（現在: {datetime.now().year}年）",
                ),
            ]
        )

    def llm(
        self,
        auto_model_override: bool = True,
    ) -> BaseChatModel:
        """Returns the LLM to use for agent nodes."""
        if self._nat_llm is not None:
            return self._nat_llm

        api_base = self.litellm_api_base(self.config.llm_deployment_id)
        model = self.model or self.default_model
        if auto_model_override and not self.config.use_datarobot_llm_gateway:
            model = self.default_model
        if self.verbose:
            print(f"Using model: {model}")

        config = {
            "model": model,
            "api_base": api_base,
            "api_key": self.api_key,
            "timeout": self.timeout,
            "streaming": True,
            "max_retries": 3,
        }

        if not self.config.use_datarobot_llm_gateway and self._identity_header:
            config["model_kwargs"] = {"extra_headers": self._identity_header}  # type: ignore[assignment]

        return ChatLiteLLM(**config)

    @property
    def workflow(self) -> StateGraph[MessagesState]:
        tools = ALL_TOOLS + self.mcp_tools + self._workflow_tools
        model = self.llm().bind_tools(tools)

        system_prompt = (
            "あなたは環境エネルギー本部の経営レポーティングAIです。\n"
            "ユーザーの質問に対し、複数のデータソースを統合的に分析し、\n"
            "経営企画・経営層向けの構造化レポートを提供します。\n\n"
            "## 利用可能なデータソース（ツール）\n"
            "1. **analyze_financial_data**: 売上・利益・EBITDA・予算達成率の月次データ（FY2023-FY2024、10セグメント）\n"
            "2. **analyze_sfa_pipeline**: 営業案件60件（アクティブ・受注・失注）、競合分析、失注理由分析\n"
            "3. **search_documents**: 社内文書50件（事業計画・月次報告・議事録・分析レポート・ESG報告・技術評価・規程）\n"
            "4. **analyze_generation_data**: 発電実績（設備容量・発電量・稼働率トレンド）\n"
            "5. **get_user_feedback_context**: 過去のユーザーフィードバック\n"
            "6. **analyze_kpi_performance**: 中期経営計画KPI（財務・事業・ESG・人材、FY2023実績〜FY2028目標）\n"
            "7. **analyze_esg_metrics**: ESG月次指標（CO2削減・再エネ供給・カーボンクレジット・Scope排出量）\n"
            "8. **analyze_project_milestones**: 大型プロジェクト8件のマイルストーン進捗\n\n"
            "## 作業手順\n"
            "1. **データ取得**: 質問に応じて適切なツールを1つ以上呼び出す\n"
            "   - 複合的な質問は複数ツールを併用\n"
            "   - KPI分析は analyze_kpi_performance + analyze_financial_data\n"
            "   - ESG関連は analyze_esg_metrics + search_documents\n"
            "2. **分析**: 取得データから洞察を導出\n"
            "   - 前期比・前年比のトレンド、予算達成率\n"
            "   - セグメント間比較、リスク・機会の特定\n"
            "   - 競合動向、プロジェクト遅延リスク\n"
            "3. **レポート作成**: Markdown形式で構造化レポートを出力\n\n"
            "## レポート構成\n"
            "1. **エグゼクティブサマリー** (3-5文)\n"
            "2. **主要指標** (表形式)\n"
            "3. **分析詳細**: セグメント別・テーマ別の状況\n"
            "4. **リスクと機会**\n"
            "5. **アクション提案**\n\n"
            "## 注意事項\n"
            "- 数値には適切な単位を付ける(百万円、億円、MW、MWh、%等)\n"
            "- 日本語で回答\n"
            "- 不明な点がある場合はその旨を明記\n"
        )

        async def call_model(state: MessagesState, config: RunnableConfig):
            messages = state["messages"]
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=system_prompt)] + messages
            response = await model.ainvoke(messages, config=config)
            return {"messages": [response]}

        def should_continue(state: MessagesState):
            last = state["messages"][-1]
            if last.tool_calls:
                return "tools"
            return END

        tool_node = ToolNode(tools)

        graph = StateGraph(MessagesState)
        graph.add_node("agent", call_model)
        graph.add_node("tools", tool_node)
        graph.add_edge(START, "agent")
        graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        graph.add_edge("tools", "agent")
        return graph  # type: ignore[return-value]
