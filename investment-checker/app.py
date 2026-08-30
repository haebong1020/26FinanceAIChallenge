"""Streamlit entry point for the Investment Thesis Checker POC."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai.portfolio_analyzer import AIAnalysisError, analyze_portfolio_thesis
from data.financial_data import (
    FinancialDataError,
    get_financial_data,
    get_historical_prices,
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
    generate_portfolio_questions,
    validate_portfolio,
)
from logic.cross_examination import (
    CrossExaminationError,
    select_cross_examination_questions,
    validate_cross_examination_answers,
)
from logic.thesis_standards import evaluate_thesis_standards


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
    return {
        "filename": evidence["filename"],
        "page_count": evidence["page_count"],
    }


def show_auth_page() -> None:
    """Show the minimal login/sign-up flow until a Supabase Auth session exists."""
    st.title("Portfolio Thesis Checker")
    st.caption("분석을 시작하려면 로그인해주세요.")

    auth_view = st.session_state.get("auth_view", "login")
    if auth_view == "signup":
        st.subheader("회원가입")
        with st.form("sign_up_form"):
            signup_email = st.text_input("아이디(이메일)")
            signup_password = st.text_input("비밀번호", type="password")
            signup_password_confirm = st.text_input("비밀번호 확인", type="password")
            sign_up_submitted = st.form_submit_button("회원가입")

        if sign_up_submitted:
            if not all([signup_email.strip(), signup_password, signup_password_confirm]):
                st.error("아이디와 비밀번호를 모두 입력해주세요.")
            elif signup_password != signup_password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(signup_password) < 6:
                st.error("비밀번호는 6자 이상 입력해주세요.")
            else:
                try:
                    supabase_client.auth.sign_up(
                        {"email": signup_email.strip(), "password": signup_password}
                    )
                except Exception as exc:
                    st.error(f"회원가입에 실패했습니다: {exc}")
                else:
                    # Keep sign-up and sign-in as separate steps in this MVP.
                    supabase_client.auth.sign_out()
                    st.session_state["auth_view"] = "login"
                    st.rerun()

        if st.button("로그인으로 돌아가기"):
            st.session_state["auth_view"] = "login"
            st.rerun()
        return

    st.subheader("로그인")
    with st.form("sign_in_form"):
        login_email = st.text_input("아이디(이메일)")
        login_password = st.text_input("비밀번호", type="password")
        sign_in_submitted = st.form_submit_button("로그인")

    if sign_in_submitted:
        if not login_email.strip() or not login_password:
            st.error("아이디와 비밀번호를 모두 입력해주세요.")
        else:
            try:
                supabase_client.auth.sign_in_with_password(
                    {"email": login_email.strip(), "password": login_password}
                )
            except Exception:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.rerun()

    st.caption("계정이 없나요?")
    if st.button("회원가입"):
        st.session_state["auth_view"] = "signup"
        st.rerun()


openai_api_key = get_openai_api_key()
supabase_client = get_session_supabase_client()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_financial_data(ticker: str) -> dict[str, object]:
    """Cache provider data briefly so reruns do not repeat the same request."""
    return get_financial_data(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_historical_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Cache price history briefly for faster repeated thesis checks."""
    return get_historical_prices(list(tickers))


st.set_page_config(page_title="Portfolio Thesis Checker")

if supabase_client is None:
    st.error("Supabase 연결 설정을 확인해주세요. .env에 URL과 Publishable key가 필요합니다.")
    st.stop()

authenticated_user_id = get_authenticated_user_id(supabase_client)
if not authenticated_user_id:
    show_auth_page()
    st.stop()

st.title("Portfolio Thesis Checker")
st.caption("포트폴리오를 추천하지 않고, 입력한 구성과 투자 논리를 점검합니다.")
account_col, sign_out_col = st.columns([6, 1])
account_col.caption("로그인됨")
if sign_out_col.button("로그아웃"):
    supabase_client.auth.sign_out()
    st.session_state["auth_view"] = "login"
    st.rerun()

