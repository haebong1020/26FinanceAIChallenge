# Portfolio Thesis Checker — 팀 통합본

미국 주식 포트폴리오의 투자 논리를 데이터와 추가 질문으로 점검하는 Streamlit MVP입니다.
추천·목표 비중·수익률 예측·검증되지 않은 점수를 제공하지 않습니다.

## 통합 범위

- 메인 코드의 Supabase 로그인·회원가입·로그아웃 및 사용자별 저장
- 디자인 레포의 입력 화면, 색상·타이포그래피, 단계 표시, 질문별 화면, 8개 항목 보고서
- 기존 금융 데이터·PDF 추출·팀 기준·선택적 AI 분석
- 디자인 출처: dudwldd/26FinanceAIChallenge_design, f08b665f
- DB 출처: haebong1020/26FinanceAIChallenge, 5aca6453
- DB 상세 입력 컬럼 migration: PR #4, 19e2d4b

로그인 → 포트폴리오 입력 → 객관식 투자 기준/PDF → 데이터 점검 →
최대 3개 추가 질문(한 화면에 하나) → 최종 결과 및 저장 순서입니다.
질문은 건너뛸 수 있지만 미답변으로 표시하며, 제출 수를 논리의 품질로 평가하지 않습니다.

## 실행

Python 3.11 이상을 사용하세요.

```bash
cd investment-checker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

로컬 .env 또는 Streamlit Cloud Secrets에 다음 이름으로 설정합니다.
실제 키를 코드·PR·README에 넣지 마세요.

```text
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_publishable_key
OPENAI_API_KEY=optional_openai_key
OPENAI_MODEL=gpt-5.4-mini
```

Supabase 설정은 필수입니다. OpenAI 키는 선택이며 없으면 AI 체크박스가 비활성화됩니다.
FMP_API_KEY는 향후 사용을 위한 예약값입니다.
.env와 .streamlit/secrets.toml은 Git에서 제외됩니다.

## Supabase

- 팀의 기존 프로젝트라면 테이블·정책 적용 여부를 먼저 확인하세요.
- 기존 프로젝트에는 supabase/migrations/20260903_add_design_question_fields.sql을 한 번 적용하세요.
- 새 프로젝트에서는 supabase/schema.sql을 확인한 뒤 SQL Editor에서 적용합니다.
- 공개용 publishable/anon 키만 사용합니다. service_role 키는 사용하지 않습니다.
- Auth 이메일 인증이 켜져 있으면 가입 후 인증 이메일을 확인해야 합니다.
- 코드에 포함된 RLS 정책은 사용자 자신의 행만 조회·생성·수정하도록 설계되어 있습니다.
  실제 서버에서도 정책이 적용되어 있는지 별도 확인해야 합니다.
- 사용자마다 클라이언트를 세션별로 유지하며 로그아웃하면 입력·분석 ID를 초기화합니다.
- 새로고침으로 Streamlit 세션이 종료되면 다시 로그인할 수 있습니다.

최종 결과 단계에서 최초 투자 논리·종목·비중·객관식 답변·추가 답변·AI 결과/오류를 저장합니다.
답변 수정은 같은 행을 업데이트하고, 포트폴리오 수정은 새 분석으로 처리합니다.
저장 실패를 표시하고 재시도 버튼을 제공합니다. 응답을 받지 못한 네트워크 오류 후 재시도는
중복 저장 가능성이 있으므로 실제 배포 전 확인이 필요합니다.
PDF는 파일명·페이지 수만 저장합니다. PDF 원문과 추출 텍스트는 DB에 저장하지 않습니다.
참고 URL과 선택 근거 상세 설명은 사용자가 입력한 정보로 함께 기록합니다.

## 분석 원칙

- 산업 비중 70% 이상 또는 평균 상관계수 0.70 이상이라는 기존 팀 기준을 유지합니다.
- 산업 미확인은 집중도로 단정하지 않고, 상관계수 미확인은 숫자로 대체하지 않습니다.
- 단일 종목 및 과거 가격 조회 실패도 추가 질문으로 진행할 수 있습니다.
- 금융 데이터 조회만으로 자유서술 주장이 입증되었다고 표시하지 않습니다.
- AI가 없거나 실패하면 규칙 점검과 답변 기록만 제공하며 편향·논리 일관성 등급을 생성하지 않습니다.
- PDF: 텍스트 기반 1개, 10MB 이하, 최대 30페이지/30,000자. 스캔·암호화 PDF 미지원.
- 참고 URL은 주소만 기록하며 웹 본문은 수집하지 않습니다.
- OpenAI 분석 선택 시 투자 논리·금융 데이터·설문·PDF 추출 텍스트·추가 답변이 API로 전송됩니다.
- 비교 비중과 과거 성과는 참고용이며 투자 추천이 아닙니다.

## 주요 파일

- app.py: 입력 화면과 인증 진입점
- ui/login.py: 디자인이 적용된 실제 Supabase 인증
- ui/review_flow.py: 질문·결과 화면, 저장 흐름
- ui/styles.py, ui/workflow.py: 디자인과 단계 표시
- logic/review.py: 데이터 수집 조합, 누락값 처리, 질문 선택, 보고서 항목
- data/supabase_repository.py: 팀의 DB 저장 모듈
- supabase/schema.sql: 사용자별 접근 정책
- tests/: 금융 데이터·규칙·화면·세션·저장 호출 테스트

## 검증

```bash
python -m pytest -q
```

자동 테스트는 가짜 외부 서비스를 사용합니다. 실제 Supabase 계정 로그인·RLS 격리·저장,
실제 AI 호출, 배포 Secrets, 모바일/브라우저 디자인은 별도 실환경 확인이 필요합니다.
기존 localhost:8503은 별도 임시 디자인 코드일 수 있습니다. 위 경로의 app.py를 실행해야 통합본입니다.
