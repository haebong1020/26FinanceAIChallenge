"""Regression tests for missing data and non-AI reports."""

from types import SimpleNamespace
from unittest.mock import Mock

from data.financial_data import FinancialDataError
from logic.review import build_review_context, report_sections


def questionnaire() -> dict:
    """Return neutral survey inputs."""
    return {"thesis_factors": [], "investment_horizon": "3년 이상", "evidence_level": "여러 출처"}


def test_missing_data_never_becomes_sample_metrics():
    """Missing sector/history must not be displayed as 100% and 0.76."""
    provider = Mock(side_effect=FinancialDataError("공급자 오류"))
    context = build_review_context(
        [{"ticker": "AAPL", "weight": 50}, {"ticker": "MSFT", "weight": 50}],
        questionnaire(), provider, provider,
    )
    assert context["average_correlation"] is None
    assert context["sector_concentration"]["dominant_weight"] is None
    assert not context["team_standard_findings"]
    assert len(context["questions"]) == 3
    report = report_sections(context)
    assert report["supported"] == report["biases"] == []


def test_single_stock_does_not_request_correlation():
    """One-stock reviews continue without correlation."""
    history = Mock()
    provider = Mock(return_value={"company_profile": {"sector": "Energy"}})
    context = build_review_context(
        [{"ticker": "XOM", "weight": 100}], questionnaire(), provider, history,
    )
    history.assert_not_called()
    assert context["average_correlation"] is None
    assert all("기술 섹터" not in question for question in context["questions"])


def test_team_threshold_and_unknown_sector():
    """Unknown classification must not trigger a sector concentration finding."""
    def provider(ticker: str) -> dict:
        """Return a known sector for one holding only."""
        return {"company_profile": {"sector": "Energy" if ticker == "XOM" else None}}
    history = Mock(side_effect=FinancialDataError("가격 누락"))
    for weight, expected in [(69, False), (70, True)]:
        context = build_review_context(
            [{"ticker": "XOM", "weight": weight}, {"ticker": "ABC", "weight": 100-weight}],
            questionnaire(), provider, history,
        )
        assert bool(context["team_standard_findings"]) is expected


def test_empty_ai_lists_are_supported():
    """An empty supported-points list must not cause IndexError."""
    ai = SimpleNamespace(supported_points=[], uncertain_points=[], possible_biases=[],
                         data_limitations=[])
    result = report_sections({"warnings": [], "team_standard_findings": []}, ai)
    assert result["supported"] == []
