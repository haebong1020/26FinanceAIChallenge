"""Login gate used by the Streamlit prototype."""

import os
from supabase import Client
from data.supabase_repository import create_supabase_client, get_authenticated_user_id

import streamlit as st


def get_secret(name: str) -> str | None:
    """Read configuration without exposing keys."""
    try:
        return os.getenv(name) or st.secrets.get(name)
    except FileNotFoundError:
        return os.getenv(name)


def session_client() -> Client | None:
    """Create one auth client per browser session."""
    if st.session_state.get("supabase_client") is None:
        st.session_state["supabase_client"] = create_supabase_client(
            get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY")
        )
    return st.session_state["supabase_client"]


def clear_session() -> None:
    """Discard all private form inputs and review IDs."""
    for key in list(st.session_state):
        del st.session_state[key]


def render_login(client: Client) -> str | None:
    """Render the team's login design backed by Supabase Auth."""
    user_id = get_authenticated_user_id(client)
    if user_id:
        return user_id
    # Expired authentication must not leave another account's review in memory.
    private_keys = {
        "review_context", "final_result", "review_id", "draft_answers",
        "followup_index", "save_error", "evidence_pdf", "workflow_screen",
    }
    for key in list(st.session_state):
        if key in private_keys or key.startswith(("portfolio_", "criteria_")):
            del st.session_state[key]

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    intro_column, form_column = st.columns([1.08, 0.92], gap="large")

    with intro_column:
        st.markdown(
            """
            <section class="login-intro">
                <span class="login-eyebrow">투자 논리 점검 도구</span>
                <h1>투자 판단의 답보다,<br>근거를 먼저 점검합니다.</h1>
                <p class="login-lead">
                    포트폴리오 추천 없이 내가 세운 투자 논리와<br>
                    판단 근거를 점검해보세요.
                </p>
                <div class="login-feature-list">
                    <div><span>▥</span> 포트폴리오 비중 및 구성 논리 입력</div>
                    <div><span>⌕</span> 5가지 판단 근거 점검 질문</div>
                    <div><span>✦</span> AI 기반 행동편향 및 논리 정합성 분석</div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with form_column:
        st.markdown('<div class="login-form-heading">', unsafe_allow_html=True)
        signup = st.session_state.get("signup", False)
        st.subheader("회원가입" if signup else "로그인")
        st.caption("계정에 로그인하여 계속하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("supabase_login_form"):
            email = st.text_input(
                "이메일",
                placeholder="name@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="••••••••",
                autocomplete="current-password",
            )
            option_column, link_column = st.columns([1.25, 0.75])
            with option_column:
                st.caption("현재 브라우저 세션에서 로그인됩니다.")
            with link_column:
                st.markdown(
                    '<div class="login-help">Supabase 계정 인증</div>',
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button("회원가입" if signup else "로그인", use_container_width=True)

        if submitted:
            if not email.strip() or not password:
                st.error("이메일과 비밀번호를 입력해주세요.")
            elif signup and len(password) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            else:
                try:
                    if signup:
                        client.auth.sign_up({"email": email.strip(), "password": password})
                        client.auth.sign_out()
                    else:
                        client.auth.sign_in_with_password(
                            {"email": email.strip(), "password": password}
                        )
                except Exception:
                    st.error("인증하지 못했습니다. 입력 정보·네트워크·이메일 인증 상태를 확인해주세요.")
                else:
                    if signup:
                        st.success("가입 요청을 처리했습니다. 필요한 경우 인증 이메일을 확인한 뒤 로그인해주세요.")
                    else:
                        st.rerun()
        if st.button("로그인으로 돌아가기" if signup else "회원가입하기"):
            st.session_state["signup"] = not signup
            st.rerun()
    st.caption("분석 결과는 로그인한 사용자 계정에 저장합니다. PDF 본문은 DB에 저장하지 않습니다.")
    return None
