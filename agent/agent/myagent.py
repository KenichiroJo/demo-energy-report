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

from datarobot_genai.core.agents import (
    make_system_prompt,
)
from datarobot_genai.langgraph.agent import LangGraphAgent
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_litellm.chat_models import ChatLiteLLM
from langgraph.graph import END, START, MessagesState, StateGraph

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
    # LangGraph workflow: router → analyst → reporter → formatter
    # -----------------------------------------------------------------

    @property
    def workflow(self) -> StateGraph[MessagesState]:
        langgraph_workflow = StateGraph[
            MessagesState, None, MessagesState, MessagesState
        ](MessagesState)
        langgraph_workflow.add_node("router_node", self.agent_router)
        langgraph_workflow.add_node("analyst_node", self.agent_analyst)
        langgraph_workflow.add_node("reporter_node", self.agent_reporter)
        langgraph_workflow.add_edge(START, "router_node")
        langgraph_workflow.add_edge("router_node", "analyst_node")
        langgraph_workflow.add_edge("analyst_node", "reporter_node")
        langgraph_workflow.add_edge("reporter_node", END)
        return langgraph_workflow  # type: ignore[return-value]

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

    # -----------------------------------------------------------------
    # LLM accessor (NAT or DRUM)
    # -----------------------------------------------------------------

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

    # -----------------------------------------------------------------
    # Node 1: Router — ユーザー意図を判定しデータ取得方針を決定
    # -----------------------------------------------------------------

    @property
    def agent_router(self) -> Any:
        return create_agent(
            self.llm(),
            tools=ALL_TOOLS + self.mcp_tools + self._workflow_tools,
            system_prompt=make_system_prompt(
                "あなたは環境エネルギー本部のルーターエージェントです。\n"
                "ユーザーの質問を分析し、必要なデータソースを特定して取得します。\n\n"
                "## 対応データソース\n"
                "1. **財務データ** (analyze_financial_data): 売上・利益・発電量の月次データ\n"
                "2. **SFAパイプライン** (analyze_sfa_pipeline): 営業案件・受注見込み\n"
                "3. **社内文書** (search_documents): 事業計画書・議事録・報告書\n"
                "4. **発電実績** (analyze_generation_data): 設備容量・稼働率・トレンド\n"
                "5. **フィードバック** (get_user_feedback_context): 過去のユーザー評価\n\n"
                "## 指示\n"
                "- 質問に応じて適切なツールを1つ以上呼び出してください\n"
                "- 複合的な質問(例:「今期の業績とパイプライン状況」)は複数ツールを使ってください\n"
                "- フィードバックツールを活用し、過去の改善要望を反映してください\n"
                "- 取得したデータをそのまま次のノードに渡してください\n"
            ),
            name="router_agent",
        )

    # -----------------------------------------------------------------
    # Node 2: Analyst — データを構造的に分析し洞察を導出
    # -----------------------------------------------------------------

    @property
    def agent_analyst(self) -> Any:
        return create_agent(
            self.llm(),
            tools=ALL_TOOLS + self.mcp_tools + self._workflow_tools,
            system_prompt=make_system_prompt(
                "あなたは環境エネルギー本部のデータアナリストです。\n"
                "ルーターが収集したデータを分析し、経営判断に有用な洞察を導出します。\n\n"
                "## 分析の観点\n"
                "- **前期比・前年比**: 数値の変化率を計算し、トレンドを特定\n"
                "- **セグメント比較**: 事業セグメント間のパフォーマンス差異を分析\n"
                "- **リスク要因**: 業績悪化リスクやパイプラインの懸念事項を特定\n"
                "- **機会の特定**: 成長が見込まれる領域・案件をハイライト\n"
                "- **CO2削減効果**: 環境インパクトを定量的に評価\n\n"
                "## 出力形式\n"
                "- 定量的な事実を先に記述し、その後に解釈・洞察を付加\n"
                "- 必要に応じてツールで追加データを取得してください\n"
                "- 分析結果は箇条書きで構造化してください\n"
            ),
            name="analyst_agent",
        )

    # -----------------------------------------------------------------
    # Node 3: Reporter — 分析結果を経営レポートとして整形
    # -----------------------------------------------------------------

    @property
    def agent_reporter(self) -> Any:
        return create_agent(
            self.llm(),
            tools=self.mcp_tools + self._workflow_tools,
            system_prompt=make_system_prompt(
                "あなたは環境エネルギー本部のレポートライターです。\n"
                "アナリストの分析結果を基に、経営企画・経営層向けの構造化レポートを作成します。\n\n"
                "## レポート構成\n"
                "1. **エグゼクティブサマリー** (3-5文): 重要なポイントの概要\n"
                "2. **主要指標** (表形式): KPI数値の一覧\n"
                "3. **分析詳細**: セグメント別の状況説明\n"
                "4. **リスクと機会**: 注意点と成長余地\n"
                "5. **アクション提案**: 次のステップの推奨事項\n\n"
                "## 注意事項\n"
                "- Markdown形式で出力してください\n"
                "- 数値には適切な単位を付けてください(百万円、MW、MWh、%等)\n"
                "- 全体で1000文字以内に収めてください\n"
                "- 日本語で回答してください\n"
                "- 不明な点がある場合はその旨を明記してください\n"
            ),
            name="reporter_agent",
        )
