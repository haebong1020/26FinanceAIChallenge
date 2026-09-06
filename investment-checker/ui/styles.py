"""Global visual system for the Portfolio Thesis Checker."""

import streamlit as st


def apply_global_styles() -> None:
    """Apply the Figma-inspired visual tokens to Streamlit widgets."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&family=Noto+Serif+KR:wght@500;600&family=Playfair+Display:wght@600&display=swap');

        :root {
            --court-ink: #202124;
            --court-muted: #72767f;
            --court-line: #e7e8eb;
            --court-soft: #f7f8fa;
            --court-coral: #ef5447;
            --court-coral-hover: #dc463b;
            --court-mint: #20b989;
            --court-warning: #e8a600;
            --court-radius: 12px;
        }

        .stApp {
            background: #ffffff;
            color: var(--court-ink);
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
            overflow-x: hidden;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
            border-bottom: 1px solid var(--court-line);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1020px;
            padding-top: 0;
            padding-left: 0;
            padding-right: 0;
            padding-bottom: 6rem;
        }

        [data-testid="stMainBlockContainer"]:has(.login-shell) {
            max-width: 1280px;
            padding-top: 2.75rem;
            padding-left: 2.75rem;
            padding-right: 2.75rem;
        }

        [data-testid="stMainBlockContainer"]:has(.app-shell-marker) {
            max-width: 880px !important;
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        .app-shell-marker {
            display: none;
        }

        h1, h2, h3 {
            color: var(--court-ink);
            letter-spacing: -0.035em;
        }

        h1 {
            font-family: "Playfair Display", Georgia, "Times New Roman", serif !important;
            font-size: clamp(2.25rem, 5vw, 3.45rem) !important;
            line-height: 1.08 !important;
            font-weight: 500 !important;
            margin-bottom: 0.55rem !important;
        }

        h2 {
            font-size: 1.35rem !important;
            font-weight: 650 !important;
            margin-top: 2rem !important;
        }

        p, label, [data-testid="stCaptionContainer"] {
            line-height: 1.65;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--court-muted);
        }

        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stDataFrame"],
        div[data-testid="stMetric"] {
            border: 1px solid var(--court-line);
            border-radius: var(--court-radius);
            background: #ffffff;
            box-shadow: 0 8px 30px rgba(25, 31, 42, 0.035);
        }

        [data-testid="stForm"] {
            padding: 1.35rem 1.4rem 1.5rem;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div {
            border-color: var(--court-line) !important;
            border-radius: 9px !important;
            background: var(--court-soft) !important;
        }

        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="textarea"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--court-coral) !important;
            box-shadow: 0 0 0 1px var(--court-coral) !important;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            min-height: 2.85rem;
            border-radius: 9px;
            border: 1px solid var(--court-line);
            font-weight: 650;
            transition: border-color 150ms ease, color 150ms ease,
                background 150ms ease, transform 150ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            color: var(--court-coral);
            border-color: var(--court-coral);
            transform: translateY(-1px);
        }

        .stFormSubmitButton > button {
            color: #ffffff;
            background: var(--court-coral);
            border-color: var(--court-coral);
        }

        .stFormSubmitButton > button:hover {
            color: #ffffff;
            background: var(--court-coral-hover);
            border-color: var(--court-coral-hover);
        }

        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed #cfd2d8;
            border-radius: var(--court-radius);
            background: var(--court-soft);
        }

        div[data-testid="stMetric"] {
            padding: 1rem 1.1rem;
        }

        [data-testid="stAlert"] {
            border-radius: var(--court-radius);
        }

        hr {
            border-color: var(--court-line) !important;
        }

        .login-shell {
            margin-top: 1.5rem;
        }

        .login-intro {
            min-height: 540px;
            padding: 5.5rem 4.5rem 4rem 0.5rem;
            border-right: 1px solid var(--court-line);
        }

        .login-eyebrow {
            display: inline-block;
            margin-bottom: 1.2rem;
            padding: 0.38rem 0.65rem;
            border-radius: 999px;
            background: #fff1ef;
            color: var(--court-coral);
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }

        .login-intro h1 {
            margin: 0 0 1.2rem !important;
            max-width: 590px;
            font-size: clamp(2rem, 3.1vw, 2.75rem) !important;
            line-height: 1.18 !important;
        }

        .login-lead {
            color: var(--court-muted);
            font-size: 0.98rem;
        }

        .login-feature-list {
            display: grid;
            gap: 0.85rem;
            margin-top: 2.3rem;
            color: #535761;
            font-size: 0.9rem;
        }

        .login-feature-list span {
            display: inline-grid;
            width: 1.6rem;
            height: 1.6rem;
            margin-right: 0.45rem;
            place-items: center;
            border-radius: 7px;
            background: #fff1ef;
            color: var(--court-coral);
            font-weight: 800;
        }

        .login-form-heading {
            padding-top: 4.7rem;
        }

        .login-form-heading h2 {
            margin: 0 0 0.15rem !important;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 1.9rem !important;
            font-weight: 500 !important;
        }

        .login-form-heading + [data-testid="stForm"] {
            margin-top: 1.3rem;
            padding: 0;
            border: 0;
            box-shadow: none;
        }

        .login-help {
            padding-top: 0.55rem;
            color: var(--court-coral);
            font-size: 0.82rem;
            text-align: right;
        }

        .login-divider {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 1.25rem 0;
            color: #a0a3a9;
            font-size: 0.76rem;
        }

        .login-divider::before,
        .login-divider::after {
            content: "";
            height: 1px;
            flex: 1;
            background: var(--court-line);
        }

        .login-signup {
            margin-top: 1.1rem;
            color: var(--court-muted);
            font-size: 0.8rem;
            text-align: center;
        }

        .login-signup span {
            color: var(--court-coral);
            font-weight: 700;
        }

        .workflow-nav {
            position: relative;
            z-index: 110;
            left: 50%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100vw;
            height: 70px;
            margin: 0 0 5rem -50vw;
            padding: 0 max(1.5rem, calc((100vw - 880px) / 2));
            box-sizing: border-box;
            border-bottom: 1px solid var(--court-line);
            background: rgba(255, 255, 255, 0.98);
            font-family: "Playfair Display", Georgia, "Times New Roman", serif;
        }

        .workflow-steps {
            display: flex;
            gap: 0.7rem;
            color: #a0a4ac;
            font-family: sans-serif;
            font-size: 0.78rem;
        }

        .workflow-step {
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .workflow-step:not(:last-child)::after {
            content: "";
            display: inline-block;
            width: 24px;
            height: 1px;
            margin-left: 0.7rem;
            background: #dce3ed;
        }

        .workflow-step span {
            display: inline-block;
            width: 6px;
            height: 6px;
            margin-right: 0.4rem;
            border-radius: 50%;
            background: #d8dbe0;
            vertical-align: middle;
        }

        .workflow-step.is-active {
            color: var(--court-ink);
            font-weight: 700;
        }

        .workflow-step.is-active span {
            background: var(--court-coral);
        }

        .workflow-step.is-complete span {
            background: var(--court-mint);
        }

        .page-hero {
            margin: 0 0 2.2rem;
        }

        .page-hero h1 {
            margin: 0 0 0.7rem !important;
            padding: 0 !important;
            color: #0f172a;
            font-family: "Playfair Display", Georgia, "Times New Roman", serif !important;
            font-size: clamp(2.8rem, 4vw, 3.4rem) !important;
            font-weight: 600 !important;
            line-height: 1.12 !important;
            letter-spacing: -0.035em;
        }

        .page-hero p {
            margin: 0;
            color: #71829b;
            font-size: 1rem;
            line-height: 1.55;
        }

        .criteria-hero {
            margin: 0.75rem 0 1.4rem;
        }

        .criteria-hero h1 {
            margin: 0 0 0.7rem !important;
            padding: 0 !important;
            color: #111827;
            font-family: "Noto Serif KR", "Batang", serif !important;
            font-size: clamp(2.15rem, 3.4vw, 2.6rem) !important;
            font-weight: 500 !important;
            line-height: 1.25 !important;
            letter-spacing: -0.055em;
        }

        .criteria-hero p {
            margin: 0;
            color: #9aa4b3;
            font-size: 0.98rem;
        }

        .stButton > button {
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif !important;
        }

        .criteria-question {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin: 2.25rem 0 1rem;
            color: #1f2a3d;
        }

        .criteria-question.first {
            margin-top: 0.5rem;
        }

        .st-key-criteria_back button {
            min-height: 44px;
            color: #273449 !important;
            border-color: #dbe3ee !important;
            background: #ffffff !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
        }

        .criteria-question span {
            display: inline-grid;
            min-width: 34px;
            height: 34px;
            place-items: center;
            border-radius: 50%;
            background: #fff2f0;
            color: var(--court-coral);
            font-size: 0.85rem;
            font-weight: 700;
        }

        .criteria-question strong {
            font-size: 1.05rem;
            font-weight: 500;
        }

        div[data-testid="stButtonGroup"] {
            margin-bottom: 0.9rem;
        }

        div[data-testid="stButtonGroup"] [role="toolbar"] {
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem 0.9rem !important;
        }

        div[data-testid="stButtonGroup"] button {
            min-height: 46px;
            padding: 0.65rem 1.25rem;
            border: 1px solid #d9e1ec;
            border-radius: 999px;
            background: #ffffff;
            color: #344054;
            font-family: "Noto Sans KR", sans-serif;
            font-size: 0.94rem;
            transition: color 140ms ease, border-color 140ms ease,
                background 140ms ease, transform 140ms ease;
        }

        div[data-testid="stButtonGroup"] button:hover {
            border-color: var(--court-coral);
            background: #fff7f6;
            color: var(--court-coral);
            transform: translateY(-1px);
        }

        div[data-testid="stButtonGroup"] button[aria-pressed="true"] {
            border-color: var(--court-coral);
            background: #fff1ef;
            color: var(--court-coral);
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .factor-detail-heading
        ) {
            margin-top: 0.5rem;
            padding: 1.4rem 1.55rem 1.5rem !important;
            border: 1px solid #dce4ef !important;
            border-radius: 16px !important;
            background: #f7f9fc !important;
        }

        .factor-detail-heading {
            margin-bottom: 0.9rem;
            color: #344054;
        }

        .factor-detail-heading strong {
            font-size: 0.94rem;
            font-weight: 500;
        }

        .factor-detail-heading span,
        .factor-detail-heading p {
            color: #91a0b6;
        }

        .factor-detail-heading span {
            margin-left: 0.25rem;
            font-size: 0.82rem;
        }

        .factor-detail-heading p {
            margin: 0.3rem 0 0;
            font-size: 0.83rem;
        }

        div[data-testid="stRadio"] [role="radiogroup"] {
            gap: 0.55rem;
        }

        div[data-testid="stRadio"] [role="radiogroup"] > label {
            width: 100%;
            min-height: 54px;
            margin: 0;
            padding: 0.75rem 1rem;
            border: 1px solid #dbe3ee;
            border-radius: 13px;
            background: #ffffff;
            transition: border-color 140ms ease, background 140ms ease,
                box-shadow 140ms ease, transform 140ms ease;
        }

        div[data-testid="stRadio"] [role="radiogroup"] > label:hover {
            border-color: #9eb0c8;
            background: #f7f9fc;
            box-shadow: 0 3px 10px rgba(44, 62, 88, 0.05);
            transform: translateY(-1px);
        }

        div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
            border-color: var(--court-coral);
            background: #fff7f6;
        }

        div[data-testid="stRadio"] [role="radiogroup"] > label p {
            color: #344054;
            font-size: 0.94rem;
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .evidence-panel-heading
        ) {
            margin: 2rem 0 0.5rem;
            padding: 1.6rem 1.75rem 1.7rem !important;
            border: 1px solid #dce4ef !important;
            border-radius: 18px !important;
            background: #f7f9fc !important;
        }

        .evidence-panel-heading strong {
            color: #344054;
            font-size: 0.95rem;
            font-weight: 500;
        }

        .evidence-panel-heading p {
            margin: 0.35rem 0 1.1rem;
            color: #8fa0b7;
            font-size: 0.86rem;
        }

        div[data-testid="stVerticalBlock"]:has(.evidence-panel-heading)
        [data-testid="stFileUploaderDropzone"] {
            position: relative;
            min-height: 260px;
            border: 1px dashed transparent;
            border-radius: 16px;
            background: transparent;
            cursor: pointer;
        }

        .upload-visual {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 260px;
            margin-bottom: -260px;
            padding: 1.25rem;
            border: 1px dashed #d7e0ec;
            border-radius: 16px;
            background: #ffffff;
            color: #8fa0b7;
            font-family: "Noto Sans KR", sans-serif;
            text-align: center;
            pointer-events: none;
        }

        .upload-icon {
            display: grid;
            width: 54px;
            height: 54px;
            margin-bottom: 0.65rem;
            place-items: center;
            border: 1px solid #dbe3ee;
            border-radius: 14px;
            background: #f9fbfd;
            color: #90a4be;
            font-size: 1.5rem;
            line-height: 1;
        }

        .upload-visual strong {
            color: #253247;
            font-size: 0.98rem;
            font-weight: 650;
        }

        .upload-visual p {
            margin: 0.25rem 0 0.85rem;
            color: #8fa0b7;
            font-size: 0.82rem;
            line-height: 1.55;
        }

        .upload-visual small {
            padding: 0.45rem 0.8rem;
            border: 1px solid #dce4ef;
            border-radius: 999px;
            background: #ffffff;
            color: #8fa0b7;
            font-size: 0.76rem;
        }

        div[data-testid="stVerticalBlock"]:has(.evidence-panel-heading)
        [data-testid="stFileUploaderDropzone"] > div {
            opacity: 0;
        }

        div[data-testid="stVerticalBlock"]:has(.evidence-panel-heading)
        [data-testid="stFileUploaderDropzone"] button {
            position: absolute;
            inset: 0;
            z-index: 2;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }

        div[data-testid="stVerticalBlock"]:has(.evidence-panel-heading)
        div[data-baseweb="input"] > div {
            background: #ffffff !important;
        }

        div[data-testid="stVerticalBlock"]:has(.evidence-panel-heading)
        div[data-testid="stButton"] button {
            color: #ffffff;
            border-color: #111827;
            background: #111827;
        }

        .analysis-loading {
            position: fixed;
            z-index: 100;
            inset: 70px 0 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
            max-width: none;
            height: calc(100vh - 70px);
            margin: 0;
            padding: 1.5rem;
            box-sizing: border-box;
            overflow: hidden;
            background: #ffffff;
            font-size: 16px;
            text-align: center;
        }

        [data-testid="stMain"]:has(.analysis-loading) {
            overflow-y: scroll !important;
            scrollbar-gutter: stable;
        }

        [data-testid="stMain"] {
            scrollbar-gutter: stable;
        }

        .analysis-loading h1 {
            margin: 1rem 0 0.55rem !important;
            font-size: 2rem !important;
            white-space: nowrap;
        }

        .loading-spinner {
            width: 60px;
            height: 60px;
            min-width: 60px;
            min-height: 60px;
            flex: 0 0 auto;
            margin: 0 auto;
            box-sizing: border-box;
            border: 5px solid #eef0ff;
            border-top-color: #646cff;
            border-radius: 50%;
            animation: court-spin 0.9s linear infinite;
        }

        @keyframes court-spin {
            to { transform: rotate(360deg); }
        }

        .loading-lead {
            margin: 0;
            color: #76849f;
            font-size: 0.92rem;
            line-height: 1.65;
        }

        .loading-card {
            width: min(520px, calc(100vw - 3rem));
            margin-top: 2rem;
            padding: 1.2rem 1.45rem;
            border: 1px solid #dde2ed;
            border-radius: 18px;
            background: #ffffff;
            text-align: left;
            box-shadow: 0 10px 35px rgba(42, 55, 82, 0.04);
        }

        .loading-stage {
            position: relative;
            display: grid;
            grid-template-columns: 38px 1fr;
            min-height: 64px;
            color: #a3adbf;
        }

        .loading-stage:not(:last-child)::after {
            content: "";
            position: absolute;
            top: 34px;
            bottom: -2px;
            left: 15px;
            width: 2px;
            background: #e5e9f1;
        }

        .loading-stage.complete:not(:last-child)::after,
        .loading-stage.active:not(:last-child)::after {
            background: #666cff;
        }

        .loading-node {
            z-index: 1;
            display: grid;
            width: 32px;
            height: 32px;
            place-items: center;
            border: 2px solid #e1e6ef;
            border-radius: 50%;
            background: #f8f9fc;
            font-weight: 800;
        }

        .loading-stage strong {
            display: block;
            padding-top: 0.25rem;
            font-size: 0.92rem;
        }

        .loading-stage p {
            margin: 0.15rem 0 0;
            font-size: 0.8rem;
        }

        .loading-stage.active,
        .loading-stage.complete {
            color: #6068ff;
        }

        .loading-stage.active .loading-node {
            animation: court-spin 1.1s linear infinite;
        }

        .loading-stage.complete .loading-node {
            color: #ffffff;
            border-color: #646cff;
            background: #646cff;
        }

        .result-analysis-loading .loading-spinner {
            width: 62px;
            height: 62px;
            min-width: 62px;
            min-height: 62px;
            border-width: 5px;
            border-color: #fcecea;
            border-top-color: var(--court-coral);
        }

        .result-analysis-loading {
            transform: translateY(2px);
            font-size: 14px;
        }

        .result-analysis-loading h1 {
            margin: 1.25rem 0 0.55rem !important;
            font-size: 1.9rem !important;
        }

        .result-analysis-loading .loading-lead {
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .result-analysis-loading .loading-card {
            width: min(500px, calc(100vw - 3rem));
            margin-top: 2.5rem;
            padding: 1.15rem 1.35rem;
            border-radius: 17px;
        }

        .result-analysis-loading .loading-stage {
            grid-template-columns: 38px 1fr;
            min-height: 60px;
        }

        .result-analysis-loading .loading-node {
            width: 30px;
            height: 30px;
            font-size: 0.82rem;
        }

        .result-analysis-loading .loading-stage:not(:last-child)::after {
            top: 31px;
            bottom: -1px;
            left: 14px;
            width: 2px;
        }

        .result-analysis-loading .loading-stage strong {
            padding-top: 0.12rem;
            font-size: 0.88rem;
        }

        .result-analysis-loading .loading-stage p {
            margin-top: 0.15rem;
            font-size: 0.76rem;
        }

        .result-analysis-loading .loading-stage.complete {
            color: #19b886;
        }

        .result-analysis-loading .loading-stage.active {
            color: var(--court-coral);
        }

        .result-analysis-loading .loading-stage.complete .loading-node {
            border-color: #19b886;
            background: #19b886;
        }

        .result-analysis-loading .loading-stage.active .loading-node {
            border-color: var(--court-coral);
        }

        .result-analysis-loading .loading-stage.complete:not(:last-child)::after {
            background: #19b886;
        }

        .result-analysis-loading .loading-stage.active:not(:last-child)::after {
            background: var(--court-coral);
        }

        [data-testid="stMainBlockContainer"]:has(.followup-hero) .workflow-nav {
            margin-bottom: 1.8rem;
        }

        .followup-hero {
            margin: 0 0 1.35rem;
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
        }

        .followup-progress-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            width: 100%;
        }

        .followup-progress-copy {
            flex: 0 0 auto;
            color: #91a0b6;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .followup-progress {
            flex: 1 1 auto;
            height: 3px;
            overflow: hidden;
            border-radius: 999px;
            background: #dfe6ef;
        }

        .followup-progress span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: var(--court-coral);
            transition: width 180ms ease;
        }

        .followup-hero h1 {
            display: block;
            width: 100%;
            margin: 1.25rem 0 0.15rem !important;
            color: #111827;
            font-family: "Noto Serif KR", "Batang", serif !important;
            font-size: 2rem !important;
            font-weight: 500 !important;
            line-height: 1.15 !important;
            letter-spacing: -0.045em;
            white-space: nowrap;
        }

        .followup-hero p {
            margin: 0;
            color: #71829b;
            font-size: 0.86rem;
            line-height: 1.6;
        }

        .followup-risk-chip {
            display: inline-flex;
            width: fit-content;
            margin: 0 0 1rem;
            padding: 0.45rem 0.7rem;
            border: 1px solid #f5bf5b;
            border-radius: 9px;
            background: #fffaf0;
            color: #ad6800;
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
            font-size: 0.76rem;
            font-weight: 600;
        }

        .followup-question-card {
            margin-bottom: 1.35rem;
            padding: 1.35rem 1.55rem;
            border: 1px solid #dce4ef;
            border-radius: 17px;
            background: #ffffff;
            color: #253247;
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
            font-size: 0.94rem;
            line-height: 1.8;
            box-shadow: 0 3px 10px rgba(43, 59, 82, 0.025);
        }

        .followup-answer-label {
            margin-bottom: 0.45rem;
            color: #344054;
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
            font-size: 0.82rem;
        }

        .followup-answer-label span {
            color: #91a0b6;
        }

        div[class*="st-key-cross_examination_answer_"] textarea {
            min-height: 160px;
            border-color: #dce4ef !important;
            border-radius: 14px !important;
            background: #ffffff !important;
            color: #344054 !important;
            font-family: "Noto Sans KR", "Apple SD Gothic Neo", sans-serif !important;
            font-size: 0.88rem !important;
        }

        div[class*="st-key-followup_skip_"] button {
            justify-content: flex-start;
            padding-left: 0;
            color: #91a0b6;
            border-color: transparent;
            background: transparent;
            text-decoration: underline;
            box-shadow: none;
        }

        div[class*="st-key-followup_skip_"] button:hover {
            color: #667085;
            border-color: transparent;
            background: transparent;
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .portfolio-card-title
        ) {
            margin-bottom: 1.4rem;
            padding: 3rem 3.2rem 3.1rem !important;
            border: 1px solid #dbe3ee !important;
            border-radius: 22px !important;
            background: #ffffff !important;
            box-shadow: 0 3px 12px rgba(43, 59, 82, 0.035) !important;
        }

        .portfolio-card-title {
            margin: 0 0 2.25rem !important;
            padding: 0 !important;
            font-family: "Noto Serif KR", "Batang", serif !important;
            font-size: 1.55rem !important;
            font-weight: 500 !important;
            letter-spacing: -0.04em;
            line-height: 1.45 !important;
        }

        .portfolio-card-title.thesis {
            margin-bottom: 0.45rem !important;
        }

        .portfolio-card-copy {
            margin: 0 0 1.25rem;
            color: #8ea0b9;
            font-size: 0.95rem;
        }

        .portfolio-column-label {
            padding: 0 0.3rem 0.85rem;
            border-bottom: 1px solid #dce4ef;
            color: #93a3ba;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
        }

        .portfolio-header-gap {
            height: 0.8rem;
        }

        .portfolio-column-label.right {
            text-align: right;
        }

        .portfolio-total {
            padding-top: 0.65rem;
            color: #94a3b8;
            text-align: right;
        }

        .portfolio-total strong {
            margin-left: 0.35rem;
            font-size: 1.18rem;
            font-style: italic;
        }

        .portfolio-total.valid strong {
            color: #10b981;
        }

        .portfolio-total.invalid strong {
            color: var(--court-coral);
        }

        .portfolio-rule {
            height: 1px;
            margin: 1rem 0 0.95rem;
            background: #dce4ef;
        }

        button[kind="primary"] {
            color: #ffffff !important;
            border-color: var(--court-coral) !important;
            background: var(--court-coral) !important;
        }

        button[kind="primary"]:hover {
            border-color: var(--court-coral-hover) !important;
            background: var(--court-coral-hover) !important;
        }

        div[data-testid="stNumberInput"] input {
            font-weight: 700;
            text-align: right;
        }

        div[data-testid="stNumberInput"] button {
            display: none;
        }

        div[data-baseweb="input"] > div {
            min-height: 52px;
        }

        div[data-testid="stTextInput"] input {
            color: #111827;
            font-weight: 600;
            letter-spacing: 0.04em;
        }

        [data-testid="stMainBlockContainer"]:has(.final-report) {
            max-width: 680px;
            padding-top: 2.4rem;
            padding-bottom: 4rem;
        }

        .final-report {
            color: #111827;
            font-size: 14px;
        }

        .result-kicker {
            color: #15b981;
            font-size: 0.72rem;
            font-weight: 800;
        }

        .final-report > h1 {
            margin: 0.65rem 0 0.8rem !important;
            font-size: 34px !important;
            line-height: 1.15;
        }

        .result-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        .result-pills span {
            padding: 0.3rem 0.65rem;
            color: #8090aa;
            border: 1px solid #dbe2ed;
            border-radius: 999px;
            background: #fff;
            font-size: 0.68rem;
        }

        .result-rule {
            height: 0;
            margin: 1.4rem 0 2.2rem;
            background: transparent;
        }

        .final-report section {
            margin-bottom: 2.4rem;
        }

        .final-report section h2 {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0 0 1rem !important;
            font-size: 1.08rem !important;
            font-family: inherit !important;
            font-weight: 800;
        }

        .final-report section h2::after {
            content: "";
            flex: 1;
            height: 1px;
            background: #dce3ed;
        }

        .final-report section h2 em {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            flex: 0 0 32px;
            color: var(--court-coral);
            border-radius: 50%;
            background: #fff0ee;
            font-size: 1.02rem;
            font-weight: 800;
            font-style: normal;
        }

        .result-section-copy {
            margin: -0.65rem 0 1rem 1.75rem;
            color: #8b98ad;
            font-size: 0.72rem;
        }

        .result-score-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.55rem;
        }

        .result-score-card {
            min-height: 92px;
            padding: 0.85rem 0.9rem;
            border: 1px solid #dce3ed;
            border-top: 3px solid #f4a300;
            border-radius: 10px;
            background: #fff;
        }

        .result-score-card.good { border-top-color: #15b981; }
        .result-score-card.bad { border-top-color: var(--court-coral); }

        .result-score-card > div {
            display: flex;
            justify-content: space-between;
            gap: 0.5rem;
        }

        .result-score-card strong { font-size: 0.9rem; }
        .result-score-card span {
            padding: 0.15rem 0.35rem;
            color: #c98100;
            border-radius: 4px;
            background: #fff5d9;
            font-size: 0.58rem;
            font-weight: 800;
        }
        .result-score-card.good span { color: #099d70; background: #e5faf3; }
        .result-score-card.bad span { color: #e64b40; background: #ffebe9; }
        .result-score-card p { margin: 0.65rem 0 0; color: #57657b; font-size: 0.86rem; line-height: 1.6; }

        .result-thesis {
            margin: 1.1rem auto 0;
            padding: 1.1rem 1.25rem;
            border: 1px solid #dce3ed;
            border-radius: 10px;
        }

        .result-thesis blockquote {
            margin: 0 0 1rem;
            padding-left: 0.8rem;
            border-left: 2px solid var(--court-coral);
            font-size: 1rem;
            font-weight: 700;
        }

        .result-thesis dl { display: grid; grid-template-columns: 70px 1fr 70px 1fr; gap: 0.65rem; margin: 0; }
        .result-thesis dt { color: #92a0b4; font-size: 0.62rem; }
        .result-thesis dd { margin: 0; padding-bottom: 0.4rem; border-bottom: 1px solid #e3e8f0; font-size: 0.88rem; }

        .result-evidence {
            display: flex;
            gap: 0.9rem;
            margin-bottom: 0.55rem;
            padding: 0.8rem 1rem;
            border: 1px solid #dce3ed;
            border-left: 3px solid #15b981;
            border-radius: 9px;
        }
        .result-evidence.warn { border-left-color: #f4a300; }
        .result-evidence.bad { border-left-color: var(--court-coral); }
        .result-evidence > b { color: #15b981; }
        .result-evidence.warn > b { color: #f4a300; }
        .result-evidence.bad > b { color: var(--court-coral); }
        .result-evidence strong { display: block; font-size: 0.92rem; }
        .result-evidence small { display: block; margin-top: 0.25rem; color: #74839a; font-size: 0.82rem; }

        .result-bias {
            display: grid;
            grid-template-columns: 82px 1fr;
            gap: 0.8rem;
            margin-bottom: 0.55rem;
            padding: 0.75rem 1rem;
            border: 1px solid #dce3ed;
            border-left: 3px solid #f4a300;
            border-radius: 9px;
        }
        .result-bias strong { padding: 0.45rem; color: #a86800; border: 1px solid #f1c665; border-radius: 7px; background: #fffaf0; text-align: center; font-size: 0.68rem; }
        .result-bias p { margin: 0; align-self: center; font-size: 0.88rem; line-height: 1.6; }

        .result-qa {
            margin-bottom: 0.75rem;
            overflow: hidden;
            color: #fff;
            border-radius: 10px;
            background: #111a2d;
            box-shadow: 0 3px 10px rgba(18, 27, 46, 0.12);
        }
        .result-qa > div { display: flex; align-items: center; gap: 0.7rem; padding: 0.75rem 1rem 0; }
        .result-qa small { color: #7f8da5; font-weight: 800; }
        .result-qa span { padding: 0.2rem 0.45rem; color: #ffd95f; border: 1px solid #826c1d; border-radius: 5px; font-size: 0.58rem; font-weight: 800; }
        .result-qa > strong { display: block; padding: 0.65rem 1rem 0.9rem; font-size: 0.92rem; line-height: 1.65; }
        .result-qa > p { margin: 0; padding: 0.75rem 1rem; color: #bc6c1b; background: #fff9e8; font-size: 0.88rem; font-style: italic; }

        .result-empty {
            padding: 1rem;
            color: #8694aa;
            border: 1px solid #dce3ed;
            border-radius: 9px;
            text-align: center;
            font-size: 0.9rem;
            font-style: italic;
        }

        .result-checklist { margin: 0; padding: 0; overflow: hidden; border: 1px solid #dce3ed; border-radius: 9px; list-style: none; }
        .result-checklist li { display: flex; gap: 0.8rem; padding: 0.75rem 1rem; border-bottom: 1px solid #dce3ed; font-size: 0.86rem; }
        .result-checklist li:last-child { border-bottom: 0; }
        .result-checklist i { width: 12px; height: 12px; flex: 0 0 auto; border: 1px solid #cfd8e6; border-radius: 2px; }

        .result-limitations { overflow: hidden; border: 1px solid #dce3ed; border-radius: 9px; }
        .result-limitations summary { padding: 0.8rem 1rem; font-size: 0.9rem; font-weight: 800; cursor: pointer; }
        .result-limitations ul { margin: 0; padding: 0.8rem 1.7rem 1rem; border-top: 1px solid #dce3ed; color: #64738a; font-size: 0.84rem; line-height: 1.8; }
        .result-api-warning { margin-bottom: 1rem; padding: 0.8rem; color: #9a6500; border-radius: 8px; background: #fff9df; }

        [data-testid="stMainBlockContainer"]:has(.final-report) > div > div > div[data-testid="stHorizontalBlock"] {
            padding-top: 1rem;
            border-top: 1px solid #dce3ed;
        }

        @media (max-width: 720px) {
            [data-testid="stMainBlockContainer"] {
                padding: 0 1rem 4rem;
            }

            [data-testid="stMainBlockContainer"]:has(.login-shell) {
                padding: 2rem 1rem 4rem;
            }

            [data-testid="stMainBlockContainer"]:has(.app-shell-marker) {
                padding: 0 1rem 4rem !important;
            }

            [data-testid="stForm"] {
                padding: 1rem;
            }

            div[data-testid="stVerticalBlock"]:has(
                > div[data-testid="stElementContainer"] .portfolio-card-title
            ) {
                padding: 1.6rem 1.3rem 1.8rem !important;
                border-radius: 17px;
            }

            .login-intro {
                min-height: auto;
                padding: 2rem 0 1.5rem;
                border-right: 0;
                border-bottom: 1px solid var(--court-line);
            }

            .login-form-heading {
                padding-top: 1rem;
            }

            .workflow-nav,
            .workflow-steps {
                align-items: flex-start;
            }

            .workflow-nav {
                gap: 1rem;
                height: auto;
                margin-bottom: 3rem;
                padding-top: 1rem;
                padding-bottom: 1rem;
            }

            .workflow-steps {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.45rem 0.8rem;
            }

            .result-score-grid { grid-template-columns: 1fr; }
            .result-thesis dl { grid-template-columns: 70px 1fr; }
            .result-bias { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
