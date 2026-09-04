"""Streamlit entry point for the Investment Thesis Checker POC."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from data.financial_data import (
    FinancialDataError,
    get_financial_data,
    get_historical_prices,
)
from logic.portfolio import (
    PortfolioValidationError,
    validate_portfolio,
)
from ui.login import render_login, session_client, clear_session
from ui.review_flow import render_review_flow
from ui.styles import apply_global_styles
from ui.workflow import (
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


openai_api_key = get_openai_api_key()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_financial_data(ticker: str) -> dict[str, object]:
    """Cache provider data briefly so reruns do not repeat the same request."""
    return get_financial_data(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_historical_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Cache price history briefly for faster repeated thesis checks."""
    return get_historical_prices(list(tickers))


st.set_page_config(
    page_title="Portfolio Thesis Checker",
    page_icon="⚖️",
    layout="centered",
)
apply_global_styles()

try:
    supabase_client = session_client()
except Exception:
    st.error("Supabase 설정을 확인해주세요.")
    st.stop()
if supabase_client is None:
    st.error("SUPABASE_URL과 SUPABASE_KEY를 환경변수 또는 배포 Secrets에 설정해주세요.")
    st.stop()
authenticated_user_id = render_login(supabase_client)
if not authenticated_user_id:
    st.stop()
if st.button("로그아웃"):
    try:
        supabase_client.auth.sign_out()
    except Exception:
        st.warning("원격 로그아웃을 확인하지 못했습니다.")
    clear_session()
    st.rerun()

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
            lookup_errors = []
            with st.spinner("ticker와 금융 데이터를 확인하는 중입니다..."):
                for holding in validated_holdings:
                    try:
                        get_cached_financial_data(str(holding["ticker"]))
                    except FinancialDataError as exc:
                        lookup_errors.append(str(exc))
            if lookup_errors:
                st.error("ticker 또는 데이터 공급자 응답을 확인해주세요. 잠시 후 다시 시도할 수 있습니다.")
                for error in lookup_errors:
                    st.caption(error)
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
        st.caption("참고 URL은 주소만 기록하며 웹 본문은 수집하지 않습니다.")
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
        value=False,
        disabled=not bool(openai_api_key),
        key="criteria_use_ai",
        help=(
            "선택하면 최초 투자 논리, 금융 데이터 요약, 반대심문 답변이 "
            "최종 단계에서 OpenAI API로 전송됩니다. 매수·매도 추천은 생성하지 않습니다."
        ),
    )
    if not openai_api_key:
        st.caption("AI 키가 없으면 규칙 점검과 답변 기록만 사용할 수 있습니다.")

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
            for state_key in ("review_context", "final_result", "review_id", "draft_answers", "followup_index", "save_error"):
                st.session_state.pop(state_key, None)
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


render_review_flow(
    supabase_client, authenticated_user_id, openai_api_key,
    get_cached_financial_data, get_cached_historical_prices,
)
