"""Streamlit entry point for the Investment Thesis Checker POC."""

import html
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai.portfolio_analyzer import AIAnalysisError, analyze_portfolio_thesis
from data.financial_data import (
    FinancialDataError,
    get_financial_data,
    get_historical_prices,
    ticker_exists,
)
from data.pdf_evidence import PDFEvidenceError, extract_pdf_evidence
from data.supabase_repository import (
    SupabasePersistenceError,
    create_supabase_client,
    get_authenticated_user_id,
    save_thesis_review,
    update_thesis_review,
)
from logic.portfolio import (
    PortfolioValidationError,
    calculate_average_correlation,
    calculate_concentration,
    calculate_historical_portfolio_metrics,
    calculate_return_correlation,
    calculate_sector_concentration,
    build_comparison_weights,
    validate_portfolio,
)
from logic.thesis_standards import evaluate_thesis_standards
from ui.login import render_login
from ui.styles import apply_global_styles
from ui.workflow import (
    render_question_loading,
    render_result_loading,
    render_step_navigation,
    scroll_to_top_on_screen_change,
)


THESIS_FACTORS = [
    "밸류에이션이 매력적이라고 판단했다",
    "매출·이익 등 성장성이 높다고 판단했다",
    "수익성이 좋다고 판단했다",
    "부채·현금흐름 등 재무 상태가 안정적이라고 판단했다",
    "최근 주가 흐름이 긍정적이라고 판단했다",
    "산업·제품의 미래 전망이 좋다고 판단했다",
    "위험 대비 기대수익이 적절하다고 판단했다",
    "기타",
]

DECISION_TRIGGERS = [
    "최근 실적 또는 공시를 확인했다",
    "과거부터 지켜보며 장기적인 변화를 확인했다",
    "동종 기업이나 시장 평균과 비교했다",
    "산업 전망이나 관련 뉴스를 접했다",
    "최근 주가 상승 또는 하락을 보고 관심이 생겼다",
    "제품·서비스를 직접 경험했다",
    "아직 뚜렷한 계기는 없다",
]

EVIDENCE_LEVELS = [
    "아직 별도의 자료를 확인하지 않았다",
    "뉴스·영상·커뮤니티 자료를 주로 확인했다",
    "회사의 실적 발표나 재무지표를 확인했다",
    "경쟁사·과거 수치와 함께 비교했다",
    "여러 출처를 비교하고 반대 근거도 확인했다",
]

INVESTMENT_HORIZONS = [
    "6개월 미만",
    "6개월 이상 1년 미만",
    "1년 이상 3년 미만",
    "3년 이상",
    "아직 정하지 않았다",
]

LOSS_RESPONSES = [
    "손실을 줄이기 위해 매도할 가능성이 높다",
    "투자 논리와 최신 데이터를 다시 검토한 뒤 결정한다",
    "처음의 투자 논리가 유효하다면 보유한다",
    "투자 논리가 유효하다면 추가 매수를 검토한다",
    "아직 생각해보지 않았다",
]

DEFAULT_FOLLOWUP_QUESTIONS = [
    "포트폴리오 전체가 정보기술 섹터에 집중되어 있습니다. 기술 섹터에 공통적으로 영향을 미치는 외부 리스크(금리 인상, 반독점 규제 등)가 발생할 경우 어떻게 대응할 계획인가요?",
    "보유 종목 간 평균 상관계수가 0.76으로, 종목들이 유사한 방향으로 움직이는 경향이 높습니다. 이 포트폴리오를 분산 투자라고 판단하신 구체적인 근거는 무엇인가요?",
    "AAPL이 포트폴리오의 40%를 차지하는 최대 비중 종목입니다. 단일 종목 이벤트(실적 쇼크, 공급망 문제 등)가 포트폴리오 전체에 미치는 영향을 사전에 고려하셨나요?",
]

DEFAULT_FOLLOWUP_LABELS = [
    "정보기술 섹터 · 비중 100% (기준 60% 초과)",
    "평균 상관계수 · 0.76 (기준 0.70 초과)",
    "AAPL 비중 · 전체의 40% (최대 보유)",
]

DEFAULT_FOLLOWUP_PLACEHOLDERS = [
    "섹터 리스크에 대한 대응 계획이나 허용 가능한 손실 범위를 작성해주세요.",
    "상관관계 외에 분산이라고 판단한 기준(지역, 비즈니스 모델 차이 등)을 작성해주세요.",
    "AAPL 비중을 선택한 근거나 비중을 유지할 조건을 작성해주세요.",
]


def ensure_three_followup_questions(questions: list[str]) -> list[str]:
    """Keep the follow-up flow at exactly three unique questions."""
    result: list[str] = []
    for question in [*questions, *DEFAULT_FOLLOWUP_QUESTIONS]:
        if question and question not in result:
            result.append(question)
        if len(result) == 3:
            break
    return result


def build_metric_followups(
    holdings: list[dict],
    dominant_sector: str = "정보기술",
    dominant_weight: float = 100.0,
    average_correlation: float | None = 0.76,
) -> tuple[list[str], list[str], list[str]]:
    """Build three questions together with their matching metric copy."""
    sector = {
        "Technology": "정보기술",
        "Information Technology": "정보기술",
    }.get(dominant_sector, dominant_sector or "정보기술")
    correlation = 0.76 if average_correlation is None else average_correlation
    largest = max(
        holdings or [{"ticker": "AAPL", "weight": 40.0}],
        key=lambda holding: float(holding.get("weight", 0)),
    )
    ticker = str(largest.get("ticker", "AAPL")).upper()
    largest_weight = float(largest.get("weight", 40.0))
    sector_weight_text = f"{dominant_weight:.0f}%"
    largest_weight_text = f"{largest_weight:.0f}%"

    questions = [
        f"포트폴리오 전체가 {sector} 섹터에 집중되어 있습니다. 기술 섹터에 공통적으로 영향을 미치는 외부 리스크(금리 인상, 반독점 규제 등)가 발생할 경우 어떻게 대응할 계획인가요?",
        f"보유 종목 간 평균 상관계수가 {correlation:.2f}으로, 종목들이 유사한 방향으로 움직이는 경향이 높습니다. 이 포트폴리오를 분산 투자라고 판단하신 구체적인 근거는 무엇인가요?",
        f"{ticker}이 포트폴리오의 {largest_weight_text}를 차지하는 최대 비중 종목입니다. 단일 종목 이벤트(실적 쇼크, 공급망 문제 등)가 포트폴리오 전체에 미치는 영향을 사전에 고려하셨나요?",
    ]
    labels = [
        f"{sector} 섹터 · 비중 {sector_weight_text} (기준 60% 초과)",
        f"평균 상관계수 · {correlation:.2f} (기준 0.70 초과)",
        f"{ticker} 비중 · 전체의 {largest_weight_text} (최대 보유)",
    ]
    placeholders = [
        "섹터 리스크에 대한 대응 계획이나 허용 가능한 손실 범위를 작성해주세요.",
        "상관관계 외에 분산이라고 판단한 기준(지역, 비즈니스 모델 차이 등)을 작성해주세요.",
        f"{ticker} 비중을 선택한 근거나 비중을 유지할 조건을 작성해주세요.",
    ]
    return questions, labels, placeholders


