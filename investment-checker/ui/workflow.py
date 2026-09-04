"""Workflow navigation and transition screens."""

import streamlit as st
import streamlit.components.v1 as components


STEPS = [
    ("portfolio", "포트폴리오 입력"),
    ("criteria", "투자 기준"),
    ("followup", "추가 질문"),
    ("result", "진단 결과"),
]


def scroll_to_top_on_screen_change(screen: str) -> None:
    """Reset the main viewport only when the workflow advances to another screen."""
    previous_screen = st.session_state.get("_last_workflow_screen")
    if previous_screen == screen:
        return
    st.session_state["_last_workflow_screen"] = screen
    components.html(
        """
        <script>
        const workflowScreen = "%WORKFLOW_SCREEN%";
        const scrollMainToTop = () => {
            const doc = window.parent.document;
            const selectors = [
                '[data-testid="stMain"]',
                '[data-testid="stAppViewContainer"]',
                'section.main',
                '.stApp'
            ];
            selectors.forEach((selector) => {
                const element = doc.querySelector(selector);
                if (element) {
                    element.scrollTop = 0;
                    element.scrollLeft = 0;
                    element.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                }
            });
            doc.documentElement.scrollTop = 0;
            doc.body.scrollTop = 0;
            window.parent.scrollTo(0, 0);

            const top = doc.querySelector('[data-testid="stMainBlockContainer"]');
            if (top) top.scrollIntoView({ block: 'start', behavior: 'auto' });
        };
        scrollMainToTop();
        const scrollReset = window.setInterval(scrollMainToTop, 40);
        window.setTimeout(() => {
            scrollMainToTop();
            window.clearInterval(scrollReset);
        }, 280);

        const shield = window.parent.document.getElementById('workflow-transition-shield');
        if (shield && %REMOVE_SHIELD%) {
            window.setTimeout(() => {
                shield.remove();
                const main = window.parent.document.querySelector('[data-testid="stMain"]');
                if (main) {
                    main.style.removeProperty('overflow-y');
                    main.style.removeProperty('scrollbar-gutter');
                }
            }, 300);
        }
        </script>
        """
        .replace("%WORKFLOW_SCREEN%", screen)
        .replace(
            "%REMOVE_SHIELD%",
            "true"
            if screen
            not in {"loading", "analysis", "result_loading", "finalize_result"}
            else "false",
        ),
        height=0,
        width=0,
    )


def render_step_navigation(active_step: str) -> None:
    """Render the compact four-step navigation used after login."""
    active_index = next(
        (index for index, step in enumerate(STEPS) if step[0] == active_step),
        0,
    )
    items = []
    for index, (_, label) in enumerate(STEPS):
        state = "is-active" if index == active_index else ""
        if index < active_index:
            state = "is-complete"
        items.append(
            f'<div class="workflow-step {state}"><span></span>{label}</div>'
        )
    st.markdown(
        '<nav class="workflow-nav"><b>Portfolio Thesis Checker</b>'
        f'<div class="workflow-steps">{"".join(items)}</div></nav>',
        unsafe_allow_html=True,
    )
