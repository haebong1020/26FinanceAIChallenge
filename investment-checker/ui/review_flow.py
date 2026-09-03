"""Connect the team's screens to financial evidence, AI, and per-user storage."""

import html
from collections.abc import Callable
from typing import Any

import pandas as pd
import streamlit as st
from supabase import Client

from ai.portfolio_analyzer import AIAnalysisError, analyze_portfolio_thesis
from data.pdf_evidence import PDFEvidenceError, extract_pdf_evidence
from data.supabase_repository import (
    SupabasePersistenceError, save_thesis_review, update_thesis_review,
)
from logic.review import build_review_context, report_sections
from ui.workflow import render_step_navigation


def reset_review() -> None:
    """Remove inputs and derived results without signing out the user."""
    for key in list(st.session_state):
        if key not in {"supabase_client", "signup"}:
            del st.session_state[key]
    st.session_state["workflow_screen"] = "portfolio"


def save_result(client: Client, user_id: str) -> None:
    """Save once per review and update the same record after answer edits."""
    state = st.session_state
    context, result = state["review_context"], state["final_result"]
    analysis = result.get("analysis")
    common = {
        "cross_examination_answers": result["answers"],
        "ai_analysis": analysis.model_dump(mode="json") if analysis else None,
        "ai_error": result.get("error"),
    }
    try:
        if state.get("review_id"):
            update_thesis_review(client, review_id=state["review_id"], **common)
        else:
            evidence = context.get("uploaded_evidence")
            state["review_id"] = save_thesis_review(
                client, user_id=user_id,
                original_thesis=state["portfolio_thesis"],
                holdings=context["holdings"], questionnaire=context["questionnaire"],
                evidence_metadata=(
                    {"filename": evidence["filename"], "page_count": evidence["page_count"]}
                    if evidence else None
                ),
                **common,
            )
    except SupabasePersistenceError as exc:
        state["save_error"] = str(exc)
    else:
        state.pop("save_error", None)


def section(number: int, title: str, items: list[str], empty: str) -> None:
    """Render escaped report text in the designer's report cards."""
    rows = "".join(
        '<div class="result-evidence"><div>' + html.escape(item) + '</div></div>'
        for item in items
    ) or '<div class="result-empty">' + html.escape(empty) + '</div>'
    st.markdown(
        f'<div class="final-report"><section><h2><em>{number}</em>'
        f'{html.escape(title)}</h2>{rows}</section></div>',
        unsafe_allow_html=True,
    )


def render_report() -> None:
    """Show only computed findings and actual AI output, never mock ratings."""
    state = st.session_state
    context, result = state["review_context"], state["final_result"]
    analysis = result.get("analysis")
    report = report_sections(context, analysis)
    st.markdown(
        '<div class="final-report"><h1>투자 논리 진단 결과</h1></div>',
        unsafe_allow_html=True,
    )
    if result.get("error"):
        st.warning(result["error"])
    if not analysis:
        st.info("규칙 점검·답변 기록 결과입니다. AI 의미 분석은 완료되지 않았습니다.")
    if state.get("save_error"):
        st.warning(state["save_error"])
    elif state.get("review_id"):
        st.caption("현재 계정에 저장되었습니다.")
    section(1, "투자 논리 점검 요약",
            [state["portfolio_thesis"]] + ([analysis.summary] if analysis else []),
            "입력 없음")
    with st.expander("포트폴리오 및 실제 계산값", expanded=True):
        st.dataframe(pd.DataFrame(context["holdings"]), hide_index=True)
        concentration = context["concentration"]
        st.write(f'최대 비중 종목: {concentration["largest_ticker"]} '
                 f'({concentration["largest_weight"]:.1f}%)')
        st.write(f'상위 2개 종목 비중: {concentration["top_two_weight"]:.1f}%')
        sector = context["sector_concentration"]
        weight = sector["dominant_weight"]
        st.write("최대 확인 산업: " + str(sector["dominant_sector"]))
        st.write("산업 비중: " + (f"{weight:.1f}%" if weight is not None else "확인 불가"))
        average = context["average_correlation"]
        st.write("평균 상관계수: " + (f"{average:.2f}" if average is not None else "계산 불가"))
        if context["correlation"]:
            st.dataframe(pd.DataFrame(context["correlation"]).round(2))
        if context["comparison_weights_percent"]:
            st.caption("비교용 비중이며 추천·목표 비중이 아닙니다.")
            st.dataframe(pd.DataFrame(context["comparison_weights_percent"]).round(2))
            st.caption("아래 성과는 최근 1년 과거 가격 기준 소수 비율입니다. 비용·세금·환율은 미반영입니다.")
            st.dataframe(pd.DataFrame(context["historical_metrics"]).round(4))
    section(2, "데이터와 부합하는 근거", report["supported"],
            "현재 확인된 부합 근거가 없습니다. 데이터 조회만으로 투자 주장이 입증되는 것은 아닙니다.")
    section(3, "데이터와 충돌하거나 확인되지 않은 근거", report["uncertain"],
            "추가 지적 사항이 없다고 해서 투자 논리가 검증된 것은 아닙니다.")
    section(4, "편향 가능성", report["biases"],
            "편향을 확인하지 못했거나 AI 분석을 실행하지 않았습니다.")
    section(5, "반대심문 질문과 사용자 답변",
            [f'Q: {item["question"]}\nA: {item["answer"]}' for item in result["answers"]],
            "답변 없음")
    answered = sum(item["answer"] != "답변하지 않음" for item in result["answers"])
    section(6, "답변으로 보완된 부분",
            [f"총 {len(result['answers'])}개 중 {answered}개 답변 제출.",
             "답변 제출 수는 논리 보완 정도를 뜻하지 않습니다. 보완 여부는 위 종합 분석을 참고해주세요."
             if analysis else "답변의 의미와 논리 보완 여부는 AI 분석 전에는 확인할 수 없습니다."],
            "평가 미실행")
    section(7, "아직 남아 있는 가정·확인 사항",
            (list(analysis.devils_advocate_questions) if analysis else []) +
            [item["question"] for item in result["answers"] if item["answer"] == "답변하지 않음"],
            "추가 확인 사항을 자동 확정할 수 없습니다.")
    section(8, "분석에 사용된 데이터와 한계", report["limitations"], "정보 없음")
    with st.expander("사용한 금융 데이터 · 팀 기준 · PDF 추출 범위"):
        st.json(context["financial_data"])
        st.json(context["team_standard_findings"])
        evidence = context.get("uploaded_evidence")
        if evidence:
            st.write(f'PDF: {evidence["filename"]} / {evidence["page_count"]}페이지')
            if evidence["was_truncated"]:
                st.warning("PDF 일부만 분석에 사용했습니다.")
            for page in evidence["pages"][:3]:
                st.caption(f'{page["page"]}페이지 (최대 2,000자 미리보기)')
                st.text(str(page["text"])[:2000])
    left, middle, right = st.columns(3)
    if left.button("포트폴리오 수정하기"):
        for key in ("review_context", "final_result", "review_id", "draft_answers", "save_error"):
            state.pop(key, None)
        state["workflow_screen"] = "portfolio"
        st.rerun()
    if middle.button("답변 수정하기"):
        state.pop("final_result", None)
        state["followup_index"] = 0
        state["workflow_screen"] = "followup"
        st.rerun()
    if right.button("새 포트폴리오 분석", type="primary"):
        reset_review()
        st.rerun()


