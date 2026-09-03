"""Login gate used by the Streamlit prototype."""

import streamlit as st

from data.supabase_repository import get_authenticated_user_id


def render_login(supabase_client) -> bool:
    """Render the designed login view backed by the current Supabase session."""
    if get_authenticated_user_id(supabase_client):
        return True

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
        auth_view = st.session_state.get("auth_view", "login")
        is_signup = auth_view == "signup"
        st.subheader("회원가입" if is_signup else "로그인")
        st.caption(
            "계정을 만들어 분석 결과를 안전하게 저장하세요."
            if is_signup
            else "계정에 로그인하여 계속하세요."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("sign_up_form" if is_signup else "sign_in_form"):
            email = st.text_input(
                "이메일",
                placeholder="name@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="••••••••",
                autocomplete="new-password" if is_signup else "current-password",
            )
            password_confirm = ""
            if is_signup:
                password_confirm = st.text_input(
                    "비밀번호 확인",
                    type="password",
                    placeholder="••••••••",
                    autocomplete="new-password",
                )
            submitted = st.form_submit_button(
                "회원가입" if is_signup else "로그인", use_container_width=True
            )

        if submitted:
            if not email.strip() or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
            elif is_signup and password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif is_signup and len(password) < 6:
                st.error("비밀번호는 6자 이상 입력해주세요.")
            elif is_signup:
                try:
                    supabase_client.auth.sign_up(
                        {"email": email.strip(), "password": password}
                    )
                except Exception as exc:
                    st.error(f"회원가입에 실패했습니다: {exc}")
                else:
                    st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                    st.session_state["auth_view"] = "login"
            elif not password:
                st.error("비밀번호를 입력해주세요.")
            else:
                try:
                    supabase_client.auth.sign_in_with_password(
                        {"email": email.strip(), "password": password}
                    )
                except Exception:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
                else:
                    st.rerun()

        st.markdown(
            '<p class="login-signup">'
            + ("이미 계정이 있으신가요?" if is_signup else "아직 계정이 없으신가요?")
            + "</p>",
            unsafe_allow_html=True,
        )
        if st.button(
            "로그인으로 돌아가기" if is_signup else "회원가입",
            use_container_width=True,
            key="auth_view_switch",
        ):
            st.session_state["auth_view"] = "login" if is_signup else "signup"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    return False
