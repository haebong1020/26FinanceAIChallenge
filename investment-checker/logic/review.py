"""Build a review from real provider data; never substitute sample metrics."""

from collections.abc import Callable
from typing import Any

from data.financial_data import FinancialDataError
from logic.cross_examination import select_cross_examination_questions
from logic.portfolio import (
    PortfolioValidationError, validate_portfolio, calculate_concentration,
    calculate_sector_concentration, calculate_return_correlation,
    calculate_average_correlation, build_comparison_weights,
    calculate_historical_portfolio_metrics,
)
from logic.thesis_standards import evaluate_thesis_standards


def build_review_context(
    rows: list[dict[str, Any]],
    questionnaire: dict[str, Any],
    financial_provider: Callable,
    history_provider: Callable,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect available evidence and preserve unavailable metrics as missing."""
    holdings = validate_portfolio(rows)
    financial_data, sectors, warnings = [], {}, []
    for holding in holdings:
        ticker = str(holding["ticker"])
        try:
            data = financial_provider(ticker)
        except FinancialDataError as exc:
            warnings.append(str(exc))
            sectors[ticker] = None
        else:
            financial_data.append(data)
            sectors[ticker] = data["company_profile"]["sector"]
    sector = calculate_sector_concentration(holdings, sectors)
    known = {key: value for key, value in sector["sector_weights"].items()
             if key != "Unknown"}
    dominant_sector = max(known, key=known.get) if known else "확인 불가"
    dominant_weight = known.get(dominant_sector)
    sector["dominant_sector"] = dominant_sector
    sector["dominant_weight"] = dominant_weight
    if any(not value for value in sectors.values()):
        warnings.append("일부 산업 정보가 누락되었습니다. 확인된 산업 비중만 표시합니다.")
    average = None
    correlation, weights, metrics = {}, {}, {}
    if len(holdings) >= 2:
        try:
            prices = history_provider(tuple(str(row["ticker"]) for row in holdings))
            matrix = calculate_return_correlation(prices)
            average = calculate_average_correlation(matrix)
            correlation = matrix.to_dict()
            comparison = build_comparison_weights(holdings, prices)
            weights = (comparison * 100).to_dict()
            metrics = calculate_historical_portfolio_metrics(prices, comparison).to_dict()
        except (FinancialDataError, PortfolioValidationError) as exc:
            warnings.append(str(exc))
    else:
        warnings.append("단일 종목은 종목 간 상관관계를 계산하지 않습니다.")
    findings = evaluate_thesis_standards(
        holding_count=len(holdings),
        dominant_sector_weight=dominant_weight or 0.0,
        average_correlation=average,
        thesis_factors=questionnaire["thesis_factors"],
        investment_horizon=questionnaire["investment_horizon"],
        evidence_level=questionnaire["evidence_level"],
    )
    largest = calculate_concentration(holdings)
    neutral_questions = [
        f'{largest["largest_ticker"]}의 비중 {largest["largest_weight"]:.1f}%를 정한 근거와 재검토 조건은 무엇인가요?',
        "최초 투자 논리가 틀렸음을 보여줄 수 있는 반대 근거는 무엇인가요?",
        "투자 기간 안에 어떤 데이터를 확인하고 판단을 다시 검토할 예정인가요?",
    ]
    return {
        "holdings": holdings, "financial_data": financial_data, "concentration": largest,
        "sector_concentration": sector, "average_correlation": average,
        "correlation": correlation, "comparison_weights_percent": weights,
        "historical_metrics": metrics, "questionnaire": questionnaire,
        "uploaded_evidence": evidence, "team_standard_findings": findings,
        "questions": select_cross_examination_questions(findings, neutral_questions),
        "warnings": warnings,
    }


def report_sections(context: dict[str, Any], analysis: Any = None) -> dict[str, list[str]]:
    """Use AI output only when available; rules do not establish thesis truth."""
    return {
        "supported": list(analysis.supported_points) if analysis else [],
        "uncertain": list(analysis.uncertain_points) if analysis else [
            str(finding["diagnosis"]) for finding in context["team_standard_findings"]
        ],
        "biases": list(analysis.possible_biases) if analysis else [],
        "limitations": list(context["warnings"]) + (
            list(analysis.data_limitations) if analysis else
            ["AI 의미 분석을 실행하지 않았거나 완료하지 못했습니다.",
             "규칙 점검은 투자 논리의 진실 여부나 편향을 확정하지 않습니다."]
        ) + ["과거 데이터는 미래 성과를 보장하지 않습니다.",
             "PDF는 최대 30페이지·30,000자까지만 분석합니다.",
             "참고 URL은 주소만 기록하며 웹 본문은 수집하지 않습니다."],
    }
