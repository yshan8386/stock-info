# ysj.brief PRD

> 개발/투자/AI 뉴스를 큐레이션해서 AI가 요약 브리핑하는 개인 대시보드
>
> **버전**: 3.2
> **작성일**: 2026-04-20
> **프로젝트 위상**: 개인 투자 프로그램의 기반 대시보드. "데일리 브리핑"과 "투자 개념 정리"가 첫 메뉴이며, "백테스트", "투자 현황"은 향후 확장될 메뉴.

---

## 목차

1. [제품 개요](#1-제품-개요)
2. [프로젝트 위상과 범위](#2-프로젝트-위상과-범위)
3. [사용자 시나리오](#3-사용자-시나리오)
4. [기능 명세](#4-기능-명세)
5. [화면 설계](#5-화면-설계)
6. [시스템 아키텍처](#6-시스템-아키텍처)
7. [데이터 모델](#7-데이터-모델)
8. [API 명세](#8-api-명세)
9. [외부 API 연동 및 비용 전략](#9-외부-api-연동-및-비용-전략)
10. [스케줄 작업](#10-스케줄-작업)
11. [비기능 요구사항](#11-비기능-요구사항)
12. [개발 로드맵](#12-개발-로드맵)
13. [배포 및 운영](#13-배포-및-운영)
14. [리스크 관리](#14-리스크-관리)
15. [향후 확장 계획](#15-향후-확장-계획)

---

## 1. 제품 개요

### 1.1 제품명
**ysj.brief**

### 1.2 한 줄 소개
"매일 아침, AI가 큐레이션한 개발·투자·AI 핵심 이슈를 5분 만에 파악하는 개인 대시보드. 여기서 시작해 점차 투자 도구들을 붙여나간다."

### 1.3 해결하고자 하는 문제

| 문제 | 현재 상황 | ysj.brief의 해결 |
|------|----------|-----------------|
| 정보 과부하 | 매일 수십 개의 RSS, 뉴스레터, 블로그 확인 | 3개 섹터 AI 요약 브리핑 |
| 카테고리 분산 | 개발/투자/AI 소식을 각각 다른 곳에서 확인 | 단일 브리핑에서 통합 조회 |
| 시간 부족 | 출근길 30분도 길다 | 3분 요약으로 핵심 흡수 |
| 투자 도구 분산 | 여러 툴/스프레드시트로 관리 | 하나의 대시보드로 통합 예정 |

### 1.4 핵심 가치 제안
- **큐레이션**: 18개 이상의 검증된 소스를 자동 수집
- **AI 요약**: 하루 1번 Claude가 전체 기사를 종합한 브리핑 생성
- **확장 기반**: 데일리 브리핑 → 백테스트 → 투자 현황으로 자연스럽게 확장
- **저비용**: 월 운영비 $3~5 목표 (VPS 제외)

### 1.5 성공 지표

**정량적**
- 매일 브리핑 확인률: 80% 이상
- 브리핑 페이지 로딩 시간: 1.5초 이하
- RSS 수집 실패율: 5% 이하
- Claude API 월 비용: $5 이하

**정성적**
- 출근 전 뉴스 확인 시간 단축 (30분 → 5분)
- 중요 이슈를 놓치지 않는다는 안정감
- 추후 투자 도구 확장 시 자연스러운 통합

---

## 2. 프로젝트 위상과 범위

### 2.1 프로젝트 위상

ysj.brief는 **개인 투자 대시보드의 기반**입니다. 현재는 **데일리 브리핑** 메뉴가 먼저 구현되고, 추후 **백테스트**, **투자 현황** 메뉴가 붙어나가는 구조입니다.

```
┌───────────────────────────────────────────────────────────┐
│                   ysj.brief 대시보드                       │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ ⭐ 데일리 │ │          │ │          │ │ ⭐ 투자       │  │
│  │   브리핑  │ │ 백테스트  │ │ 투자 현황│ │   개념 정리  │  │
│  │          │ │  (추후)   │ │  (추후)  │ │              │  │
│  │[지금 구현]│ │          │ │          │ │  [지금 구현]  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 2.2 이번 범위 (In Scope)

**기반 (Foundation)**
- 회원가입/로그인 (아이디, 비밀번호, 닉네임, 핸드폰, 이메일)
- 대시보드 레이아웃 (4개 메인 메뉴)
- 백테스트, 투자 현황은 **Placeholder 페이지만**

**데일리 브리핑 (Daily Brief)**
- RSS 피드 자동 수집 (18개 이상)
- AI 기반 일일 통합 브리핑 생성 (아침 6:30)
- 브리핑 내 3개 섹션: 개발/기술, 투자/금융, AI/ML
- 오늘의 브리핑 / 과거 아카이브

**투자 개념 정리 (Glossary)**
- 투자 관련 용어/개념 DB 기반 사전
- 카테고리별 분류 (기술적 분석, 성과 지표, 기본적 분석 등)
- 개념 조회, 검색, 관리 (추가/수정)

### 2.3 설계 원칙

1. **확장 기반**: 대시보드는 향후 메뉴 추가가 쉬운 구조로
2. **저비용**: Claude API 사용 최소화 (하루 1~2회 호출)
3. **단순함**: 지금은 기능 수를 늘리지 않고 브리핑 품질에 집중
4. **개인 전용**: 본인 사용만 고려 (회원가입은 있지만 공개 서비스 아님)

---

## 3. 사용자 시나리오

### 3.1 페르소나

**한한 (30대 후반, 백엔드 개발자)**
- 관심사: Next.js/React, AI 활용 개발, 국내 주식 투자
- 하루 사용 패턴:
  - **아침 출근길** (30분): 스마트폰으로 브리핑 확인
  - **점심 시간** (10분): 관심 섹션 상세 읽기
  - **주말**: 백테스트/투자 현황 기능 사용 (추후)

### 3.2 핵심 유스케이스

#### UC-01: 첫 방문 및 회원가입
```
⏰ 시점: 서비스 배포 후 첫 사용 시
🎯 목표: 계정 생성 및 로그인

흐름:
1. https://brief.ysj.example.com 접속
2. 로그인 페이지 → "회원가입" 클릭
3. 폼 작성:
   - 아이디 (예: han)
   - 비밀번호 (8자 이상)
   - 비밀번호 확인
   - 닉네임 (예: 한한)
   - 핸드폰 번호 (예: 010-1234-5678)
   - 이메일 (예: han@example.com)
4. 가입 완료 → 자동 로그인 → 홈 대시보드
```

#### UC-02: 아침 브리핑 읽기
```
⏰ 시점: 매일 오전 7:30 ~ 8:30
🎯 목표: 밤사이 나온 핵심 이슈 빠르게 파악
📱 디바이스: 스마트폰 (모바일 웹)

흐름:
1. 브라우저 북마크에서 ysj.brief 접속
2. (자동 로그인) 홈 대시보드 진입
3. 상단 "오늘의 브리핑" 카드에서 한 줄 요약 확인
4. 카드 클릭 → 전체 브리핑 페이지
5. 3개 섹션 스캔:
   - 💻 개발/기술
   - 💰 투자/금융
   - 🤖 AI/ML
6. 관심 기사 클릭 → 원문 링크 이동
```

#### UC-03: 과거 브리핑 조회
```
⏰ 시점: 주말 / 놓친 날 확인
🎯 목표: 과거 아카이브 탐색

흐름:
1. "데일리 브리핑" 메뉴 → "아카이브" 클릭
2. 날짜별 브리핑 리스트
3. 원하는 날짜 선택 → 해당 날의 브리핑 열람
4. 키워드로 검색 (예: "Claude")
```

#### UC-04: 백테스트 / 투자 현황 메뉴 접근 (Placeholder)
```
⏰ 시점: 호기심에 클릭 / 향후 확장용

흐름:
1. "백테스트" 또는 "투자 현황" 메뉴 클릭
2. "준비 중입니다" 안내 페이지
3. 추후 제공 예정 기능 리스트 확인
```

---

## 4. 기능 명세

### 4.1 우선순위 정의
- **P0**: MVP 필수
- **P1**: MVP 권장
- **P2**: 나중

### 4.2 기능 목록

#### F-AUTH: 인증 (P0)

##### F-AUTH-01: 회원가입
- **입력 필드 (모두 필수)**:
  - 아이디 (username, 영문+숫자+밑줄 4~20자, 중복 불가)
  - 비밀번호 (8자 이상)
  - 비밀번호 확인
  - 닉네임 (display_name, 2~20자)
  - 핸드폰 번호 (010-XXXX-XXXX 형식, 중복 불가)
  - 이메일 (유효한 이메일 형식, 중복 불가)
- **처리**:
  - 비밀번호 bcrypt 해시 저장
  - 핸드폰 번호 정규화 (숫자만 저장)
  - 이메일 소문자 정규화
- **UX**: 단일 폼, 실시간 유효성 검증 (아이디/이메일/핸드폰 중복 즉시 체크)

##### F-AUTH-02: 로그인/로그아웃
- **로그인**: 아이디 + 비밀번호
- **세션**: JWT access token을 `httpOnly`, `Secure`, `SameSite=Lax` cookie로 저장 (30일 유효)
- **자동 로그인**: 쿠키 유효 시 재로그인 불필요
- **로그아웃**: 서버 응답에서 인증 쿠키 만료 처리

##### F-AUTH-03: 인증 미들웨어
- 모든 API 로그인 필수 (로그인/회원가입/중복 체크/헬스체크 제외)
- 프론트엔드 페이지 미인증 시 로그인 페이지로 리다이렉트
- Cookie 기반 인증이므로 프론트엔드는 `credentials: "include"`로 API 호출
- CSRF: 개인 전용 웹앱 MVP에서는 `SameSite=Lax`로 기본 방어, 외부 폼/서드파티 연동 추가 시 CSRF 토큰 도입

##### F-AUTH-04: 비밀번호 변경 (P1)
- 설정 페이지에서 현재 비밀번호 + 새 비밀번호

#### F-HOME: 홈 대시보드 (P0)

##### F-HOME-01: 홈 페이지
- **구성**:
  - 상단: 인사말 ("안녕하세요, 한한님")
  - 4개 메뉴 섹션 카드
    1. 데일리 브리핑: 오늘의 브리핑 요약 → 클릭 시 `/brief`
    2. 백테스트: "준비 중" → 클릭 시 `/backtest`
    3. 투자 현황: "준비 중" → 클릭 시 `/position`
    4. 투자 개념 정리: 등록 용어 수 + 최근 추가 → 클릭 시 `/glossary`

#### F-BRIEF: 데일리 브리핑 (P0)

##### F-BRIEF-01: 오늘의 브리핑
- **페이지**: `/brief`
- **표시**:
  - 생성 일시, 모델, 참고 기사 수
  - 한 줄 요약
  - 3개 섹션 (💻 개발/기술, 💰 투자/금융, 🤖 AI/ML)
  - 오늘의 키워드
- **액션**: 수동 재생성 버튼 (쿨다운 10분)

##### F-BRIEF-02: 아카이브
- **페이지**: `/brief/archive`
- **표시**: 최근 30일 브리핑 리스트 (날짜 + 한 줄 요약)
- **필터**: 날짜 범위, 키워드 검색
- **상세**: `/brief/archive/:date`
- **상세 API**: `GET /brief/date/:date` (`YYYY-MM-DD`)

##### F-BRIEF-03: 일일 브리핑 자동 생성
- **스케줄**: 매일 오전 6:30
- **동작**: 전일 18시~당일 6:30 수집 기사를 Claude 1회 호출로 통합 분석

#### F-BACKTEST / F-POSITION: Placeholder (P0)

##### F-BACKTEST-01 / F-POSITION-01
- 각각 `/backtest`, `/position`
- "준비 중" 안내 + 예정 기능 리스트

#### F-GLOSSARY: 투자 개념 정리 (P0)

##### F-GLOSSARY-01: 개념 목록 조회
- **페이지**: `/glossary`
- **표시**: 카테고리별 개념 목록
- **카테고리 분류**:
  - 기술적 분석 (이동평균선, RSI, MACD, 볼린저밴드 등)
  - 성과 지표 (샤프 비율, MDD, CAGR, 수익률 등)
  - 기본적 분석 (PER, PBR, ROE, EPS 등)
  - 주문/거래 (지정가, 시장가, 손절, 트레일링스탑 등)
  - 전략 (이평선 교차, 변동성 돌파, 모멘텀 등)
- **필터**: 카테고리 탭, 키워드 검색
- **정렬**: 카테고리별 가나다순

##### F-GLOSSARY-02: 개념 상세
- **페이지**: `/glossary/:id`
- **표시 정보**:
  - 용어 (한글명 + 영어명)
  - 카테고리
  - 한 줄 설명
  - 상세 설명 (Markdown)
  - 수식이 있는 경우 수식 표기
  - 예시 (선택)
  - 관련 개념 링크
- **예시**:
  ```
  📌 MDD (Maximum Drawdown, 최대 낙폭)
  카테고리: 성과 지표
  
  한 줄: 투자 기간 중 고점 대비 최대 하락폭
  
  상세: 포트폴리오가 고점에서 저점까지 
  떨어진 최대 비율을 의미합니다...
  
  수식: MDD = (고점 - 저점) / 고점 × 100
  
  예시: 1000만원 → 700만원이면 MDD = 30%
  
  관련 개념: CAGR, 샤프 비율, 변동성
  ```

##### F-GLOSSARY-03: 개념 추가/수정 (P1)
- 설정 또는 글로서리 페이지 내 관리 모드
- Markdown 에디터로 상세 설명 작성
- 관련 개념 링크 설정

##### F-GLOSSARY-04: 초기 데이터 시딩
- 자주 쓰는 투자 용어 20~30개 사전 등록
- 시드 데이터는 SQL 또는 JSON으로 관리

#### F-FEED: RSS 수집 (P0)

##### F-FEED-01: RSS 자동 수집
- 등록된 피드를 1시간마다 크롤링
- URL 기반 중복 제거

##### F-FEED-02: RSS 피드 관리 (P1)
- 설정 페이지에서 활성/비활성 토글

#### F-SETTINGS: 설정 (P1)

##### F-SETTINGS-01: 프로필
- 닉네임, 이메일, 핸드폰 변경
- 비밀번호 변경

##### F-SETTINGS-02: RSS 피드 관리

#### F-SYSTEM: 시스템 (P0)

##### F-SYSTEM-01: 헬스체크
- `/health`: DB, Claude API, 기본 상태

---

## 5. 화면 설계

### 5.1 사이트맵

```
ysj.brief
│
├── 🔐 /login
├── 🔐 /signup
│
├── 🏠 /                     (홈 대시보드)
│
├── 📰 /brief                (데일리 브리핑)
│   ├── /brief               (오늘의 브리핑)
│   └── /brief/archive       (아카이브)
│       └── /brief/archive/:date
│
├── 📊 /backtest             (Placeholder)
├── 💼 /position             (Placeholder)
│
├── 📖 /glossary             (투자 개념 정리)
│   └── /glossary/:id        (개념 상세)
│
└── ⚙️ /settings
    ├── /settings/profile
    └── /settings/feeds
```

### 5.2 전체 레이아웃

#### Desktop
```
┌──────┬────────────────────────────────────────────┐
│      │  ysj.brief                    🔔 한한  ⚙️  │
│      ├────────────────────────────────────────────┤
│  🏠  │                                            │
│  📰  │                                            │
│  📊  │        [현재 선택된 메뉴 콘텐츠]            │
│  💼  │                                            │
│  📖  │                                            │
│  ⚙️  │                                            │
│      │                                            │
│ 로그 │                                            │
│ 아웃 │                                            │
└──────┴────────────────────────────────────────────┘

사이드바 아이콘:
🏠 홈 / 📰 데일리 브리핑 / 📊 백테스트 / 💼 투자 현황 / 📖 투자 개념 정리 / ⚙️ 설정
```

#### Mobile
```
┌──────────────────────────────────┐
│  ≡  ysj.brief          🔔 👤     │
├──────────────────────────────────┤
│                                  │
│      [선택된 메뉴 콘텐츠]         │
│                                  │
├──────────────────────────────────┤
│ [🏠] [📰] [📊] [💼] [📖] [⚙️]    │
└──────────────────────────────────┘
```

### 5.3 주요 페이지 와이어프레임

#### 5.3.1 회원가입 (/signup)

```
┌──────────────────────────────────┐
│     ← 회원가입                    │
├──────────────────────────────────┤
│                                  │
│  아이디 *                         │
│  [han                       ]    │
│  ✓ 사용 가능                     │
│                                  │
│  비밀번호 *                       │
│  [••••••••                  ]    │
│  ✓ 8자 이상                      │
│                                  │
│  비밀번호 확인 *                  │
│  [••••••••                  ]    │
│  ✓ 일치                         │
│                                  │
│  닉네임 *                         │
│  [한한                      ]    │
│                                  │
│  핸드폰 번호 *                    │
│  [010-1234-5678             ]    │
│                                  │
│  이메일 *                         │
│  [han@example.com           ]    │
│                                  │
│          [  가입하기  ]          │
│                                  │
│  이미 계정이 있으신가요?          │
│          [로그인 →]              │
└──────────────────────────────────┘
```

#### 5.3.2 로그인 (/login)

```
┌──────────────────────────────────┐
│                                  │
│          📰 ysj.brief            │
│     개인 투자 대시보드            │
│                                  │
│  ┌────────────────────────────┐  │
│  │ 아이디                      │  │
│  │ [                        ] │  │
│  │                             │  │
│  │ 비밀번호                    │  │
│  │ [                        ] │  │
│  │                             │  │
│  │     [  로그인  ]            │  │
│  │                             │  │
│  │   계정이 없으신가요?        │  │
│  │     [회원가입 →]            │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

#### 5.3.3 홈 대시보드 (/)

```
┌─────────────────────────────────────────────┐
│  ysj.brief                    🔔 한한  ⚙️    │
├─────────────────────────────────────────────┤
│                                             │
│   안녕하세요, 한한님 👋                       │
│   2026년 4월 20일 월요일                      │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 📰 데일리 브리핑              [→]   │    │
│  │                                     │    │
│  │ 오늘의 브리핑 · 07:30 생성           │    │
│  │                                     │    │
│  │ "OpenAI 신모델 공개와 반도체 강세"  │    │
│  │                                     │    │
│  │ • 개발: React 19 정식 출시          │    │
│  │ • 투자: 코스피 연고점 갱신          │    │
│  │ • AI: Claude Opus 4.7 발표          │    │
│  │                                     │    │
│  │ [전체 브리핑 보기 →]                │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 📊 백테스트                         │    │
│  │                                     │    │
│  │ 🚧 준비 중                           │    │
│  │ 투자 전략을 과거 데이터로 검증하는   │    │
│  │ 기능을 준비하고 있습니다.            │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 💼 투자 현황                         │    │
│  │                                     │    │
│  │ 🚧 준비 중                           │    │
│  │ 포트폴리오 조회와 손익 추적 기능을  │    │
│  │ 준비하고 있습니다.                   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 📖 투자 개념 정리              [→]  │    │
│  │                                     │    │
│  │ 등록된 개념 32개                     │    │
│  │ 최근 추가: 샤프 비율, 트레일링스탑  │    │
│  │                                     │    │
│  │ [개념 사전 보기 →]                  │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

#### 5.3.4 데일리 브리핑 - 오늘 (/brief)

```
┌─────────────────────────────────────────────┐
│  ← 데일리 브리핑                             │
│                                             │
│  [오늘] [아카이브]                  🔄       │
├─────────────────────────────────────────────┤
│                                             │
│  # 🌅 2026년 4월 20일 브리핑                │
│                                             │
│  ## 한 줄 요약                               │
│  OpenAI와 Anthropic의 신모델 경쟁이 치열해  │
│  지는 가운데, 국내 반도체 섹터가 강세...    │
│                                             │
│  ## 💻 개발/기술                             │
│  이번 주 프론트엔드 생태계는 React 19의...  │
│                                             │
│  **주목할 기사**                             │
│  • [React 19 정식 출시](링크)                │
│  • [Next.js 15.1 릴리즈](링크)               │
│                                             │
│  ## 💰 투자/금융                             │
│  국내 증시는 외국인 매수세 유입으로...       │
│                                             │
│  **주목할 기사**                             │
│  • [삼성전자 4분기 실적](링크)               │
│                                             │
│  ## 🤖 AI/ML                                 │
│  AI 모델 성능 경쟁이 가속화되는 가운데...   │
│                                             │
│  **주목할 기사**                             │
│  • [Claude Opus 4.7 출시](링크)              │
│                                             │
│  ## 📌 오늘의 키워드                         │
│  [React 19] [Claude 4.7] [삼성전자 실적]    │
│                                             │
├─────────────────────────────────────────────┤
│  📊 기반 기사 47건 · Haiku 4.5로 생성        │
└─────────────────────────────────────────────┘
```

#### 5.3.5 브리핑 아카이브 (/brief/archive)

```
┌─────────────────────────────────────────────┐
│  ← 데일리 브리핑                             │
│                                             │
│  [오늘] [아카이브]                           │
├─────────────────────────────────────────────┤
│                                             │
│  🔍 [키워드 검색...              ]          │
│  기간: [최근 30일 ▼]                         │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 2026-04-20 (월)                     │    │
│  │ OpenAI 신모델 공개와 반도체 강세     │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ 2026-04-19 (일)                     │    │
│  │ 주말 기술 트렌드 요약                │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │ 2026-04-18 (금)                     │    │
│  │ 미 FOMC 앞두고 시장 관망             │    │
│  └─────────────────────────────────────┘    │
│  ...                                        │
└─────────────────────────────────────────────┘
```

#### 5.3.6 백테스트 Placeholder (/backtest)

```
┌─────────────────────────────────────────────┐
│  ← 백테스트                                  │
├─────────────────────────────────────────────┤
│                                             │
│            🚧                                │
│                                             │
│       백테스트는 준비 중입니다                │
│                                             │
│   향후 아래 기능이 제공될 예정입니다:         │
│                                             │
│   📈 과거 데이터로 투자 전략 검증            │
│   📊 수익률, MDD, 샤프 비율 등 지표 제공     │
│   🔄 여러 전략 비교                          │
│   💾 결과 저장 및 공유                       │
│                                             │
└─────────────────────────────────────────────┘
```

#### 5.3.7 투자 개념 정리 (/glossary)

```
┌─────────────────────────────────────────────┐
│  ← 투자 개념 정리                            │
├─────────────────────────────────────────────┤
│                                             │
│  🔍 [용어 검색...                 ]         │
│                                             │
│  [전체] [기술적분석] [성과지표] [기본적분석] │
│  [주문/거래] [전략]                          │
├─────────────────────────────────────────────┤
│                                             │
│  📐 기술적 분석                              │
│  ┌─────────────────────────────────────┐    │
│  │ 📌 이동평균선 (Moving Average)      │    │
│  │ 일정 기간 주가의 평균을 이은 선     │    │
│  ├─────────────────────────────────────┤    │
│  │ 📌 RSI (Relative Strength Index)    │    │
│  │ 과매수/과매도를 판단하는 지표       │    │
│  ├─────────────────────────────────────┤    │
│  │ 📌 MACD                             │    │
│  │ 이동평균의 수렴과 발산을 나타내는...│    │
│  └─────────────────────────────────────┘    │
│                                             │
│  📊 성과 지표                                │
│  ┌─────────────────────────────────────┐    │
│  │ 📌 MDD (Maximum Drawdown)           │    │
│  │ 고점 대비 최대 하락폭              │    │
│  ├─────────────────────────────────────┤    │
│  │ 📌 샤프 비율 (Sharpe Ratio)         │    │
│  │ 위험 대비 초과 수익률              │    │
│  └─────────────────────────────────────┘    │
│  ...                                        │
└─────────────────────────────────────────────┘
```

#### 5.3.8 개념 상세 (/glossary/:id)

```
┌─────────────────────────────────────────────┐
│  ← 투자 개념 정리                            │
├─────────────────────────────────────────────┤
│                                             │
│  📌 MDD (Maximum Drawdown)                  │
│  카테고리: 성과 지표                         │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  ## 한 줄 설명                               │
│  투자 기간 중 고점 대비 최대 하락폭          │
│                                             │
│  ## 상세 설명                                │
│  포트폴리오 가치가 직전 고점에서 저점까지    │
│  떨어진 최대 비율을 의미합니다.              │
│  MDD가 작을수록 안정적인 전략으로 평가됩니다.│
│                                             │
│  ## 수식                                     │
│  MDD = (고점 - 저점) / 고점 × 100           │
│                                             │
│  ## 예시                                     │
│  투자금 1,000만원 → 최저 700만원             │
│  MDD = (1000 - 700) / 1000 × 100 = 30%     │
│                                             │
│  ## 관련 개념                                │
│  [CAGR] [샤프 비율] [변동성]                 │
│                                             │
│  ─────────────────────────────────────────  │
│  ✏️ 수정                                    │
└─────────────────────────────────────────────┘
```

### 5.4 디자인 원칙

- **모바일 퍼스트**: 출근길 모바일 사용이 주 시나리오
- **다크 모드 기본**: 눈 피로 감소
- **한국어 최적화**: Pretendard 폰트
- **카테고리 색상** (브리핑 내부):
  - 💻 개발: 보라 계열
  - 💰 투자: 초록 계열
  - 🤖 AI: 청록 계열

---

## 6. 시스템 아키텍처

### 6.1 전체 구조

```
┌────────────────────────────────────────┐
│           사용자 (모바일/PC)            │
└───────────────┬────────────────────────┘
                │ HTTPS
                ▼
┌────────────────────────────────────────┐
│      Nginx (Reverse Proxy + SSL)        │
└───────┬──────────────────┬──────────────┘
        │                  │
        ▼                  ▼
 ┌─────────────┐    ┌──────────────┐
 │  Next.js    │REST│   FastAPI    │
 │  Frontend   │◄──►│   API Server │
 │  (3000)     │    │   (8000)     │
 └─────────────┘    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌──────────┐       ┌──────────┐      ┌──────────┐
  │PostgreSQL│       │RSS Feeds │      │Claude API│
  │          │       │(external)│      │ (Haiku)  │
  └──────────┘       └──────────┘      └──────────┘
        ▲
        │
  ┌─────┴────────────────────────┐
  │  Worker Container             │
  │  APScheduler 단일 실행 주체    │
  │  - RSS 수집 (1h)              │
  │  - 일일 브리핑 생성 (하루 1회) │
  │  - DB advisory lock으로 중복 방지│
  └───────────────────────────────┘
```

> 운영 원칙: API 서버는 요청 처리만 담당하고, 정기 작업은 별도 `worker` 컨테이너에서만 실행한다. 개발/운영 환경 모두 스케줄러 인스턴스는 1개를 원칙으로 하며, 재시작/중복 실행에 대비해 작업 시작 시 PostgreSQL advisory lock을 획득한다.

### 6.2 기술 스택

#### 프론트엔드
| 기술 | 용도 |
|------|------|
| Next.js 14 (App Router) | 프레임워크 |
| TypeScript | 타입 안정성 |
| TailwindCSS | 스타일링 |
| TanStack Query | 서버 상태 |
| Zustand | 클라이언트 상태 |
| react-markdown | Markdown 렌더링 |
| date-fns | 날짜 처리 |
| Pretendard | 한국어 폰트 |
| React Hook Form + Zod | 폼 + 검증 |

#### 백엔드
| 기술 | 용도 |
|------|------|
| Python 3.12 | 언어 |
| FastAPI 0.110+ | 웹 프레임워크 |
| SQLAlchemy 2 | ORM |
| Alembic | DB 마이그레이션 |
| Pydantic 2 | 검증 |
| APScheduler | 스케줄러 |
| feedparser | RSS 파싱 |
| anthropic | Claude SDK |
| httpx | HTTP 클라이언트 |
| python-jose | JWT |
| passlib[bcrypt] | 비밀번호 해싱 |

#### 인프라
- Contabo VPS (Ubuntu)
- PostgreSQL 15
- Docker + Docker Compose
- Nginx + Let's Encrypt SSL
- GitHub Actions (CI/CD)

### 6.3 디렉토리 구조

```
ysj-brief/
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx         # 사이드바 포함
│   │   │   ├── page.tsx           # 홈
│   │   │   ├── brief/
│   │   │   │   ├── page.tsx       # 오늘
│   │   │   │   └── archive/
│   │   │   ├── backtest/page.tsx  # Placeholder
│   │   │   ├── position/page.tsx  # Placeholder
│   │   │   ├── glossary/
│   │   │   │   ├── page.tsx       # 개념 목록
│   │   │   │   └── [id]/page.tsx  # 개념 상세
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/                # 사이드바, 헤더
│   │   ├── brief/
│   │   └── dashboard/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── constants.ts
│   ├── hooks/
│   └── types/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   │
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── brief.py
│   │   │   ├── glossary.py
│   │   │   ├── feeds.py
│   │   │   └── health.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── news.py
│   │   │   ├── briefing.py
│   │   │   ├── glossary.py
│   │   │   └── feed.py
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── rss_collector.py
│   │   │   ├── briefing_generator.py
│   │   │   └── claude_client.py
│   │   │
│   │   └── scheduler/
│   │       ├── jobs.py
│   │       └── scheduler.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/nginx.conf
├── .env.example
├── README.md
└── PRD.md
```

---

## 7. 데이터 모델

### 7.1 ERD

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id       (PK)   │
│ username (UQ)   │
│ password_hash   │
│ display_name    │
│ phone    (UQ)   │
│ email    (UQ)   │
│ last_login_at   │
│ created_at      │
│ updated_at      │
└─────────────────┘

┌──────────────┐       ┌──────────────────┐
│  rss_feeds   │       │      news        │
├──────────────┤       ├──────────────────┤
│ id     (PK)  │       │ id         (PK)  │
│ name         │       │ title            │
│ url    (UQ)  │───┐   │ url        (UQ)  │
│ category     │   └──►│ source_feed_id   │
│ language     │ 1:N   │ source_name      │
│ is_active    │       │ category         │
│ last_fetched │       │ published_at     │
└──────────────┘       │ content          │
                       │ content_excerpt  │
                       │ raw_data (jsonb) │
                       │ collected_at     │
                       └──────────────────┘

┌──────────────────────┐
│     briefings        │
├──────────────────────┤
│ id             (PK)  │
│ briefing_date        │
│ briefing_type        │
│ title                │
│ one_liner            │
│ content_markdown     │
│ content_sections     │  (jsonb)
│ highlighted_news_ids │  (int[])
│ keywords             │  (text[])
│ source_article_count │
│ model_used           │
│ tokens_used          │
│ generated_at         │
└──────────────────────┘

┌──────────────────────────┐
│     glossary_categories  │
├──────────────────────────┤
│ id             (PK)      │
│ name                     │  (기술적 분석, 성과 지표...)
│ slug                     │  (technical, performance...)
│ icon                     │
│ sort_order               │
└──────────────────────────┘
          │
          │ 1:N
          ▼
┌──────────────────────────┐
│     glossary_terms       │
├──────────────────────────┤
│ id             (PK)      │
│ category_id    (FK)      │
│ term_ko                  │  (이동평균선)
│ term_en                  │  (Moving Average)
│ short_desc               │  (한 줄 설명)
│ detail_markdown          │  (상세 설명)
│ formula                  │  (수식, 선택)
│ example                  │  (예시, 선택)
│ related_term_ids         │  (int[])
│ created_at               │
│ updated_at               │
└──────────────────────────┘
```

### 7.2 테이블 DDL

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_username CHECK (username ~ '^[a-zA-Z0-9_]{4,20}$'),
    CONSTRAINT chk_phone CHECK (phone ~ '^[0-9]{10,11}$'),
    CONSTRAINT chk_email CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$')
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### rss_feeds
```sql
CREATE TABLE rss_feeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('dev', 'investment', 'ai')),
    language VARCHAR(10) NOT NULL DEFAULT 'ko' CHECK (language IN ('ko', 'en')),
    is_active BOOLEAN DEFAULT TRUE,
    last_fetched_at TIMESTAMP,
    last_fetched_status VARCHAR(20),
    last_error TEXT,
    fetch_interval_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feeds_active ON rss_feeds(is_active, category);
```

#### news
```sql
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(1000) NOT NULL,
    url VARCHAR(1500) UNIQUE NOT NULL,
    source_feed_id INTEGER REFERENCES rss_feeds(id),
    source_name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('dev', 'investment', 'ai')),
    author VARCHAR(200),
    published_at TIMESTAMP,
    content TEXT,
    content_excerpt TEXT,
    raw_data JSONB,
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_news_published ON news(published_at DESC);
CREATE INDEX idx_news_category_date ON news(category, published_at DESC);
CREATE INDEX idx_news_title_search ON news USING gin(to_tsvector('simple', title));
```

#### briefings
```sql
CREATE TABLE briefings (
    id SERIAL PRIMARY KEY,
    briefing_date DATE NOT NULL,
    briefing_type VARCHAR(30) NOT NULL CHECK (
        briefing_type IN ('daily_morning', 'manual')
    ),
    title VARCHAR(200),
    one_liner TEXT,
    content_markdown TEXT NOT NULL,
    content_sections JSONB,
    highlighted_news_ids INTEGER[],
    keywords TEXT[],
    source_article_count INTEGER,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    generated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_briefings_date_type UNIQUE (briefing_date, briefing_type)
);

CREATE INDEX idx_briefings_date_type ON briefings(briefing_date DESC, briefing_type);
CREATE INDEX idx_briefings_keywords ON briefings USING gin(keywords);
```

#### glossary_categories
```sql
CREATE TABLE glossary_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    icon VARCHAR(10),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### glossary_terms
```sql
CREATE TABLE glossary_terms (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES glossary_categories(id) NOT NULL,
    term_ko VARCHAR(100) NOT NULL,
    term_en VARCHAR(100),
    short_desc TEXT NOT NULL,
    detail_markdown TEXT,
    formula TEXT,
    example TEXT,
    related_term_ids INTEGER[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_glossary_category ON glossary_terms(category_id);
CREATE INDEX idx_glossary_term_search ON glossary_terms
    USING gin(to_tsvector('simple', term_ko || ' ' || COALESCE(term_en, '')));
```

### 7.3 초기 시드 데이터

```sql
INSERT INTO rss_feeds (name, url, category, language) VALUES
  ('GeekNews', 'https://news.hada.io/rss/news', 'dev', 'ko'),
  ('토스 기술 블로그', 'https://toss.tech/rss.xml', 'dev', 'ko'),
  ('카카오 기술 블로그', 'https://tech.kakao.com/feed/', 'dev', 'ko'),
  ('우아한형제들 기술 블로그', 'https://techblog.woowahan.com/feed/', 'dev', 'ko'),
  ('NHN Cloud Meetup', 'https://meetup.nhncloud.com/rss', 'dev', 'ko'),
  ('Dev.to', 'https://dev.to/feed', 'dev', 'en'),
  ('Hacker News', 'https://hnrss.org/frontpage', 'dev', 'en'),
  ('React Status', 'https://react.statuscode.com/rss', 'dev', 'en'),
  ('JavaScript Weekly', 'https://javascriptweekly.com/rss', 'dev', 'en'),
  ('매일경제 금융', 'https://www.mk.co.kr/rss/30100041/', 'investment', 'ko'),
  ('Google News 국내 증시', 'https://news.google.com/rss/search?q=%EA%B5%AD%EB%82%B4%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko', 'investment', 'ko'),
  ('Investing.com Stock Market News', 'https://www.investing.com/rss/news_25.rss', 'investment', 'en'),
  ('MarketWatch Top Stories', 'https://feeds.marketwatch.com/marketwatch/topstories/', 'investment', 'en'),
  ('The Motley Fool', 'https://www.fool.com/feeds/index.aspx', 'investment', 'en'),
  ('OpenAI Blog', 'https://openai.com/blog/rss.xml', 'ai', 'en'),
  ('Hugging Face Blog', 'https://huggingface.co/blog/feed.xml', 'ai', 'en'),
  ('Google AI Blog', 'https://blog.google/technology/ai/rss/', 'ai', 'en'),
  ('AI News', 'https://artificialintelligence-news.com/feed/', 'ai', 'en');
```

> 피드 검증 기준: Phase 1 시작 시 `User-Agent: ysj.brief feed validator`를 포함해 HTTP 200 응답과 XML/RSS 파싱 성공을 확인한다. 실패 피드는 시드에서 제외하거나 `is_active=false`로 등록한다.

#### 투자 개념 시드 데이터
```sql
-- 카테고리
INSERT INTO glossary_categories (name, slug, icon, sort_order) VALUES
  ('기술적 분석', 'technical', '📐', 1),
  ('성과 지표', 'performance', '📊', 2),
  ('기본적 분석', 'fundamental', '📋', 3),
  ('주문/거래', 'trading', '💹', 4),
  ('전략', 'strategy', '🎯', 5);

-- 핵심 용어 (예시, 실제 시드는 더 많이 추가)
INSERT INTO glossary_terms (category_id, term_ko, term_en, short_desc, detail_markdown, formula, example) VALUES
  (1, '이동평균선', 'Moving Average (MA)', '일정 기간 주가의 평균을 이은 선',
   '이동평균선은 일정 기간 동안의 주가 평균을 연결한 선입니다. 단기(5일, 20일)와 장기(60일, 120일)로 나뉘며, 추세 판단의 기본 도구입니다.\n\n단순이동평균(SMA)은 기간 내 종가를 단순 평균한 것이고, 지수이동평균(EMA)은 최근 가격에 더 높은 가중치를 줍니다.',
   'SMA = (P1 + P2 + ... + Pn) / n', '20일 이동평균: 최근 20일 종가의 합 ÷ 20'),
  (1, 'RSI', 'Relative Strength Index', '과매수/과매도를 판단하는 모멘텀 지표',
   'RSI는 일정 기간 동안의 상승폭과 하락폭을 비교하여 0~100 사이의 값으로 나타냅니다.\n\n일반적으로 70 이상이면 과매수(매도 신호), 30 이하면 과매도(매수 신호)로 해석합니다. 기본 기간은 14일입니다.',
   'RSI = 100 - (100 / (1 + RS))\nRS = 평균 상승폭 / 평균 하락폭', 'RSI 75: 과매수 구간 → 조정 가능성'),
  (1, 'MACD', 'Moving Average Convergence Divergence', '이동평균의 수렴과 발산을 나타내는 추세 지표',
   'MACD는 단기 지수이동평균(12일)에서 장기 지수이동평균(26일)을 뺀 값입니다.\n\nMACD선이 시그널선(MACD의 9일 EMA)을 상향 돌파하면 매수 신호, 하향 돌파하면 매도 신호로 해석합니다.',
   'MACD = EMA(12) - EMA(26)\nSignal = EMA(MACD, 9)', NULL),
  (1, '볼린저 밴드', 'Bollinger Bands', '이동평균 주위에 표준편차 밴드를 그린 변동성 지표',
   '20일 이동평균을 중심으로 위아래에 표준편차의 2배를 더하고 뺀 밴드입니다.\n\n밴드 폭이 좁아지면 변동성 축소(횡보), 넓어지면 변동성 확대를 의미합니다. 가격이 상단 밴드를 터치하면 과매수, 하단이면 과매도로 볼 수 있습니다.',
   '상단 = SMA(20) + 2σ\n하단 = SMA(20) - 2σ', NULL),
  (2, 'MDD', 'Maximum Drawdown', '투자 기간 중 고점 대비 최대 하락폭',
   '포트폴리오 가치가 직전 고점에서 저점까지 떨어진 최대 비율입니다.\n\nMDD가 작을수록 안정적인 전략으로 평가됩니다. 예를 들어 MDD 10%인 전략은 MDD 50%인 전략보다 리스크가 작습니다.\n\n백테스트 결과를 평가할 때 수익률만큼이나 중요한 지표입니다.',
   'MDD = (고점 - 저점) / 고점 × 100', '1000만원 → 700만원: MDD = 30%'),
  (2, '샤프 비율', 'Sharpe Ratio', '위험 대비 초과 수익률을 나타내는 지표',
   '무위험 수익률(예: 국채 금리) 대비 얼마나 효율적으로 수익을 냈는지 측정합니다.\n\n1 이상이면 양호, 2 이상이면 우수, 3 이상이면 매우 우수로 평가합니다.\n\n같은 수익률이라도 변동성이 작을수록 샤프 비율이 높아집니다.',
   'Sharpe = (Rp - Rf) / σp\nRp: 포트폴리오 수익률\nRf: 무위험 수익률\nσp: 포트폴리오 표준편차', '연 수익 15%, 무위험 3%, 표준편차 10% → 샤프 = 1.2'),
  (2, 'CAGR', 'Compound Annual Growth Rate', '연평균 복합 성장률',
   '투자 기간 동안의 연평균 성장률입니다. 단순 평균이 아닌 복리 기준으로 계산합니다.\n\n장기 투자 성과를 비교할 때 유용합니다.',
   'CAGR = (최종값/초기값)^(1/n) - 1\nn: 투자 기간(년)', '100만원 → 3년 후 130만원: CAGR = 약 9.1%'),
  (3, 'PER', 'Price to Earnings Ratio', '주가수익비율 (주가 ÷ 주당순이익)',
   '현재 주가가 1주당 순이익의 몇 배인지를 나타냅니다.\n\nPER이 낮으면 이익 대비 저평가, 높으면 고평가로 해석할 수 있지만, 업종별로 적정 PER이 다르므로 동종 업계 비교가 중요합니다.',
   'PER = 주가 / EPS', 'PER 15: 현재 이익 수준으로 투자금 회수에 15년'),
  (4, '손절', 'Stop Loss', '손실을 제한하기 위해 미리 정한 가격에 매도하는 것',
   '매수 후 주가가 일정 비율(예: -5%) 하락하면 자동으로 매도하는 전략입니다.\n\n감정적 판단을 배제하고 리스크를 관리하는 핵심 도구입니다.',
   NULL, '매수가 10만원, 손절선 -5% → 9.5만원 도달 시 매도'),
  (4, '트레일링 스탑', 'Trailing Stop', '고점 대비 일정 비율 하락 시 매도하는 동적 손절',
   '주가가 올라갈 때 손절선도 함께 올라가고, 내려갈 때는 손절선이 유지됩니다.\n\n상승 추세에서 수익을 최대화하면서 하락 시 이익을 보전할 수 있습니다.',
   NULL, '고점 10만원, 트레일링 3% → 9.7만원 이하로 떨어지면 매도'),
  (5, '이평선 교차 전략', 'Moving Average Crossover', '단기/장기 이동평균의 교차로 매매 시점을 판단하는 전략',
   '단기 이동평균이 장기 이동평균을 상향 돌파하면 골든크로스(매수), 하향 돌파하면 데드크로스(매도)로 판단합니다.\n\n가장 기본적인 추세 추종 전략입니다.',
   NULL, '5일선이 20일선을 상향 돌파 → 골든크로스 → 매수 신호'),
  (5, '변동성 돌파 전략', 'Volatility Breakout', '전일 변동폭의 일정 비율을 돌파하면 매수하는 단기 전략',
   '래리 윌리엄스가 개발한 전략으로, 당일 시가 + (전일 고가-저가) × k 를 돌파하면 매수합니다.\n\nk값은 보통 0.5를 사용하며, 당일 장마감 시 매도합니다.',
   '매수 기준 = 당일 시가 + (전일 고가 - 전일 저가) × k', 'k=0.5, 전일 변동폭 1000원, 시가 50000원 → 50500원 돌파 시 매수');
```

---

## 8. API 명세

### 8.1 공통 사항
- **Base URL**: `https://brief.ysj.example.com/api/v1`
- **응답 형식**: JSON
- **인증**: JWT `httpOnly` cookie (로그인/가입/중복 체크/헬스체크 제외 필수)
- **프론트 호출**: 브라우저 API 요청은 cookie 전송을 위해 `credentials: "include"` 사용
- **에러 응답**:
  ```json
  { "error": { "code": "...", "message": "..." } }
  ```

### 8.2 엔드포인트

#### 인증
| Method | Path | 설명 |
|--------|------|------|
| POST | `/auth/signup` | 회원가입, 성공 시 인증 쿠키 설정 |
| POST | `/auth/login` | 로그인, 성공 시 인증 쿠키 설정 |
| POST | `/auth/logout` | 로그아웃, 인증 쿠키 만료 |
| GET | `/auth/me` | 내 정보 |
| POST | `/auth/check-username` | 아이디 중복 체크 (Public) |
| POST | `/auth/check-email` | 이메일 중복 체크 (Public) |
| POST | `/auth/check-phone` | 핸드폰 중복 체크 (Public) |

#### 홈
| Method | Path | 설명 |
|--------|------|------|
| GET | `/dashboard/summary` | 4개 메뉴 요약 |

#### 데일리 브리핑
| Method | Path | 설명 |
|--------|------|------|
| GET | `/brief/today` | 오늘 브리핑 |
| GET | `/brief/archive` | 아카이브 리스트 |
| GET | `/brief/date/:date` | 날짜별 브리핑 (`YYYY-MM-DD`) |
| GET | `/brief/:id` | ID 기준 특정 브리핑 |
| GET | `/brief/search` | 키워드 검색 |
| POST | `/brief/regenerate` | 오늘 브리핑 수동 재생성, `daily_morning` row upsert |

#### RSS 피드
| Method | Path | 설명 |
|--------|------|------|
| GET | `/feeds` | 목록 |
| PATCH | `/feeds/:id` | 활성/비활성 |
| POST | `/feeds` | 추가 |
| DELETE | `/feeds/:id` | 삭제 |

#### 투자 개념 정리
| Method | Path | 설명 |
|--------|------|------|
| GET | `/glossary` | 전체 목록 (카테고리별 그룹) |
| GET | `/glossary/categories` | 카테고리 목록 |
| GET | `/glossary/:id` | 개념 상세 |
| GET | `/glossary/search` | 키워드 검색 |
| POST | `/glossary` | 개념 추가 (P1) |
| PATCH | `/glossary/:id` | 개념 수정 (P1) |
| DELETE | `/glossary/:id` | 개념 삭제 (P1) |

#### 시스템
| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |

### 8.3 주요 스키마

#### POST /auth/signup
```http
Request:
{
  "username": "han",
  "password": "mysecret123",
  "password_confirm": "mysecret123",
  "display_name": "한한",
  "phone": "01012345678",
  "email": "han@example.com"
}

Response 201:
Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000

{
  "user": {
    "id": 1,
    "username": "han",
    "display_name": "한한",
    "email": "han@example.com",
    "created_at": "2026-04-20T10:00:00+09:00"
  }
}

Response 400:
{
  "error": {
    "code": "DUPLICATE_USERNAME",
    "message": "이미 사용 중인 아이디입니다"
  }
}
```

#### GET /dashboard/summary
```json
Response 200:
{
  "today_briefing": {
    "id": 42,
    "date": "2026-04-20",
    "title": "OpenAI 신모델 공개와 삼성전자 실적 호조",
    "one_liner": "OpenAI와 Anthropic의 신모델 경쟁 치열, 국내 반도체 강세",
    "section_highlights": {
      "dev": "React 19 정식 출시",
      "investment": "코스피 연고점 갱신",
      "ai": "Claude Opus 4.7 발표"
    },
    "generated_at": "2026-04-20T07:30:00+09:00"
  },
  "backtest": { "status": "coming_soon" },
  "position": { "status": "coming_soon" },
  "glossary": {
    "total_terms": 12,
    "recent_added": ["샤프 비율", "트레일링 스탑"]
  }
}
```

#### GET /brief/today
```json
Response 200:
{
  "id": 42,
  "briefing_date": "2026-04-20",
  "briefing_type": "daily_morning",
  "title": "OpenAI 신모델 공개와 삼성전자 실적 호조",
  "one_liner": "OpenAI와 Anthropic의 신모델 경쟁이...",
  "content_markdown": "# 🌅 2026년 4월 20일 브리핑\n...",
  "content_sections": {
    "dev": {
      "comment": "이번 주 프론트엔드 생태계는...",
      "highlights": [
        { "title": "React 19 정식 출시", "url": "...", "source": "GeekNews" }
      ]
    },
    "investment": { "..." },
    "ai": { "..." }
  },
  "keywords": ["React 19", "Claude 4.7", "삼성전자 실적"],
  "source_article_count": 47,
  "model_used": "claude-haiku-4-5",
  "generated_at": "2026-04-20T07:30:00+09:00"
}
```

---

## 9. 외부 API 연동 및 비용 전략

### 9.1 비용 절감 전략 (핵심)

**목표**: Claude API 월 비용 **$5 이하**

| 전략 | 설명 |
|------|------|
| **하루 1회 호출** | 기사별 분석 없이, 일일 브리핑 생성 시 Claude 1회만 호출 |
| **Haiku 우선** | `claude-haiku-4-5` 사용 (가장 저렴) |
| **입력 최소화** | 제목 + RSS excerpt만 전달 (본문 전체 X) |
| **데이터 먼저** | RSS 수집 3~4일 돌려서 일 수집량 파악 후 프롬프트 최적화 |

#### 예상 비용 (Haiku 기준)
```
일일 브리핑 1회:
- 입력: ~10k tokens (기사 50건 × 제목+excerpt 200토큰)
- 출력: ~2k tokens
- 월 30회

월 예상: $1~3
```

### 9.2 Claude API

#### 사용 모델
- **기본**: `claude-haiku-4-5`
- **(향후)**: 품질 부족 시 `claude-sonnet-4-6` 테스트

#### 일일 브리핑 프롬프트

```
You are writing a morning briefing in Korean for a developer-investor.

Below are articles collected since yesterday evening.
Each article: category (dev/investment/ai), title, source, published_at, excerpt.

Articles:
{articles_json}

Write the briefing in Korean Markdown:

# 🌅 {YYYY년 M월 D일} 브리핑

## 한 줄 요약
{핵심 한 문장, 50자 이내}

## 💻 개발/기술
{3~5줄 종합 코멘트}

**주목할 기사**
- [{제목}]({url}): {1~2줄 설명}
- ...

## 💰 투자/금융
(같은 구조)

## 🤖 AI/ML
(같은 구조)

## 📌 오늘의 키워드
{5~8개 키워드, 쉼표}

Rules:
- 각 섹션 중요도 높은 것 3~5건
- 사실 위주, 추측 배제
- 차분한 존댓말
- 총 800자 이내
- URL은 입력 데이터 그대로
```

### 9.3 RSS 피드

18개 피드 ([7.3 초기 시드 데이터](#73-초기-시드-데이터) 참조)

**수집 전략**: 병렬 fetch (asyncio + httpx), `User-Agent` 지정, 타임아웃 10초, 실패 시 다음 주기 재시도

---

## 10. 스케줄 작업

### 10.1 작업 일정표

| 주기 | 시간 | 작업 | 설명 |
|------|------|------|------|
| 1시간마다 | 매시 5분 | `collect_rss_feeds` | 모든 RSS 수집 |
| 매일 | 06:30 | `generate_daily_briefing` | 일일 브리핑 (Claude 1회) |
| 매일 | 03:00 | `cleanup_old_data` | 6개월+ raw_data 정리 |

> 권장: Phase 1에서 RSS 수집만 3~4일 돌려 일일 수집량 파악 후, 브리핑 생성 활성화.

### 10.2 실패 처리

| 작업 | 실패 시 |
|------|---------|
| RSS 수집 | 다음 주기 재시도, 피드별 에러 로깅 |
| 일일 브리핑 | 1시간 후 재시도 (최대 3회), 실패 시 관리자 로그 |

### 10.3 중복 실행 방지
- 정기 작업은 `worker` 컨테이너의 APScheduler에서만 실행
- 각 작업 시작 시 PostgreSQL advisory lock 획득
- lock 획득 실패 시 같은 작업이 이미 실행 중인 것으로 보고 즉시 종료
- `generate_daily_briefing`은 `(briefing_date, briefing_type)` unique key 기준 upsert

---

## 11. 비기능 요구사항

### 11.1 성능
- 대시보드 FCP < 1.5s
- API p95 < 500ms

### 11.2 보안
- HTTPS (Let's Encrypt)
- JWT (httpOnly cookie, 30일)
- Cookie 옵션: `HttpOnly`, `Secure`, `SameSite=Lax`, `Max-Age=30일`
- bcrypt (rounds ≥ 12)
- SQLAlchemy ORM
- Pydantic 입력 검증
- Rate Limiting (로그인 10분당 5회)
- CORS: 프론트 도메인만
- 인증 cookie를 쓰므로 CORS는 credentials 허용 도메인을 명시하고 wildcard 금지

### 11.3 데이터 관리
- `news.raw_data`: 3개월 후 NULL
- `briefings`: 영구 보관
- DB 일일 백업

### 11.4 코드 품질
- Python: Black + Ruff
- TypeScript: Prettier + ESLint
- 테스트: 핵심 로직 70%+
- 로그: 구조화 JSON

---

## 12. 개발 로드맵

### Phase 0: 인증 + 기본 레이아웃 (1주)

**Day 1~2: 프로젝트 셋업**
- [ ] Git 저장소, 디렉토리 구조
- [ ] Docker Compose 로컬 환경
- [ ] Next.js 14 / FastAPI 부트스트랩
- [ ] PostgreSQL + Alembic

**Day 3~4: 인증**
- [ ] users 테이블 (아이디/비밀번호/닉네임/핸드폰/이메일)
- [ ] 회원가입 API + 폼
- [ ] 로그인 API + JWT
- [ ] 인증 미들웨어 + 프론트 가드

**Day 5~7: 대시보드 레이아웃 + 투자 개념 정리**
- [ ] 사이드바 + 헤더 공통 레이아웃
- [ ] 홈 페이지 (4개 카드)
- [ ] 백테스트 / 투자 현황 Placeholder
- [ ] 모바일 하단 탭바
- [ ] glossary_categories, glossary_terms 테이블
- [ ] 시드 데이터 삽입 (12개 용어)
- [ ] 개념 목록/상세 API + 페이지
- [ ] 키워드 검색

**완료 기준**:
- ✅ 회원가입 → 로그인 → 대시보드 접근
- ✅ 4개 메뉴 네비게이션 동작
- ✅ 투자 개념 정리에서 용어 조회 가능

### Phase 1: RSS 수집 (1주)

**Day 8~10: 수집 파이프라인**
- [ ] rss_feeds, news 테이블
- [ ] 시드 데이터 삽입 (18개 피드)
- [ ] 피드 검증 스크립트로 HTTP 200 + 파싱 성공 확인
- [ ] feedparser 수집 모듈
- [ ] worker 컨테이너 + APScheduler 통합
- [ ] PostgreSQL advisory lock 기반 중복 실행 방지
- [ ] 중복 제거 로직

**Day 11~14: 관리 UI + 데이터 확인**
- [ ] 피드 목록/토글 UI
- [ ] 수집 통계 확인 (일 수집량, 피드별 성공률)
- [ ] 3~4일 수집 데이터 축적 → 일일 기사 수 파악

**완료 기준**:
- ✅ 1시간마다 자동 수집
- ✅ 일일 수집량 파악 완료

### Phase 2: 데일리 브리핑 ⭐ (1주)

**Day 15~17: 브리핑 생성**
- [ ] briefings 테이블
- [ ] Claude API 클라이언트 (Haiku)
- [ ] 프롬프트 개발/테스트
- [ ] 스케줄 등록 (06:30)

**Day 18~21: 브리핑 UI**
- [ ] 오늘의 브리핑 페이지
- [ ] 아카이브 페이지
- [ ] 홈 대시보드 카드 연동
- [ ] 수동 재생성 버튼
- [ ] 키워드 검색

**완료 기준**:
- ✅ 매일 6:30 자동 브리핑 생성
- ✅ 대시보드 + 브리핑 페이지에서 확인

### Phase 3: 배포 및 안정화 (1주)

**Day 22~24: 배포**
- [ ] Contabo VPS 배포
- [ ] Docker Compose Production
- [ ] Nginx + SSL
- [ ] GitHub Actions CI/CD

**Day 25~28: 안정화**
- [ ] 1주 운영 후 비용 체크
- [ ] 프롬프트 품질 개선
- [ ] 버그 수정, README

**완료 기준**:
- ✅ Production 도메인 접속
- ✅ 매일 자동 운영
- ✅ 월 Claude API $5 이하

### 총 예상 기간
- **집중 개발**: 4주
- **업무 병행**: 6~8주

---

## 13. 배포 및 운영

### 13.1 Docker Compose (Production)

```yaml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_URL=https://brief.ysj.example.com/api/v1

  backend:
    build: ./backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - TZ=Asia/Seoul
    depends_on:
      postgres:
        condition: service_healthy

  worker:
    build: ./backend
    restart: unless-stopped
    command: ["python", "-m", "app.scheduler.worker"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - TZ=Asia/Seoul
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: ysj_brief
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/letsencrypt

volumes:
  pgdata:
```

### 13.2 환경변수 (.env.example)

```
DATABASE_URL=postgresql://ysj:pass@postgres:5432/ysj_brief
DB_USER=ysj
DB_PASSWORD=<change_me>
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=<random_long_string>
JWT_EXPIRE_DAYS=30
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 13.3 백업
- 일일 `pg_dump` → `/backups/YYYYMMDD.sql`
- 7일 보관

### 13.4 비용 요약
| 항목 | 월 비용 |
|------|--------|
| Contabo VPS | $5~8 (기보유) |
| Claude API | $1~5 (Haiku) |
| 도메인 | 기보유 |
| SSL | $0 |
| **추가 비용** | **$1~5** |

---

## 14. 리스크 관리

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| Claude 비용 증가 | 중 | 중 | Haiku 고수, 월 모니터링 |
| RSS 피드 종료 | 중 | 낮 | 자동 비활성화 + 로그 |
| VPS 다운 | 낮 | 중 | 자동 재시작, 백업 |
| AI 오판 | 중 | 낮 | 프롬프트 튜닝 |
| 저작권 | 낮 | 중 | 요약 + 원문 링크 |
| 계정 탈취 | 낮 | 중 | bcrypt, JWT, Rate Limit |

---

## 15. 향후 확장 계획

### 15.1 백테스트 메뉴 (단기)
- 전략 스크립트 업로드
- 과거 데이터 기반 수익률 계산
- MDD, 샤프 비율 등 성과 지표

### 15.2 투자 현황 메뉴 (중기)
- KIS API 연동, 보유 종목 시세
- 거래 기록 + 매매 일지
- 수익률 추이 차트

### 15.3 브리핑 고도화 (중기)
- 기사별 개별 AI 요약 (비용 허용 시)
- 보유 종목 관련 뉴스 필터
- 주간 다이제스트
- 시맨틱 검색 (pgvector)

### 15.4 알림 채널 (필요 시)
현재는 웹 확인만. 추후:
- Discord 웹훅
- 사내 메신저 (Slack/Teams)
- 이메일 (Resend)

구현 방향: `services/notifications/` 어댑터 패턴

### 15.5 대화형 AI
- "이번 주 개발 트렌드 요약해줘"
- "내 포트폴리오 분석해줘" (투자 현황 연동 후)

---

## 부록

### A. 변경 이력
| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| 1.0 | 2026-04-20 | 초안 (InvestMate) |
| 2.0 | 2026-04-20 | 브리핑 모듈 재정의, ysj.brief |
| 3.0 | 2026-04-20 | 3-메뉴 대시보드, 인증, 비용 절감 |
| 3.1 | 2026-04-20 | 회원가입 필드 확정, 메뉴명 "데일리 브리핑", 축적기간 조정 |
| 3.2 | 2026-04-20 | "투자 개념 정리" 메뉴 추가, glossary 테이블/시드 데이터 |

---

**문서 끝**
