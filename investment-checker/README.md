# Portfolio Thesis Checker

> 작업 기록 (2026-09-03): 디자인 저장소 `dudwldd/26FinanceAIChallenge_design`의
> Streamlit 화면을 적용하고, 기존 Supabase 이메일/비밀번호 인증 및 분석 결과
> 저장을 연결했다. 아래의 **디자인·DB 적용 현황**과 **실행·로그인 점검**을 다음
> 작업 시작점으로 사용한다.

A minimal Streamlit proof of concept that retrieves financial data to help users
evaluate the reasoning behind a US-listed stock portfolio. It does not optimize
portfolio weights, make buy/sell decisions, or recommend securities. An optional
AI layer classifies the thesis, separates supported and uncertain points, flags
possible biases, and produces devil's-advocate questions.

## Project structure

```text
investment-checker/
├── app.py
├── data/financial_data.py
├── ai/portfolio_analyzer.py
├── logic/fact_check.py
├── tests/test_financial_data.py
├── requirements.txt
├── .env.example
└── .gitignore
```

The financial-data layer currently retrieves normalized data from yfinance. The
optional AI analysis uses OpenAI Structured Outputs so its result has a stable
shape for the Streamlit UI.

Users can enter up to ten tickers and portfolio weights. The app validates that
weights total 100%, rejects duplicate or malformed tickers, retrieves each
holding's basic financial data, and displays the largest holding and combined
weight of the top two holdings. It also aggregates weights by sector and shows a
one-year daily-return correlation matrix. Correlation is presented as historical
context, not as a forecast or investment recommendation.

For thesis checking, the app compares the user's weights with equal weights and
inverse-volatility weights. It shows historical return, annualized volatility,
and maximum drawdown under each weighting method, then generates deterministic
questions about material differences. These are comparison references, not
recommended or target allocations.

Users may optionally attach one text-based PDF up to 10MB. The app extracts
page-aware text in memory, shows a short preview, and includes the bounded text
in the optional AI analysis. The PDF is not stored in a database. Image-only
scans and encrypted PDFs are not supported in this MVP.

Each `Check my thesis` submission is stored against the signed-in user's ID and
cannot be read by another user. If the user completes the cross-examination,
the same record is updated with those answers and optional AI output. PDF text
is never stored; only its filename and page count are retained when a PDF was
attached.

The app also applies three deterministic team review standards: diversification
illusion (sector weight of at least 70% or average correlation of at least
0.70), mismatch between long-term reasoning and a horizon below one year, and
quantitative claims made with a low level of supporting research. Each triggered
standard shows its measured basis, a neutral diagnosis, and a follow-up question.

The review flow has two stages. The first stage identifies issues and selects up
to three cross-examination questions. The user answers those questions in a
second form before seeing the final review. Without an OpenAI API key, the app
records the completed answers without claiming to understand their meaning. If
optional AI analysis is enabled, the final step compares the original thesis and
follow-up answers for support, unresolved assumptions, and rationale changes.

## Installation

Python 3.10 or newer is recommended.

```bash
cd investment-checker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Copy the example file if you plan to add Financial Modeling Prep later:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` to enable the optional AI checkbox. `OPENAI_MODEL` defaults
to `gpt-5.4-mini`. `FMP_API_KEY` is reserved for a later FMP integration. No key
is required for the existing deterministic portfolio analysis, and `.env` is
excluded from Git.

```text
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.4-mini

SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_publishable_key_here
```

### Supabase setup

1. Create a Supabase project, then open **SQL Editor** and run
   `supabase/schema.sql` once.
2. Open **Project Settings → API** and copy the Project URL and the
   **publishable** key (called `anon` in legacy projects).
3. Put them in `SUPABASE_URL` and `SUPABASE_KEY` in `.env`, or configure the
   same values as Streamlit secrets when deploying.

기존 `thesis_reviews` 테이블을 이미 생성했다면, 디자인 질문 흐름의 추가 입력값을
저장하기 위해 다음 SQL도 한 번 실행해야 한다.

```sql
alter table public.thesis_reviews
  add column if not exists factor_detail text not null default '',
  add column if not exists evidence_url text,
  add column if not exists workflow_version text not null default 'design-v1';
```

전체 SQL은 [supabase/migrations/20260903_add_design_question_fields.sql](supabase/migrations/20260903_add_design_question_fields.sql)에 있다. 이 마이그레이션은 기존 분석 기록을 삭제하거나 수정하지 않고 컬럼만 추가한다.

사용자별로 최신 분석 1건만 유지하려면 [supabase/migrations/20260906_one_review_per_user.sql](supabase/migrations/20260906_one_review_per_user.sql)을 한 번 실행한다. 이 마이그레이션은 사용자별 기존 기록 중 가장 최근 기록만 남기므로, 실행 전 기존 분석 이력을 보관해야 한다면 별도로 백업해야 한다.

The included Row Level Security policies require a signed-in user and allow that
user to insert and read only their own reviews. Do not add an anonymous-insert
policy as a temporary shortcut. Do not use a `service_role` key in Streamlit or
commit real keys to Git.

### Login-ready Supabase integration status

The database integration includes a minimal email/password login and sign-up
screen using Supabase Auth.