def render_review_flow(
    client: Client, user_id: str, api_key: str | None,
    financial_provider: Callable, history_provider: Callable,
) -> None:
    """Run data collection, one-question screens, final analysis, and persistence."""
    state = st.session_state
    if state["workflow_screen"] == "loading":
        render_step_navigation("followup")
        evidence = None
        if state.get("evidence_pdf") is not None:
            pdf = state["evidence_pdf"]
            try:
                evidence = extract_pdf_evidence(pdf.getvalue(), pdf.name)
            except PDFEvidenceError as exc:
                st.error(str(exc))
                if st.button("자료 수정하기"):
                    state["workflow_screen"] = "criteria"
                    st.rerun()
                return
        with st.status("금융 데이터 대조 및 추가 질문 생성", expanded=True) as status:
            st.write("종목별 재무 정보, 산업 집중도, 과거 수익률을 확인합니다.")
            state["review_context"] = build_review_context(
                state["portfolio_input"].to_dict("records"), state["criteria_values"],
                financial_provider, history_provider, evidence,
            )
            status.update(label="규칙 점검 완료", state="complete")
        state["followup_index"] = 0
        state["workflow_screen"] = "followup"
        st.rerun()
    if state["workflow_screen"] == "followup":
        render_step_navigation("followup")
        context = state["review_context"]
        index = state.get("followup_index", 0)
        questions = context["questions"]
        with st.expander("1차 점검 근거와 데이터 한계"):
            for finding in context["team_standard_findings"]:
                st.write(finding["diagnosis"])
                st.caption(" / ".join(finding["evidence"]))
            for warning in context["warnings"]:
                st.warning(warning)
            st.caption("팀 집중도 기준: 동일 산업 70% 이상 또는 평균 상관계수 0.70 이상.")
        st.progress((index + 1) / len(questions), text=f"질문 {index + 1} / {len(questions)}")
        st.markdown(
            '<section class="followup-hero"><h1>추가 점검 질문</h1></section>'
            '<div class="followup-question-card">' + html.escape(questions[index]) + '</div>',
            unsafe_allow_html=True,
        )
        drafts = state.setdefault("draft_answers", {})
        with st.form(f"answer_form_{index}"):
            answer = st.text_area("답변 (선택)", value=drafts.get(str(index), ""))
            skip = st.form_submit_button("건너뛰기")
            next_step = st.form_submit_button(
                "최종 진단 보기" if index == len(questions) - 1 else "다음 질문", type="primary"
            )
        if skip or next_step:
            drafts[str(index)] = "" if skip else answer.strip()
            if index + 1 < len(questions):
                state["followup_index"] = index + 1
            else:
                state["workflow_screen"] = "finalize"
            st.rerun()
    elif state["workflow_screen"] == "finalize":
        render_step_navigation("result")
        context = state["review_context"]
        answers = [
            {"question": question, "answer": state["draft_answers"].get(str(index)) or "답변하지 않음"}
            for index, question in enumerate(context["questions"])
        ]
        result: dict[str, Any] = {"answers": answers}
        if state["criteria_values"]["use_ai_analysis"] and api_key:
            with st.spinner("최초 논리와 추가 답변을 함께 분석하고 있습니다..."):
                try:
                    result["analysis"] = analyze_portfolio_thesis(
                        state["portfolio_thesis"],
                        {**context, "cross_examination_answers": answers},
                        api_key=api_key,
                    )
                except AIAnalysisError as exc:
                    result["error"] = str(exc)
        state["final_result"] = result
        save_result(client, user_id)
        state["workflow_screen"] = "result"
        st.rerun()
    elif state["workflow_screen"] == "result":
        render_step_navigation("result")
        if state.get("save_error") and st.button("저장 다시 시도"):
            save_result(client, user_id)
            st.rerun()
        render_report()
