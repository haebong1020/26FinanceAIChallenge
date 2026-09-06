"""Persistence helpers for completed portfolio thesis reviews."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from supabase import Client, create_client


class SupabasePersistenceError(Exception):
    """Raised when a completed review cannot be written to Supabase."""


def create_supabase_client(url: str | None, key: str | None) -> Client | None:
    """Create a client only when the app has both public Supabase settings."""
    if not url or not key:
        return None
    return create_client(url, key)


def get_authenticated_user_id(client: Client) -> str | None:
    """Return the currently signed-in user's id, if this client has a session."""
    try:
        user = client.auth.get_user().user
    except Exception:
        return None
    return str(user.id) if user else None


def save_thesis_review(
    client: Client,
    *,
    user_id: str,
    original_thesis: str,
    holdings: list[dict[str, Any]],
    questionnaire: dict[str, Any],
    cross_examination_answers: list[dict[str, str]],
    ai_analysis: dict[str, Any] | None,
    ai_error: str | None,
    evidence_metadata: dict[str, Any] | None,
    factor_detail: str,
    evidence_url: str,
    workflow_version: str,
) -> str:
    """Create or replace the signed-in user's current review and return its id.

    The uploaded PDF content is intentionally excluded. Only non-sensitive file
    metadata (name and page count) may be passed in ``evidence_metadata``.
    """
    row = {
        "user_id": user_id,
        "original_thesis": original_thesis,
        "holdings": holdings,
        "questionnaire": questionnaire,
        "cross_examination_answers": cross_examination_answers,
        "ai_analysis": ai_analysis,
        "ai_error": ai_error,
        "evidence_metadata": evidence_metadata,
        "factor_detail": factor_detail,
        "evidence_url": evidence_url or None,
        "workflow_version": workflow_version,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    try:
        response = (
            client.table("thesis_reviews")
            .upsert(row, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:  # Supabase client exceptions vary by transport version.
        raise SupabasePersistenceError("Supabase에 분석 결과를 저장하거나 갱신하지 못했습니다.") from exc

    if not response.data or not response.data[0].get("id"):
        raise SupabasePersistenceError("Supabase가 저장된 분석의 ID를 반환하지 않았습니다.")
    return str(response.data[0]["id"])


def update_thesis_review(
    client: Client,
    *,
    review_id: str,
    cross_examination_answers: list[dict[str, str]],
    ai_analysis: dict[str, Any] | None,
    ai_error: str | None,
) -> None:
    """Add final cross-examination output to an already saved review."""
    updates = {
        "cross_examination_answers": cross_examination_answers,
        "ai_analysis": ai_analysis,
        "ai_error": ai_error,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    try:
        response = (
            client.table("thesis_reviews")
            .update(updates)
            .eq("id", review_id)
            .execute()
        )
    except Exception as exc:
        raise SupabasePersistenceError("Supabase에 최종 진단을 저장하지 못했습니다.") from exc

    if not response.data:
        raise SupabasePersistenceError("저장할 분석 결과를 찾지 못했습니다.")