| Area | Prepared state |
| --- | --- |
| Supabase client | `app.py` creates one client per Streamlit browser session and retains it in `st.session_state["supabase_client"]`. |
| Credentials | `SUPABASE_URL` and `SUPABASE_KEY` are loaded from `.env` first, then Streamlit secrets. |
| Authentication | The app requires a Supabase Auth session before showing the thesis checker. Login and sign-up use an email as the account ID plus a password. |
| Data ownership | `thesis_reviews.user_id` references `auth.users(id)`. |
| Row Level Security | An authenticated user can insert and select only rows whose `user_id` equals `auth.uid()`. Anonymous access is denied. |
| Saved data | A row is created immediately after `Check my thesis`. It contains the original thesis, holdings, questionnaire, and PDF metadata. Final cross-examination answers and optional AI analysis are added to the same row later. PDF contents are not saved. |

#### Supabase Dashboard settings to configure now

1. In **Authentication → Providers**, enable **Email** if email/password login
   will be used. It is commonly enabled by default; confirm it before building
   the screen.
2. In **Authentication → Sign In / Providers → Email**, turn **Confirm email**
   off. This app intentionally uses a simple ID/password flow without email
   verification.
3. Run `supabase/schema.sql` only after creating the project. It creates the
   `thesis_reviews` table and enables the user-scoped RLS policies.

#### Login implementation details

The login and sign-up screens in `app.py` already use the existing session
client. Do not create a separate global client or use a `service_role` key.
After successful email/password sign-in, Supabase keeps the authenticated
session on that client. `Check my thesis` saves the review with that user ID;
the final submission updates the same review.

The relevant login call is:

```python
supabase_client = get_session_supabase_client()
result = supabase_client.auth.sign_in_with_password(
    {"email": email, "password": password}
)
```

Registration uses `supabase_client.auth.sign_up(...)` with the same email and
password fields. Sign-out uses `supabase_client.auth.sign_out()`. A future
history page can query `thesis_reviews`; the existing `select` RLS policy will
automatically limit it to the signed-in user's records.

### 디자인·DB 적용 현황

- `ui/styles.py`, `ui/workflow.py`, `ui/login.py`: 디자인 저장소의 로그인,
  단계 내비게이션, 로딩, 결과 화면 스타일을 적용했다.
- 로그인·회원가입·로그아웃은 시연용 상태값이 아니라 Supabase Auth를 사용한다.
- 디자인의 투자 기준 화면은 다음 입력을 받는다: 핵심 근거, 선택 근거 상세 설명,
  구성 계기, 자료 확인 수준, PDF, 참고 URL, 투자 기간, 30% 하락 시 대응.
- `factor_detail`, `evidence_url`, `workflow_version`은 전용 DB 컬럼에 저장한다.
  나머지 질문 답변은 기존 `questionnaire` JSONB 컬럼에 저장한다.
- PDF의 원문은 저장하지 않고, 파일명과 페이지 수만 `evidence_metadata`에 저장한다.
- 새 포트폴리오 분석을 시작하면 같은 사용자의 기존 `thesis_reviews` 레코드를
  덮어쓴다. 따라서 사용자별 최신 분석 결과 1건만 저장된다.
- 추가 점검 질문은 디자인 흐름에 맞춰 3단계로 표시되며, 최종 답변과 선택적 AI
  분석 결과는 같은 `thesis_reviews` 레코드에 업데이트된다.

### 실행·로그인 점검

```bash
cd "/Users/osemin/Library/Mobile Documents/com~apple~CloudDocs/SNU/사이드 프로젝트/26FinanceAIChallenge/investment-checker"
source .venv/bin/activate
python -m pytest -q
streamlit run app.py
```

브라우저 주소는 `http://localhost:8501`이다. 실행 전에 `.env`의
`SUPABASE_URL`, `SUPABASE_KEY`가 실제 프로젝트의 URL과 publishable key인지
확인한다.

로그인 화면은 현재 Supabase의 모든 로그인 실패를 동일한 문구로 표시한다. 로그인에
실패하면 먼저 다음을 확인한다.

1. 로그인하려는 이메일이 회원가입 화면을 통해 실제로 등록되었는지
2. Supabase Dashboard → Authentication → Users에 해당 사용자가 있는지
3. Supabase에서 **Confirm email**을 켰다면 수신한 인증 메일을 완료했는지. 간단한
   로컬 테스트만 할 경우 Authentication의 Email 설정에서 이를 끌 수 있다.
4. `.env`를 수정했다면 Streamlit 서버를 종료 후 다시 실행했는지

이번 작업에서는 로컬 서버를 `streamlit run app.py --server.headless true --server.port 8501`로 시작했다. 이후 터미널 오류가 의심되어 추가 진단은 중단했다.

## Run the app

```bash
streamlit run app.py
```

Enter portfolio tickers and weights, describe the portfolio thesis, answer the
five multiple-choice questions, optionally enable AI analysis, then select
**Check my thesis**. The app shows
simple concentration metrics and a table of available financial data. It does
not score the answers, forecast returns, or calculate optimal weights at this
POC stage. Missing provider values are displayed as `null`. When AI analysis is
enabled, the thesis and the displayed portfolio-data summary are sent to the
OpenAI API; they are not stored by this app.

## Run tests

```bash
pytest
```

Tests use a fake ticker provider and do not require network access.
