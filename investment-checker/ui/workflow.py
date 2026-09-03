"""Workflow navigation and transition screens."""

import time

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


def _keep_loading_background_covered() -> None:
    """Keep a white layer mounted across the loading-to-content rerun."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        if (!doc.getElementById('workflow-transition-shield')) {
            const shield = doc.createElement('div');
            shield.id = 'workflow-transition-shield';
            Object.assign(shield.style, {
                position: 'fixed',
                zIndex: '90',
                top: '70px',
                right: '0',
                bottom: '0',
                left: '0',
                background: '#ffffff'
            });
            doc.body.appendChild(shield);
        }
        </script>
        """,
        height=0,
        width=0,
    )


def _preserve_loading_screen_during_analysis() -> None:
    """Mirror loading content into one stable overlay throughout every stage."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const shield = doc.getElementById('workflow-transition-shield');
        const loading = doc.querySelector('[data-testid="stMain"] .analysis-loading');
        if (shield && loading) {
            const clone = loading.cloneNode(true);
            clone.style.visibility = 'visible';
            shield.style.zIndex = '120';
            shield.replaceChildren(clone);
            loading.style.visibility = 'hidden';
            const main = doc.querySelector('[data-testid="stMain"]');
            if (main) {
                main.style.overflowY = 'scroll';
                main.style.scrollbarGutter = 'stable';
            }
        }
        </script>
        """,
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
        f'<div class="workflow-steps">{"".join(items)}</div>'
        '<a class="workflow-logout" href="?logout=1">로그아웃</a></nav>',
        unsafe_allow_html=True,
    )


def _loading_markup(active_index: int) -> str:
    stages = [
        ("포트폴리오 구성 파악", "입력한 종목, 비중, 투자 논리를 읽어들입니다"),
        ("데이터 대조", "재무 지표·상관관계와 투자 논리를 비교합니다"),
        ("추가 질문 생성", "논리에서 확인이 필요한 부분을 질문으로 만듭니다"),
    ]
    rows = []
    for index, (title, description) in enumerate(stages):
        if index < active_index:
            state, symbol = "complete", "✓"
        elif index == active_index:
            state, symbol = "active", "↻"
        else:
            state, symbol = "pending", "•"
        rows.append(
            f'<div class="loading-stage {state}">'
            f'<div class="loading-node">{symbol}</div>'
            f'<div><strong>{title}</strong><p>{description}</p></div>'
            '</div>'
        )
    return (
        '<section class="analysis-loading">'
        '<div class="loading-spinner"></div>'
        '<h1>추가 질문 생성 중</h1>'
        '<p class="loading-lead">입력하신 포트폴리오와 투자 논리를 바탕으로<br>'
        '확인이 필요한 부분을 분석하고 있습니다.</p>'
        f'<div class="loading-card">{"".join(rows)}</div>'
        '</section>'
    )


def _result_loading_markup(completed_count: int) -> str:
    stages = [
        ("투자 논리 구조 검토", "입력한 논리의 일관성과 근거를 파악합니다"),
        ("재무·시장 데이터 조회", "각 종목의 재무지표와 시장 데이터를 불러옵니다"),
        ("집중도 및 상관관계 측정", "섹터 집중도와 종목 간 상관관계를 분석합니다"),
        ("행동편향 점검", "확증편향 등 인지적 왜곡 패턴을 탐지합니다"),
        ("진단 결과 준비", "분석 결과를 정리하고 진단 보고서를 생성합니다"),
    ]
    rows = []
    for index, (title, description) in enumerate(stages):
        if index < completed_count:
            state, symbol = "complete", "✓"
        elif index == completed_count:
            state, symbol = "active", "↻"
        else:
            state, symbol = "pending", "•"
        rows.append(
            f'<div class="loading-stage {state}">'
            f'<div class="loading-node">{symbol}</div>'
            f'<div><strong>{title}</strong><p>{description}</p></div>'
            '</div>'
        )
    return (
        '<section class="analysis-loading result-analysis-loading">'
        '<div class="loading-spinner"></div>'
        '<h1>투자 논리 분석 중</h1>'
        '<p class="loading-lead">입력한 판단 근거와 실제 데이터의 정합성을 확인하고 있습니다.</p>'
        f'<div class="loading-card">{"".join(rows)}</div>'
        '</section>'
    )


def render_question_loading() -> None:
    """Show a short staged transition, then advance to analysis."""
    _keep_loading_background_covered()
    placeholder = st.empty()
    for active_index in range(3):
        placeholder.markdown(
            _loading_markup(active_index),
            unsafe_allow_html=True,
        )
        _preserve_loading_screen_during_analysis()
        time.sleep(1.1)
    placeholder.markdown(_loading_markup(3), unsafe_allow_html=True)
    _preserve_loading_screen_during_analysis()
    time.sleep(0.9)
    st.session_state["workflow_screen"] = "analysis"
    st.session_state["analysis_processed"] = False
    st.rerun()


def render_result_loading() -> None:
    """Complete five visible stages before final-result processing."""
    _keep_loading_background_covered()
    placeholder = st.empty()
    for completed_count in range(5):
        placeholder.markdown(
            _result_loading_markup(completed_count),
            unsafe_allow_html=True,
        )
        _preserve_loading_screen_during_analysis()
        time.sleep(1.1)
    placeholder.markdown(_result_loading_markup(5), unsafe_allow_html=True)
    _preserve_loading_screen_during_analysis()
    time.sleep(0.9)
    st.session_state["workflow_screen"] = "finalize_result"
    st.rerun()
