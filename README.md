# Investment Thesis Checker

팀 통합 브랜치에서는 영지님의 디자인과 세민님의 Supabase 인증·저장을 연결했습니다.
최신 실행·설정·테스트 안내는 [통합본 README](investment-checker/README.md)를 참고하세요.

미국 상장주식 포트폴리오에 대한 사용자의 투자 논리를 금융 데이터와 비교해 점검하는
Streamlit 기반 금융 AI Challenge MVP입니다.

이 서비스는 종목이나 매수·매도 시점을 추천하지 않습니다. 사용자가 직접
제시한 투자 근거를 구조화하고, 실제 데이터와 얼마나 부합하는지 검증할 수
있도록 돕는 것이 목표입니다.

## 현재 구현된 기능

- 최대 10개 미국 상장주식 ticker와 비중 입력
- 비중 합계 100%, 중복 ticker, 잘못된 ticker 검증
- 포트폴리오 구성 논리 입력
- 판단 근거, 계기, 확인한 자료, 투자 기간, 손실 대응에 관한 객관식 문항
- yfinance를 이용한 종목별 기본 금융 데이터 조회
- 최대 비중 종목과 상위 2개 종목 집중도 표시
- 종목별 금융 데이터 표 출력
- 산업별 비중과 최대 산업 비중 표시
- 최근 1년 일별 수익률 기준 상관행렬과 평균 상관계수 표시
- 현재 비중을 동일 비중·역변동성 비중과 비교
- 비교 기준별 과거 누적수익률·변동성·최대 낙폭 표시
- 비중과 산업 집중 차이에 관한 추가 검증 질문 생성
- 선택적 OpenAI 연동을 통한 투자 논리 카테고리 분류
- AI를 통한 데이터 부합·확인 불가 항목, 편향 가능성, 반대심문 질문 생성
- 판단 근거 PDF 1개 첨부, 페이지별 텍스트 추출 및 AI 검증 문맥에 포함
- 팀 합의 기준에 따른 분산 착각·기간 불일치·근거 부족 규칙 진단
- 1차 분석 후 2~3개 반대심문 질문에 답하고 최종 진단을 확인하는 2단계 흐름
- 잘못된 ticker와 외부 API 오류 처리
- 누락된 금융 데이터를 `None`으로 처리하는 일관된 데이터 구조

현재 조회·계산하는 데이터는 다음과 같습니다.

- 회사명과 현재 주가
- 시가총액
- Trailing P/E와 P/B
- 매출 성장률과 이익률
- 부채비율
- 산업 분류와 산업별 포트폴리오 비중
- 최근 1년 가격을 이용한 일별 수익률 상관계수

## 현재 구현하지 않은 기능

- 외부 뉴스·공시까지 검색하는 Fact Check
- 점수 산정
- 매수·매도 및 종목 추천
- 포트폴리오 최적화와 목표 비중 추천
- 사용자별 과거 분석 기록 조회 화면
- 스캔 PDF OCR과 암호화 PDF 분석

통합본은 최종 결과를 Supabase의 로그인 사용자 계정에 저장합니다.
PDF 본문은 저장하지 않고 파일명·페이지 수만 기록합니다.

동일 비중과 역변동성 비중은 사용자의 선택을 검토하기 위한 비교 기준일 뿐,
서비스가 제안하는 목표 비중이나 투자 추천이 아닙니다.

## 프로젝트 구조

```text
investment-checker/
├── app.py
├── data/
│   └── financial_data.py
├── ai/
│   ├── claim_extractor.py
│   ├── question_generator.py
│   └── portfolio_analyzer.py
├── logic/
│   └── fact_check.py
├── tests/
│   └── test_financial_data.py
├── requirements.txt
├── .env.example
└── README.md
```

## 로컬 실행 방법

Python 3.10 이상을 권장합니다.

```bash
git clone https://github.com/haebong1020/26FinanceAIChallenge.git
cd 26FinanceAIChallenge/investment-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 다음 주소로 접속합니다.

```text
http://localhost:8501
```

## 환경변수

Supabase 로그인 설정은 필수입니다. AI 논리 검증을 활성화하려면
추가로 OpenAI API 키를 설정합니다.

```bash
cp .env.example .env
```

```text
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_publishable_key_here
OPENAI_MODEL=gpt-5.4-mini
FMP_API_KEY=your_fmp_api_key_here
```

`.env`는 Git에 올라가지 않도록 `.gitignore`에 포함되어 있습니다. API 키를
코드나 README에 직접 작성하지 마세요.

Streamlit Community Cloud에서는 앱 설정의 **Secrets**에 동일한 키를
추가합니다. AI 체크박스를 켠 경우에만 입력한 논리와 화면에 표시된
포트폴리오 데이터 요약이 OpenAI API로 전송됩니다. 이 앱은 그 결과를
로그인한 사용자 계정에 저장합니다. PDF 추출 본문은 DB에 저장하지 않습니다.

## 테스트

```bash
cd investment-checker
pytest
```

테스트에서는 외부 API를 직접 호출하지 않고 가짜 ticker provider를 사용합니다.

## 주의사항

이 프로젝트가 제공하는 정보는 투자 자문이 아니며, 최종 투자 판단과 책임은
사용자에게 있습니다.