with st.form("thesis_form"):
    st.subheader("포트폴리오 입력")
    portfolio_input = st.data_editor(
        pd.DataFrame(
            [
                {"ticker": "AAPL", "weight": 40.0},
                {"ticker": "MSFT", "weight": 30.0},
                {"ticker": "NVDA", "weight": 30.0},
            ]
        ),
        column_config={
            "ticker": st.column_config.TextColumn(
                "Ticker", help="미국 상장주식 ticker를 입력하세요."
            ),
            "weight": st.column_config.NumberColumn(
                "비중 (%)", min_value=0.01, max_value=100.0, format="%.2f"
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
    )
    st.caption("최대 10개 종목까지 입력할 수 있으며 비중 합계는 100%여야 합니다.")

    thesis = st.text_area(
        "포트폴리오 구성 논리",
        placeholder="예: AI 성장주를 여러 기업에 나누어 투자해 위험을 분산했다고 생각한다.",
        help="이 종목들과 비중을 선택한 이유를 자유롭게 적어주세요.",
    )

    evidence_pdf = st.file_uploader(
        "판단에 참고한 PDF (선택)",
        type=["pdf"],
        accept_multiple_files=False,
        help=(
            "10MB 이하의 PDF 1개를 첨부할 수 있습니다. "
            "파일은 DB에 저장하지 않으며, AI 분석을 선택한 경우에만 "
            "추출된 텍스트가 OpenAI API로 전송됩니다."
        ),
    )
    if evidence_pdf is not None:
        st.caption(f"첨부된 자료: {evidence_pdf.name}")

    st.subheader("판단 근거 점검")
    thesis_factors = st.multiselect(
        "1. 이 판단에서 중요하게 본 근거는 무엇인가요? (복수 선택 가능)",
        THESIS_FACTORS,
    )
    decision_trigger = st.radio(
        "2. 이 포트폴리오를 구성하게 된 가장 큰 계기는 무엇인가요?",
        DECISION_TRIGGERS,
        index=None,
    )
    evidence_level = st.radio(
        "3. 판단하기 전에 어느 정도까지 자료를 확인했나요?",
        EVIDENCE_LEVELS,
        index=None,
    )
    investment_horizon = st.radio(
        "4. 예상하는 투자 기간은 어느 정도인가요?",
        INVESTMENT_HORIZONS,
        index=None,
        horizontal=True,
    )
    loss_response = st.radio(
        "5. 포트폴리오 가치가 30% 하락한다면 어떻게 대응할 가능성이 가장 높은가요?",
        LOSS_RESPONSES,
        index=None,
    )

    use_ai_analysis = st.checkbox(
        "반대심문 답변 후 AI로 최종 논리 일관성을 분석합니다.",
        value=False,
        disabled=not bool(openai_api_key),
        help=(
            "선택하면 최초 투자 논리, 금융 데이터 요약, 반대심문 답변이 "
            "최종 단계에서 OpenAI API로 전송됩니다. 매수·매도 추천은 생성하지 않습니다."
        ),
    )
    if not openai_api_key:
        st.caption("AI 분석을 사용하려면 OPENAI_API_KEY를 설정해주세요.")

    submitted = st.form_submit_button("Check my thesis")

pdf_evidence = None
pdf_error = None
submitted_review_id = None
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
                        },
                        cross_examination_answers=[],
                        ai_analysis=None,
                        ai_error=None,
                        evidence_metadata=get_evidence_metadata(pdf_evidence),
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
                st.error(data_error)
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

                        questions = generate_portfolio_questions(
                            holdings,
                            comparison_weights,
                            str(sector_concentration["dominant_sector"]),
                            float(sector_concentration["dominant_weight"]),
                            average_correlation,
                        )
                        cross_examination_questions = (
                            select_cross_examination_questions(
                                standard_findings, questions
                            )
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


cross_examination = st.session_state.get("cross_examination")
if cross_examination:
    st.divider()
    st.header("2단계: 반대심문 답변")
    st.write(
        "1차 분석에서 발견된 쟁점에 답해주세요. 답변은 새로운 추천을 받기 위한 "
        "것이 아니라, 최초 논리를 보완하거나 수정할 수 있는지 확인하는 데 사용됩니다."
    )

    with st.form("cross_examination_form"):
        follow_up_answers = [
            st.text_area(
                f"질문 {index + 1}. {question}",
                key=f"cross_examination_answer_{index}",
            )
            for index, question in enumerate(cross_examination["questions"])
        ]
        final_submitted = st.form_submit_button("최종 진단 보기")

    if final_submitted:
        try:
            answer_records = validate_cross_examination_answers(
                cross_examination["questions"], follow_up_answers
            )
        except CrossExaminationError as exc:
            st.error(str(exc))
        else:
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
                    with st.spinner("AI가 최초 논리와 추가 답변을 함께 검증하는 중입니다..."):
                        final_result["ai_analysis"] = analyze_portfolio_thesis(
                            combined_thesis,
                            final_context,
                            api_key=openai_api_key,
                        )
                except AIAnalysisError as exc:
                    final_result["ai_error"] = str(exc)
            st.session_state["final_cross_examination"] = final_result

            review_id = cross_examination.get("review_id")
            if review_id:
                try:
                    update_thesis_review(
                        supabase_client,
                        review_id=str(review_id),
                        cross_examination_answers=answer_records,
                        ai_analysis=(
                            final_result["ai_analysis"].model_dump(mode="json")
                            if final_result.get("ai_analysis")
                            else None
                        ),
                        ai_error=(
                            str(final_result["ai_error"])
                            if final_result.get("ai_error")
                            else None
                        ),
                    )
                except SupabasePersistenceError as exc:
                    st.warning(str(exc))

    final_cross_examination = st.session_state.get("final_cross_examination")
    if final_cross_examination:
        st.header("최종 진단")
        st.success("반대심문 답변이 모두 제출되었습니다.")

        st.markdown("#### 질문별 보완 답변")
        for record in final_cross_examination["answers"]:
            with st.expander(str(record["question"]), expanded=True):
                st.write(str(record["answer"]))

        ai_error = final_cross_examination.get("ai_error")
        ai_analysis = final_cross_examination.get("ai_analysis")
        if ai_error:
            st.warning(str(ai_error))
        elif ai_analysis:
            st.markdown("#### 최초 논리와 추가 답변의 종합 분석")
            st.write(ai_analysis.summary)
            st.write("분류: " + ", ".join(ai_analysis.categories))

            st.markdown("#### 데이터와 부합하거나 보완된 부분")
            for point in ai_analysis.supported_points:
                st.write(f"- {point}")

            st.markdown("#### 여전히 확인이 필요한 부분")
            for point in ai_analysis.uncertain_points:
                st.write(f"- {point}")

            st.markdown("#### 편향 또는 논리 이동 가능성")
            if ai_analysis.possible_biases:
                for bias in ai_analysis.possible_biases:
                    st.write(f"- {bias}")
            else:
                st.write("- 현재 답변에서 뚜렷한 편향을 확인하기 어렵습니다.")

            st.markdown("#### 남은 확인 질문")
            for question in ai_analysis.devils_advocate_questions:
                st.write(f"- {question}")

            with st.expander("최종 분석의 데이터 한계"):
                for limitation in ai_analysis.data_limitations:
                    st.write(f"- {limitation}")
        else:
            st.info(
                "현재는 답변 제출과 기록까지 완료되었습니다. 답변의 의미, 최초 "
                "논리와의 일관성, 논리 이동 여부를 자동 해석하려면 AI 분석을 "
                "활성화해야 합니다."
            )

    if st.button("새 분석 시작"):
        st.session_state.pop("cross_examination", None)
        st.session_state.pop("final_cross_examination", None)
        st.session_state.pop("active_review_id", None)
        for index in range(3):
            st.session_state.pop(f"cross_examination_answer_{index}", None)
        st.rerun()
