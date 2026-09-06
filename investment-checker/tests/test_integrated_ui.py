"""Exercise integrated screens without calling real financial or auth APIs."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from data.financial_data import FinancialDataError
from logic.review import build_review_context
from data.supabase_repository import SupabasePersistenceError
from ui.review_flow import save_result


APP = Path(__file__).resolve().parents[1] / "app.py"


def context() -> dict:
    """Build a realistic missing-data review."""
    missing = Mock(side_effect=FinancialDataError("테스트: 데이터 누락"))
    return build_review_context(
        [{"ticker": "AAPL", "weight": 100}],
        {"thesis_factors": [], "investment_horizon": "3년 이상",
         "evidence_level": "미확인", "use_ai_analysis": False},
        missing, missing,
    )


def authenticated_client() -> Mock:
    """Provide a fake verified auth user."""
    client = Mock()
    client.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id="user-a"))
    return client


def test_followup_skip_finalize_and_save_without_ai():
    """Skipped answers must not produce fabricated claims or prevent saving."""
    review = context()
    app = AppTest.from_file(str(APP), default_timeout=20)
    app.session_state["workflow_screen"] = "followup"
    app.session_state["review_context"] = review
    app.session_state["portfolio_thesis"] = "장기 투자 근거 테스트"
    app.session_state["criteria_values"] = review["questionnaire"]
    with patch("ui.login.session_client", return_value=authenticated_client()), \
         patch("ui.review_flow.save_thesis_review", return_value="review-a") as save:
        app.run()
        for _ in range(3):
            next(button for button in app.button if button.label == "건너뛰기").click().run()
        assert not app.exception
        assert app.session_state["workflow_screen"] == "result"
        save.assert_called_once()
        payload = save.call_args.kwargs
        assert payload["user_id"] == "user-a"
        assert payload["ai_analysis"] is None
        assert payload["evidence_metadata"] is None
        assert all(row["answer"] == "답변하지 않음" for row in payload["cross_examination_answers"])
        texts = " ".join(item.value for item in app.markdown)
        assert "세 종목 모두" not in texts
        assert "일관성 양호" not in texts
        next(button for button in app.button if button.label == "새 포트폴리오 분석").click().run()
        assert not app.exception
        assert "review_id" not in app.session_state
        assert "final_result" not in app.session_state


def test_logout_clears_previous_user_data():
    """A new user must not inherit the previous user's report or row ID."""
    app = AppTest.from_file(str(APP), default_timeout=20)
    app.session_state["workflow_screen"] = "portfolio"
    app.session_state["review_id"] = "old-private-id"
    app.session_state["portfolio_thesis"] = "private thesis"
    client = authenticated_client()
    with patch("ui.login.session_client", return_value=client):
        app.run()
        next(button for button in app.button if button.label == "로그아웃").click().run()
        client.auth.sign_out.assert_called_once()
        assert "review_id" not in app.session_state
        assert "portfolio_thesis" not in app.session_state


def test_save_retry_and_answer_edit_update_same_row():
    """A known review ID is updated, and storage failures remain visible."""
    review = context()
    review["uploaded_evidence"] = {
        "filename": "report.pdf", "page_count": 2, "text": "private PDF text",
    }
    state = {
        "review_context": review, "portfolio_thesis": "initial thesis",
        "final_result": {"answers": [], "analysis": None},
    }
    with patch("ui.review_flow.st", SimpleNamespace(session_state=state)), \
         patch("ui.review_flow.save_thesis_review",
               side_effect=[SupabasePersistenceError("실패"), "id-a"]) as insert, \
         patch("ui.review_flow.update_thesis_review") as update:
        save_result(Mock(), "user-a")
        assert state["save_error"] == "실패"
        assert "review_id" not in state
        save_result(Mock(), "user-a")
        assert state["review_id"] == "id-a"
        assert "save_error" not in state
        assert insert.call_args.kwargs["evidence_metadata"] == {
            "filename": "report.pdf", "page_count": 2,
        }
        state["final_result"]["answers"] = [{"question": "Q", "answer": "edited"}]
        save_result(Mock(), "user-a")
        assert insert.call_count == 2
        update.assert_called_once()
        assert update.call_args.kwargs["review_id"] == "id-a"


def test_auth_failure_blocks_portfolio_screen():
    """Unverified login may not reach analysis screens."""
    app = AppTest.from_file(str(APP), default_timeout=20)
    client = Mock()
    client.auth.get_user.side_effect = RuntimeError("expired")
    app.session_state["workflow_screen"] = "result"
    app.session_state["review_id"] = "private-old-id"
    with patch("ui.login.session_client", return_value=client):
        app.run()
        assert not app.exception
        assert "review_id" not in app.session_state
        assert not any(button.label == "새 포트폴리오 분석" for button in app.button)