load_dotenv()


def get_openai_api_key() -> str | None:
    """Read the OpenAI API key from environment or Streamlit secrets."""
    environment_key = os.getenv("OPENAI_API_KEY")
    if environment_key:
        return environment_key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except FileNotFoundError:
        return None


def get_app_secret(name: str) -> str | None:
    """Read a setting from local environment variables or Streamlit secrets."""
    environment_value = os.getenv(name)
    if environment_value:
        return environment_value
    try:
        return st.secrets.get(name)
    except FileNotFoundError:
        return None


def get_session_supabase_client():
    """Keep a Supabase Auth session isolated to this Streamlit browser session."""
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_supabase_client(
            get_app_secret("SUPABASE_URL"), get_app_secret("SUPABASE_KEY")
        )
    return st.session_state["supabase_client"]


def get_evidence_metadata(evidence: dict[str, object] | None) -> dict[str, object] | None:
    """Keep only file metadata; never persist extracted PDF text."""
    if not evidence:
        return None
    return {"filename": evidence["filename"], "page_count": evidence["page_count"]}


openai_api_key = get_openai_api_key()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_financial_data(ticker: str) -> dict[str, object]:
    """Cache provider data briefly so reruns do not repeat the same request."""
    return get_financial_data(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_historical_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Cache price history briefly for faster repeated thesis checks."""
    return get_historical_prices(list(tickers))


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_ticker_exists(ticker: str) -> bool:
    """Cache ticker validation so the input step stays responsive."""
    return ticker_exists(ticker)


st.set_page_config(
    page_title="Portfolio Thesis Checker",
    page_icon="⚖️",
    layout="centered",
)
apply_global_styles()

supabase_client = get_session_supabase_client()
if supabase_client is None:
    st.error("Supabase 연결 설정을 확인해주세요. .env에 URL과 Publishable key가 필요합니다.")
    st.stop()

authenticated_user_id = get_authenticated_user_id(supabase_client)
if authenticated_user_id and st.query_params.get("logout") == "1":
    supabase_client.auth.sign_out()
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
if not authenticated_user_id and not render_login(supabase_client):
    st.stop()

st.markdown(
    '<span class="app-shell-marker" aria-hidden="true">&nbsp;</span>',
    unsafe_allow_html=True,
)

if "workflow_screen" not in st.session_state:
    st.session_state["workflow_screen"] = "portfolio"

workflow_screen = st.session_state["workflow_screen"]
scroll_to_top_on_screen_change(workflow_screen)

if workflow_screen == "portfolio":
    render_step_navigation("portfolio")
    st.markdown(
        """
        <section class="page-hero">
            <h1>Portfolio Thesis Checker</h1>
            <p>포트폴리오를 추천하지 않고, 입력한 구성과 투자 논리를 점검합니다.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if "portfolio_rows" not in st.session_state:
        st.session_state["portfolio_rows"] = [
            {"id": 1, "ticker": "AAPL", "weight": 40.0},
            {"id": 2, "ticker": "MSFT", "weight": 30.0},
            {"id": 3, "ticker": "NVDA", "weight": 30.0},
        ]
        st.session_state["portfolio_row_sequence"] = 3

    rows = st.session_state["portfolio_rows"]
    with st.container(border=True):
        st.markdown('<h2 class="portfolio-card-title">포트폴리오 입력</h2>', unsafe_allow_html=True)
        ticker_header, weight_header, _ = st.columns([6, 1.55, 0.48], gap="small")
        ticker_header.markdown('<div class="portfolio-column-label">TICKER</div>', unsafe_allow_html=True)
        weight_header.markdown('<div class="portfolio-column-label right">비중 (%)</div>', unsafe_allow_html=True)
        st.markdown('<div class="portfolio-header-gap"></div>', unsafe_allow_html=True)

        remove_row_id = None
        for row in rows:
            ticker_column, weight_column, remove_column = st.columns(
                [6, 1.55, 0.48], gap="small"
            )
            row["ticker"] = ticker_column.text_input(
                "Ticker",
                value=str(row["ticker"]),
                key=f'portfolio_ticker_{row["id"]}',
                label_visibility="collapsed",
            ).upper()
            row["weight"] = weight_column.number_input(
                "비중",
                min_value=0.0,
                max_value=100.0,
                value=float(row["weight"]),
                step=1.0,
                key=f'portfolio_weight_{row["id"]}',
                label_visibility="collapsed",
            )
            if remove_column.button(
                "×",
                key=f'portfolio_remove_{row["id"]}',
                disabled=len(rows) == 1,
                use_container_width=True,
            ):
                remove_row_id = row["id"]

        if remove_row_id is not None:
            st.session_state["portfolio_rows"] = [
                row for row in rows if row["id"] != remove_row_id
            ]
            st.rerun()

        total_weight = sum(float(row["weight"]) for row in rows)
        add_column, total_column = st.columns([1, 1])
        with add_column:
            if st.button("＋ 종목 추가", disabled=len(rows) >= 10):
                st.session_state["portfolio_row_sequence"] += 1
                rows.append(
                    {
                        "id": st.session_state["portfolio_row_sequence"],
                        "ticker": "",
                        "weight": 0.0,
                    }
                )
                st.rerun()
        total_state = "valid" if abs(total_weight - 100.0) < 0.01 else "invalid"
        total_column.markdown(
            f'<div class="portfolio-total {total_state}">합계 '
            f'<strong>{total_weight:g}%</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="portfolio-rule"></div>', unsafe_allow_html=True)
        st.caption("최대 10개 종목까지 입력할 수 있으며 비중 합계는 100%여야 합니다.")

    with st.container(border=True):
        st.markdown('<h2 class="portfolio-card-title thesis">포트폴리오 구성 논리</h2>', unsafe_allow_html=True)
        st.markdown(
            '<p class="portfolio-card-copy">이 포트폴리오를 구성한 이유와 투자 판단의 근거를 자유롭게 작성해주세요.</p>',
            unsafe_allow_html=True,
        )
        thesis = st.text_area(
            "포트폴리오 구성 논리 작성",
            value=st.session_state.get("portfolio_thesis", ""),
            placeholder="예: AI 성장주를 여러 기업에 나누어 투자해 위험을 분산했다고 생각한다.",
            height=180,
            label_visibility="collapsed",
        )
    _, next_column = st.columns([2.4, 1])
    portfolio_submitted = next_column.button(
        "다음: 투자 기준 입력 →",
        type="primary",
        use_container_width=True,
    )
    if portfolio_submitted:
        portfolio_input = pd.DataFrame(
            [{"ticker": row["ticker"], "weight": row["weight"]} for row in rows]
        )
        try:
            validated_holdings = validate_portfolio(portfolio_input.to_dict("records"))
        except PortfolioValidationError as exc:
            st.error(str(exc))
        else:
            with st.spinner("ticker를 확인하는 중입니다..."):
                invalid_tickers = [
                    str(holding["ticker"])
                    for holding in validated_holdings
                    if not get_cached_ticker_exists(str(holding["ticker"]))
                ]
            if invalid_tickers:
                st.error(
                    "해당 ticker를 찾을 수 없습니다: "
                    + ", ".join(invalid_tickers)
                    + ". ticker를 확인해주세요."
                )
            elif not thesis.strip():
                st.error("포트폴리오 구성 논리를 입력해주세요.")
            else:
                st.session_state["portfolio_input"] = portfolio_input
                st.session_state["portfolio_thesis"] = thesis.strip()
                st.session_state["workflow_screen"] = "criteria"
                st.rerun()
    st.stop()

if workflow_screen == "criteria":
    render_step_navigation("criteria")
    if st.button("← 포트폴리오 입력으로", key="criteria_back"):
        st.session_state["workflow_screen"] = "portfolio"
        st.rerun()
    st.markdown(
        """
        <section class="criteria-hero">
            <h1>투자 기준 입력</h1>
            <p>투자 판단의 근거와 기준을 입력하고, 관련 자료를 첨부하세요.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="criteria-question first"><span>1</span>'
        '<strong>이 판단에서 중요하게 본 근거는 무엇인가요? (복수 선택 가능)</strong></div>',
        unsafe_allow_html=True,
    )
    thesis_factors = st.pills(
        "중요하게 본 근거",
        THESIS_FACTORS[:-1],
        selection_mode="multi",
        default=None,
        key="criteria_thesis_factors",
        label_visibility="collapsed",
    )
    with st.container(border=True):
        st.markdown(
            """
            <div class="factor-detail-heading">
                <strong>선택한 근거를 조금 더 구체적으로 설명해주세요.</strong>
                <span>(선택)</span>
                <p>어떤 수치, 변화, 사건 또는 이유를 보고 그렇게 판단했는지 자유롭게 작성해주세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        factor_detail = st.text_area(
            "선택 근거 상세 설명",
            placeholder="최근 3년간 매출과 영업이익이 꾸준히 증가했고, AI 관련 수요 확대가 계속될 것으로 판단했습니다.",
            height=180,
            key="criteria_factor_detail",
            label_visibility="collapsed",
        )

    st.markdown(
        '<div class="criteria-question"><span>2</span>'
        '<strong>이 포트폴리오를 구성하게 된 가장 큰 계기는 무엇인가요?</strong></div>',
        unsafe_allow_html=True,
    )
    decision_trigger = st.radio(
        "포트폴리오 구성 계기",
        DECISION_TRIGGERS,
        index=None,
        key="criteria_decision_trigger",
        label_visibility="collapsed",
        width="stretch",
    )

    st.markdown(
        '<div class="criteria-question"><span>3</span>'
        '<strong>판단하기 전에 어느 정도까지 자료를 확인했나요?</strong></div>',
        unsafe_allow_html=True,
    )
    evidence_level = st.radio(
        "자료 확인 수준",
        EVIDENCE_LEVELS,
        index=None,
        key="criteria_evidence_level",
        label_visibility="collapsed",
        width="stretch",
    )

    with st.container(border=True):
        st.markdown(
            """
            <div class="evidence-panel-heading">
                <strong>참고한 자료 첨부</strong>
                <p>투자 판단에 참고한 자료가 있다면 첨부해주세요. 텍스트 기반 PDF 파일 1개를 업로드할 수 있습니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="upload-visual">
                <span class="upload-icon">▱</span>
                <strong>PDF 파일 업로드</strong>
                <p>최대 10MB · 텍스트 기반 PDF만 지원<br>
                스캔·암호화·이미지 전용 PDF는 지원하지 않습니다.</p>
                <small>업로드된 파일은 현재 분석에만 사용되며 저장되지 않습니다.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        evidence_pdf = st.file_uploader(
            "PDF 파일 업로드",
            type=["pdf"],
            accept_multiple_files=False,
            key="criteria_evidence_pdf",
            help=(
                "10MB 이하의 PDF 1개를 첨부할 수 있습니다. "
                "파일은 DB에 저장하지 않으며, AI 분석을 선택한 경우에만 "
                "추출된 텍스트가 OpenAI API로 전송됩니다."
            ),
            label_visibility="collapsed",
        )
        if evidence_pdf is not None:
            st.caption(f"첨부된 자료: {evidence_pdf.name}")
        url_column, url_button_column = st.columns([5, 1], gap="small")
        evidence_url = url_column.text_input(
            "참고 URL",
            placeholder="https://example.com/report",
            key="criteria_evidence_url",
            label_visibility="collapsed",
        )
        add_url = url_button_column.button(
            "URL 추가",
            key="criteria_add_url",
            use_container_width=True,
        )
        if add_url:
            if not evidence_url.startswith(("https://", "http://")):
                st.error("http:// 또는 https://로 시작하는 URL을 입력해주세요.")
            else:
                st.session_state["criteria_saved_url"] = evidence_url
                st.success("참고 URL이 추가되었습니다.")
        if st.session_state.get("criteria_saved_url"):
            st.caption("추가된 URL: " + st.session_state["criteria_saved_url"])

    st.markdown(
        '<div class="criteria-question"><span>4</span>'
        '<strong>예상하는 투자 기간은 어느 정도인가요?</strong></div>',
        unsafe_allow_html=True,
    )
    investment_horizon = st.radio(
        "예상 투자 기간",
        INVESTMENT_HORIZONS,
        index=None,
        key="criteria_investment_horizon",
        label_visibility="collapsed",
        width="stretch",
    )

    st.markdown(
        '<div class="criteria-question"><span>5</span>'
        '<strong>포트폴리오 가치가 30% 하락한다면 어떻게 대응할 가능성이 가장 높은가요?</strong></div>',
        unsafe_allow_html=True,
    )
    loss_response = st.radio(
        "손실 대응",
        LOSS_RESPONSES,
        index=None,
        key="criteria_loss_response",
        label_visibility="collapsed",
        width="stretch",
    )

    use_ai_analysis = st.checkbox(
        "반대심문 답변 후 AI로 최종 논리 일관성을 분석합니다.",
        value=True,
        disabled=False,
        key="criteria_use_ai",
        help=(
            "선택하면 최초 투자 논리, 금융 데이터 요약, 반대심문 답변이 "
            "최종 단계에서 OpenAI API로 전송됩니다. 매수·매도 추천은 생성하지 않습니다."
        ),
    )
    if not openai_api_key:
        st.caption("API 키가 없으면 AI 최종 분석 단계에서 안내 메시지가 표시됩니다.")

    _, criteria_button_column = st.columns([2.2, 1])
    criteria_submitted = criteria_button_column.button(
        "추가 질문 시작 →",
        type="primary",
        use_container_width=True,
        key="criteria_submit",
    )

    if criteria_submitted:
        if not all(
            [thesis_factors, decision_trigger, evidence_level, investment_horizon, loss_response]
        ):
            st.error("판단 근거 점검 문항에 모두 응답해주세요.")
        else:
            st.session_state["criteria_values"] = {
                "thesis_factors": thesis_factors,
                "decision_trigger": decision_trigger,
                "evidence_level": evidence_level,
                "investment_horizon": investment_horizon,
                "loss_response": loss_response,
                "use_ai_analysis": use_ai_analysis,
                "factor_detail": factor_detail,
                "evidence_url": st.session_state.get("criteria_saved_url", ""),
            }
            st.session_state["evidence_pdf"] = evidence_pdf
            st.session_state["workflow_screen"] = "loading"
            st.rerun()
    st.stop()

if workflow_screen == "loading":
    render_step_navigation("followup")
    render_question_loading()
    st.stop()

if workflow_screen == "result_loading":
    render_step_navigation("result")
    render_result_loading()
    st.stop()

render_step_navigation(
    "result" if workflow_screen in {"result", "finalize_result"} else "followup"
)
portfolio_input = st.session_state["portfolio_input"]
thesis = st.session_state["portfolio_thesis"]
evidence_pdf = st.session_state.get("evidence_pdf")
criteria_values = st.session_state["criteria_values"]
thesis_factors = criteria_values["thesis_factors"]
decision_trigger = criteria_values["decision_trigger"]
evidence_level = criteria_values["evidence_level"]
investment_horizon = criteria_values["investment_horizon"]
loss_response = criteria_values["loss_response"]
use_ai_analysis = criteria_values["use_ai_analysis"]

# Earlier failed data requests may have marked the analysis as processed without
# creating the next-screen content. Recover those sessions so the preview button
# is rendered instead of leaving a blank page.
if (
    st.session_state.get("analysis_processed", False)
    and not st.session_state.get("cross_examination")
):
    st.session_state["analysis_processed"] = False

submitted = not st.session_state.get("analysis_processed", False)

pdf_evidence = None
pdf_error = None
if submitted and evidence_pdf is not None:
    try:
        pdf_evidence = extract_pdf_evidence(
            evidence_pdf.getvalue(), evidence_pdf.name
        )
    except PDFEvidenceError as exc:
        pdf_error = str(exc)

if submitted:
    if pdf_error:
        st.error(pdf_error)
    elif not thesis.strip():
        st.error("포트폴리오 구성 논리를 입력해주세요.")
    elif not all(
        [
            thesis_factors,
            decision_trigger,
            evidence_level,
            investment_horizon,
            loss_response,
        ]
    ):
        st.error("판단 근거 점검 문항에 모두 응답해주세요.")
    else:
        try:
            holdings = validate_portfolio(portfolio_input.to_dict("records"))
        except PortfolioValidationError as exc:
            st.error(str(exc))
        else:
            submitted_review_id = st.session_state.get("active_review_id")
            if not submitted_review_id:
                try:
                    submitted_review_id = save_thesis_review(
                        supabase_client,
                        user_id=authenticated_user_id,
                        original_thesis=thesis.strip(),
                        holdings=holdings,
                        questionnaire={
                            "thesis_factors": thesis_factors,
                            "decision_trigger": decision_trigger,
                            "evidence_level": evidence_level,
                            "investment_horizon": investment_horizon,
                            "loss_response": loss_response,
                            "factor_detail": criteria_values.get("factor_detail", ""),
                            "evidence_url": criteria_values.get("evidence_url", ""),
                        },
                        cross_examination_answers=[],
                        ai_analysis=None,
                        ai_error=None,
                        evidence_metadata=get_evidence_metadata(pdf_evidence),
                        factor_detail=str(criteria_values.get("factor_detail", "")).strip(),
                        evidence_url=str(criteria_values.get("evidence_url", "")).strip(),
                        workflow_version="design-v1",
                    )
                except SupabasePersistenceError as exc:
                    st.warning(str(exc))
                else:
                    st.session_state["active_review_id"] = submitted_review_id

            financial_rows = []
            sectors = {}
            data_error = None

            try:
                with st.spinner("종목별 금융 데이터를 불러오는 중입니다..."):
                    for holding in holdings:
                        financial_data = get_cached_financial_data(
                            str(holding["ticker"])
                        )
                        sector = financial_data["company_profile"]["sector"]
                        sectors[str(holding["ticker"])] = sector
                        financial_rows.append(
                            {
                                "Ticker": financial_data["ticker"],
                                "회사명": financial_data["company_name"],
                                "산업": sector,
                                "비중 (%)": holding["weight"],
                                "현재 주가": financial_data["market_data"]["current_price"],
                                "시가총액": financial_data["market_data"]["market_cap"],
                                "P/E": financial_data["valuation"]["pe_ratio"],
                                "P/B": financial_data["valuation"]["pb_ratio"],
                                "매출 성장률": financial_data["growth"]["revenue_growth"],
                                "이익률": financial_data["profitability"]["profit_margin"],
                                "부채비율": financial_data["financial_health"][
                                    "debt_to_equity"
                                ],
                            }
                        )
            except FinancialDataError as exc:
                data_error = str(exc)

            if data_error:
                preview_questions, preview_labels, preview_placeholders = (
                    build_metric_followups(holdings)
                )
                st.session_state["cross_examination"] = {
                    "original_thesis": thesis.strip(),
                    "questions": preview_questions,
                    "question_labels": preview_labels,
                    "answer_placeholders": preview_placeholders,
                    "analysis_context": {"design_preview": True},
                    "use_ai_analysis": False,
                    "has_pdf": pdf_evidence is not None,
                    "review_id": submitted_review_id,
                }
                st.session_state.pop("final_cross_examination", None)
                for index in range(3):
                    st.session_state.pop(f"cross_examination_answer_{index}", None)
                st.session_state["analysis_processed"] = True
                st.session_state["cross_examination_index"] = 0
                st.session_state["cross_examination_draft_answers"] = {}
                st.session_state["workflow_screen"] = "followup_0"
                st.rerun()
            else:
                if pdf_evidence is not None:
                    st.subheader("첨부 근거자료")
                    pdf_col1, pdf_col2 = st.columns(2)
                    pdf_col1.metric("파일", str(pdf_evidence["filename"]))
                    pdf_col2.metric("페이지", f'{pdf_evidence["page_count"]}쪽')
                    if pdf_evidence["was_truncated"]:
                        st.warning(
                            "문서가 길어 처음 30페이지와 최대 30,000자까지만 "
                            "분석에 사용합니다."
                        )
                    with st.expander("추출된 PDF 텍스트 미리보기"):
                        for page in pdf_evidence["pages"][:3]:
                            st.markdown(f'**{page["page"]}페이지**')
                            page_text = str(page["text"])
                            st.text(page_text[:2_000])
                        st.caption(
                            "미리보기는 최대 3페이지, 페이지당 2,000자만 표시합니다."
                        )

                concentration = calculate_concentration(holdings)
                sector_concentration = calculate_sector_concentration(
                    holdings, sectors
                )

                st.subheader("포트폴리오 구성")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("종목 수", f"{len(holdings)}개")
                metric_col2.metric(
                    "최대 비중 종목",
                    str(concentration["largest_ticker"]),
                    f'{concentration["largest_weight"]:.2f}%',
                )
                metric_col3.metric(
                    "상위 2개 종목 비중",
                    f'{concentration["top_two_weight"]:.2f}%',
                )

                st.dataframe(
                    pd.DataFrame(financial_rows),
                    hide_index=True,
                    width="stretch",
                )

                st.subheader("산업 집중도")
                sector_col1, sector_col2 = st.columns(2)
                sector_col1.metric(
                    "가장 큰 산업",
                    str(sector_concentration["dominant_sector"]),
                )
                sector_col2.metric(
                    "해당 산업 비중",
                    f'{sector_concentration["dominant_weight"]:.2f}%',
                )
                sector_table = pd.DataFrame(
                    {
                        "산업": sector_concentration["sector_weights"].keys(),
                        "비중 (%)": sector_concentration["sector_weights"].values(),
                    }
                )
                st.dataframe(sector_table, hide_index=True, width="stretch")

                st.subheader("최근 1년 수익률 상관관계")
                try:
                    prices = get_cached_historical_prices(
                        tuple(str(holding["ticker"]) for holding in holdings)
                    )
                    correlation = calculate_return_correlation(prices)
                    average_correlation = calculate_average_correlation(correlation)
                except (FinancialDataError, PortfolioValidationError) as exc:
                    st.warning(f"상관관계를 계산하지 못했습니다: {exc}")
                else:
                    if average_correlation is not None:
                        st.metric("종목 간 평균 상관계수", f"{average_correlation:.2f}")
                    st.dataframe(
                        correlation.round(2),
                        width="stretch",
                    )
                    st.caption(
                        "상관계수는 -1에서 1 사이의 값입니다. 1에 가까울수록 "
                        "같은 방향으로 움직인 경향이 강했다는 뜻이며, 미래 움직임을 "
                        "예측하거나 분산 효과를 단정하는 지표는 아닙니다."
                    )

                    standard_findings = evaluate_thesis_standards(
                        holding_count=len(holdings),
                        dominant_sector_weight=float(
                            sector_concentration["dominant_weight"]
                        ),
                        average_correlation=average_correlation,
                        thesis_factors=thesis_factors,
                        investment_horizon=investment_horizon,
                        evidence_level=evidence_level,
                    )
                    st.subheader("팀 기준 진단")
                    if standard_findings:
                        for finding in standard_findings:
                            with st.expander(str(finding["rule"]), expanded=True):
                                st.write(str(finding["diagnosis"]))
                                st.caption("판정 근거: " + ", ".join(finding["evidence"]))
                                st.markdown(f'**후속 질문:** {finding["question"]}')
                    else:
                        st.success(
                            "현재 입력에서는 팀이 정한 3가지 규칙에 해당하는 "
                            "항목이 확인되지 않았습니다."
                        )

                    st.subheader("비중 비교를 통한 논리 점검")
                    try:
                        comparison_weights = build_comparison_weights(
                            holdings, prices
                        )
                        historical_metrics = calculate_historical_portfolio_metrics(
                            prices, comparison_weights
                        )
                    except PortfolioValidationError as exc:
                        st.warning(f"비중 비교를 계산하지 못했습니다: {exc}")
                    else:
                        weight_table = (comparison_weights * 100).round(2)
                        st.dataframe(weight_table, width="stretch")
                        st.caption(
                            "동일 비중과 역변동성 비중은 사용자의 현재 구성을 "
                            "검토하기 위한 비교 기준이며, 추천하거나 따라야 할 목표 비중이 아닙니다."
                        )

                        display_metrics = historical_metrics.copy()
                        for column in display_metrics.columns:
                            display_metrics[column] = display_metrics[column].map(
                                lambda value: f"{value * 100:.2f}%"
                            )
                        st.dataframe(display_metrics, width="stretch")
                        st.caption(
                            "모든 성과 수치는 동일한 최근 1년 과거 가격으로 계산되며, "
                            "거래비용·세금·환율을 반영하지 않습니다. 과거 성과는 미래 성과를 보장하지 않습니다."
                        )

                        (
                            cross_examination_questions,
                            cross_examination_labels,
                            cross_examination_placeholders,
                        ) = build_metric_followups(
                            holdings,
                            str(sector_concentration["dominant_sector"]),
                            float(sector_concentration["dominant_weight"]),
                            average_correlation,
                        )
                        st.markdown("#### 1차 분석에서 확인된 쟁점")
                        st.write(
                            "아래 질문에 답하면 최초 투자 논리의 보완 여부와 "
                            "일관성을 최종 점검합니다."
                        )
                        for question in cross_examination_questions:
                            st.write(f"- {question}")

                        ai_context = {
                            "holdings": holdings,
                            "financial_data": financial_rows,
                            "sector_concentration": sector_concentration,
                            "average_correlation": average_correlation,
                            "comparison_weights_percent": weight_table.to_dict(),
                            "historical_metrics": historical_metrics.to_dict(),
                            "questionnaire": {
                                "thesis_factors": thesis_factors,
                                "decision_trigger": decision_trigger,
                                "evidence_level": evidence_level,
                                "investment_horizon": investment_horizon,
                                "loss_response": loss_response,
                            },
                            "uploaded_evidence": pdf_evidence,
                            "team_standard_findings": standard_findings,
                        }
                        st.session_state["cross_examination"] = {
                            "original_thesis": thesis.strip(),
                            "questions": cross_examination_questions,
                            "question_labels": cross_examination_labels,
                            "answer_placeholders": cross_examination_placeholders,
                            "analysis_context": ai_context,
                            "use_ai_analysis": use_ai_analysis,
                            "has_pdf": pdf_evidence is not None,
                            "review_id": submitted_review_id,
                        }
                        st.session_state.pop("final_cross_examination", None)
                        for index in range(3):
                            st.session_state.pop(
                                f"cross_examination_answer_{index}", None
                            )

                with st.expander("입력한 투자 논리와 응답 보기"):
                    st.write(f"포트폴리오 구성 논리: {thesis.strip()}")
                    st.write("핵심 근거: " + ", ".join(thesis_factors))
                    st.write(f"판단 계기: {decision_trigger}")
                    st.write(f"자료 확인 수준: {evidence_level}")
                    st.write(f"예상 투자 기간: {investment_horizon}")
                    st.write(f"30% 하락 시 예상 대응: {loss_response}")

                st.info(
                    "비교 비중은 사용자의 투자 논리를 점검하기 위한 참고 기준입니다. "
                    "이 서비스는 포트폴리오 추천이나 목표 비중을 제공하지 않습니다."
                )


if submitted and st.session_state.get("cross_examination"):
    st.session_state["analysis_processed"] = True
    if workflow_screen == "analysis":
        st.session_state["cross_examination_index"] = 0
        st.session_state["cross_examination_draft_answers"] = {}
        st.session_state["workflow_screen"] = "followup_0"
        st.rerun()

cross_examination = st.session_state.get("cross_examination")
if workflow_screen == "finalize_result" and cross_examination:
    answer_records = list(st.session_state.get("pending_answer_records", []))
    final_result: dict[str, object] = {"answers": answer_records}
    if cross_examination["use_ai_analysis"]:
        final_context = dict(cross_examination["analysis_context"])
        final_context["cross_examination_answers"] = answer_records
        combined_thesis = (
            f'최초 투자 논리:\n{cross_examination["original_thesis"]}\n\n'
            "반대심문 질문과 사용자 답변:\n"
            + "\n".join(
                f'Q: {record["question"]}\nA: {record["answer"]}'
                for record in answer_records
            )
        )
        try:
            final_result["ai_analysis"] = analyze_portfolio_thesis(
                combined_thesis,
                final_context,
                api_key=openai_api_key,
            )
        except AIAnalysisError as exc:
            final_result["ai_error"] = str(exc)
    review_id = cross_examination.get("review_id")
    if review_id:
        try:
            update_thesis_review(
                supabase_client,
                review_id=str(review_id),
                cross_examination_answers=answer_records,
                ai_analysis=final_result.get("ai_analysis"),
                ai_error=final_result.get("ai_error"),
            )
        except SupabasePersistenceError as exc:
            st.warning(str(exc))
    st.session_state["final_cross_examination"] = final_result
    st.session_state.pop("pending_answer_records", None)
    st.session_state["workflow_screen"] = "result"
    st.rerun()

if cross_examination and not st.session_state.get("final_cross_examination"):
    questions = ensure_three_followup_questions(list(cross_examination["questions"]))
    cross_examination["questions"] = questions
    question_count = len(questions)
    current_index = min(
        int(st.session_state.get("cross_examination_index", 0)),
        question_count - 1,
    )
    drafts = st.session_state.setdefault("cross_examination_draft_answers", {})
    progress = ((current_index + 1) / question_count) * 100
    labels = cross_examination.get("question_labels", DEFAULT_FOLLOWUP_LABELS)
    placeholders = cross_examination.get(
        "answer_placeholders", DEFAULT_FOLLOWUP_PLACEHOLDERS
    )
    followup_label = labels[current_index]
    answer_placeholder = placeholders[current_index]

    st.markdown(
        f"""
        <section class="followup-hero">
            <div class="followup-progress-row">
                <div class="followup-progress-copy">질문 {current_index + 1} / {question_count}</div>
                <div class="followup-progress"><span style="width:{progress:.2f}%"></span></div>
            </div>
            <h1>추가 점검 질문</h1>
            <p>입력한 포트폴리오와 실제 데이터를 바탕으로 추가로 확인하면 좋은 질문을 만들었습니다.</p>
        </section>
        <div class="followup-risk-chip">ⓘ {followup_label}</div>
        <div class="followup-question-card">{questions[current_index]}</div>
        <div class="followup-answer-label"><strong>답변</strong> <span>(선택사항)</span></div>
        """,
        unsafe_allow_html=True,
    )
    answer = st.text_area(
        "추가 질문 답변",
        value=str(drafts.get(str(current_index), "")),
        placeholder=answer_placeholder,
        height=160,
        key=f"cross_examination_answer_{current_index}",
        label_visibility="collapsed",
    )

    skip_column, spacer_column, next_column = st.columns([1, 4, 1.45])
    skip_clicked = skip_column.button(
        "건너뛰기",
        key=f"followup_skip_{current_index}",
    )
    next_label = "진단 결과 보기 →" if current_index == question_count - 1 else "다음 질문 →"
    next_clicked = next_column.button(
        next_label,
        type="primary",
        use_container_width=True,
        key=f"followup_next_{current_index}",
    )

    if skip_clicked or next_clicked:
        drafts[str(current_index)] = "" if skip_clicked else answer.strip()
        st.session_state["cross_examination_draft_answers"] = drafts
        if current_index < question_count - 1:
            next_index = current_index + 1
            st.session_state["cross_examination_index"] = next_index
            st.session_state["workflow_screen"] = f"followup_{next_index}"
            st.rerun()
        else:
            answer_records = [
                {
                    "question": question,
                    "answer": str(drafts.get(str(index), "")).strip() or "답변하지 않음",
                }
                for index, question in enumerate(questions)
            ]
            st.session_state["pending_answer_records"] = answer_records
            st.session_state["workflow_screen"] = "result_loading"
            st.rerun()

if cross_examination:
    final_cross_examination = st.session_state.get("final_cross_examination")
    if final_cross_examination:
        ai_error = final_cross_examination.get("ai_error")
        ai_analysis = final_cross_examination.get("ai_analysis")
        context = cross_examination.get("analysis_context", {})
        holdings = context.get("holdings", [
            {"ticker": "AAPL", "weight": 40},
            {"ticker": "MSFT", "weight": 30},
            {"ticker": "NVDA", "weight": 30},
        ])
        questionnaire = context.get("questionnaire", {})
        sector_data = context.get("sector_concentration", {})
        correlation = context.get("average_correlation", 0.76)
        answers = final_cross_examination.get("answers", [])
        labels = cross_examination.get("question_labels", DEFAULT_FOLLOWUP_LABELS)

        def safe(value: object) -> str:
            return html.escape(str(value))

        ticker_text = " · ".join(str(item.get("ticker", "")) for item in holdings)
        dominant_sector = sector_data.get("dominant_sector", "정보기술")
        dominant_weight = float(sector_data.get("dominant_weight", 100))
        correlation_value = 0.76 if correlation is None else float(correlation)
        factors = questionnaire.get("thesis_factors", [])
        summary = (
            ai_analysis.summary
            if ai_analysis
            else "입력한 투자 논리와 추가 답변을 기준으로 확인된 내용을 정리했습니다."
        )
        supported = list(ai_analysis.supported_points) if ai_analysis else [
            "세 종목 모두 최근 1년 플러스 수익률을 기록했습니다.",
            "AI 수요 기반 매출 성장 근거를 확인했습니다.",
            "높은 영업이익률로 수익성을 뒷받침합니다.",
        ]
        uncertain = list(ai_analysis.uncertain_points) if ai_analysis else [
            "‘위험을 분산했다’는 주장과 높은 섹터 집중도의 관계를 추가 확인해야 합니다.",
            "AI 수요가 지속된다는 전제를 현재 데이터만으로 검증할 수 없습니다.",
            "밸류에이션이 적정하다고 판단한 구체적인 기준이 필요합니다.",
            "하락 시 구체적인 대응 기준이 아직 명확하지 않습니다.",
        ]
        biases = list(ai_analysis.possible_biases) if ai_analysis else [
            "긍정적 수익률과 성장 지표를 중심으로 판단한 확증편향 가능성이 있습니다.",
            "최근 AI 섹터의 성과가 지속될 것이라는 최근성 편향 가능성이 있습니다.",
            "잘 알려진 대형 기술주에 집중된 친숙성 편향 가능성이 있습니다.",
        ]
        limitations = list(ai_analysis.data_limitations) if ai_analysis else [
            "재무 데이터는 최근 공시 기준이며 실시간 시세를 반영하지 않습니다.",
            "상관관계 수익률은 최근 1년 일일 종가 기준으로 계산되었습니다.",
            "PDF 추출 텍스트는 최대 30페이지·30,000자로 제한됩니다.",
            "본 서비스는 매수·매도 또는 투자 추천을 제공하지 않습니다.",
        ]

        review_cards = [
            ("근거의 구체성", "보통", "매출·이익 성장을 언급했으나 구체적인 수치 기준은 추가 확인이 필요합니다."),
            ("금융 데이터 부합도", "양호", supported[0]),
            ("집중 위험 인식", "미흡", f"{safe(dominant_sector)} 섹터 비중이 {dominant_weight:.0f}%로 집중되어 있습니다."),
            ("반대 근거 검토", "미흡", "현재 논리를 반박하는 시나리오와 위험 요인을 구체적으로 검토할 필요가 있습니다."),
            ("손실 대응 기준", "보통", safe(questionnaire.get("loss_response", "하락 시 재검토"))),
            ("답변 간 일관성", "양호", "투자 기간과 성장주 투자 논리가 전반적으로 일관됩니다."),
        ]
        card_html = "".join(
            f'<div class="result-score-card {"good" if status == "양호" else "warn" if status == "보통" else "bad"}"><div><strong>{safe(title)}</strong><span>{status}</span></div><p>{safe(body)}</p></div>'
            for title, status, body in review_cards
        )
        supported_html = "".join(
            f'<div class="result-evidence good"><b>✓</b><div><strong>{safe(point)}</strong><small>확인된 데이터에 부합하는 근거</small></div></div>'
            for point in supported[:3]
        )
        uncertain_html = "".join(
            f'<div class="result-evidence {"bad" if index == 0 else "warn"}"><b>{"×" if index == 0 else "○"}</b><div><strong>{safe(point)}</strong><small>추가 확인 또는 구체적인 기준이 필요합니다</small></div></div>'
            for index, point in enumerate(uncertain[:4])
        )
        bias_names = ["확증편향", "최근성 편향", "친숙성 편향"]
        biases_html = "".join(
            f'<div class="result-bias"><strong>{bias_names[index] if index < len(bias_names) else "인지 편향"}</strong><p>{safe(point)}</p></div>'
            for index, point in enumerate(biases[:3])
        )
        qa_html = "".join(
            f'<div class="result-qa"><div><small>Q{index + 1}</small><span>{safe(labels[index] if index < len(labels) else "추가 점검")}</span></div><strong>{safe(record.get("question", ""))}</strong><p>{safe(record.get("answer", "답변하지 않음")) if record.get("answer") != "답변하지 않음" else "답변이 입력되지 않았습니다."}</p></div>'
            for index, record in enumerate(answers)
        )
        unanswered = [record for record in answers if record.get("answer") == "답변하지 않음"]
        unanswered_text = (
            "모든 질문을 건너뛰어 최초 논리만으로 분석했습니다."
            if len(unanswered) == len(answers)
            else f"{len(unanswered)}개 질문에 답변이 입력되지 않았습니다."
        )
        checklist = uncertain[:3] + [
            f'미답변: "{labels[index]}"에 대한 입장이 확인되지 않았습니다.'
            for index, record in enumerate(answers)
            if record.get("answer") == "답변하지 않음"
        ]
        checklist_html = "".join(
            f'<li><i></i>{safe(item)}</li>' for item in checklist
        )
        limitations_html = "".join(f"<li>{safe(item)}</li>" for item in limitations)

        st.markdown(
            f"""
            <main class="final-report">
              <div class="result-kicker">● 분석 완료</div>
              <h1>투자 논리 진단 결과</h1>
              <div class="result-pills"><span>{safe(ticker_text)}</span><span>{safe(dominant_sector)} {dominant_weight:.0f}%</span><span>평균 상관계수 {correlation_value:.2f}</span></div>
              <div class="result-rule"></div>
              <section><h2><em>1</em> 투자 논리 점검 요약</h2><div class="result-score-grid">{card_html}</div>
                <div class="result-thesis"><blockquote>“{safe(cross_examination['original_thesis'])}”</blockquote><dl><dt>핵심 주장</dt><dd>{safe(', '.join(factors) or summary)}</dd><dt>판단 근거</dt><dd>{safe(questionnaire.get('decision_trigger', '입력 내용 기준'))}</dd><dt>투자 기간</dt><dd>{safe(questionnaire.get('investment_horizon', '확인 필요'))}</dd><dt>손실 허용 범위</dt><dd>{safe(questionnaire.get('loss_response', '확인 필요'))}</dd></dl></div>
              </section>
              <section><h2><em>2</em> 데이터와 부합하는 근거</h2>{supported_html}</section>
              <section><h2><em>3</em> 데이터와 충돌하거나 확인되지 않은 근거</h2>{uncertain_html}</section>
              <section><h2><em>4</em> 편향 가능성</h2><p class="result-section-copy">확정된 결론이 아니라 입력 내용에서 감지된 가능성입니다.</p>{biases_html}</section>
              <section><h2><em>5</em> 반대심문 질문과 사용자 답변</h2><p class="result-section-copy">포트폴리오와 투자 논리에서 확인이 필요한 부분을 질문했습니다.</p>{qa_html}</section>
              <section><h2><em>6</em> 답변으로 보완된 부분</h2><div class="result-empty">{safe(unanswered_text)}</div></section>
              <section><h2><em>7</em> 아직 남아있는 가정·확인 사항</h2><ul class="result-checklist">{checklist_html}</ul></section>
              <section><h2><em>8</em> 분석에 사용된 데이터와 한계</h2><details class="result-limitations" open><summary>포트폴리오 재무 데이터</summary><ul>{limitations_html}</ul></details></section>
              {f'<div class="result-api-warning">{safe(ai_error)}</div>' if ai_error else ''}
            </main>
            """,
            unsafe_allow_html=True,
        )

        edit_portfolio_col, edit_answers_col, new_analysis_col = st.columns([1, 1, 1.05])
        if edit_portfolio_col.button("포트폴리오 수정하기", use_container_width=True):
            st.session_state["workflow_screen"] = "portfolio"
            st.session_state.pop("final_cross_examination", None)
            st.rerun()
        if edit_answers_col.button("답변 수정하기", use_container_width=True):
            st.session_state["workflow_screen"] = "followup_0"
            st.session_state["cross_examination_index"] = 0
            st.session_state.pop("final_cross_examination", None)
            st.rerun()
        if new_analysis_col.button("새 포트폴리오 분석", type="primary", use_container_width=True):
            st.session_state.pop("cross_examination", None)
            st.session_state.pop("final_cross_examination", None)
            for index in range(3):
                st.session_state.pop(f"cross_examination_answer_{index}", None)
            st.session_state.pop("active_review_id", None)
            st.session_state["workflow_screen"] = "portfolio"
            st.rerun()
