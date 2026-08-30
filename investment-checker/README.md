# Portfolio Thesis Checker

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
