# 📌 Final Project README

## 1️⃣ 프로젝트 개요 (Overview)

- **프로젝트명**: AI 사회자 기반 논리 토론 플랫폼  
- **프로젝트 유형**: AI 기반 웹 서비스  
- **개발 기간**: 2025.12.23 ~ 2026.01.26  
- **팀 구성**: 5인 팀 프로젝트  
- **담당 역할**:  
  - 백엔드 API 설계 및 구현  
  - LangGraph 기반 토론 플로우 설계  
  - LLM 프롬프트 설계 및 평가 로직 구현  
  - 전처리(욕설/비방) 파이프라인 설계  

> 본 프로젝트는 **학생 토론에서 발생하는 감정적 논쟁, 주제 이탈, 공정하지 못한 평가 문제**를 해결하기 위해  
> **LLM, RAG, LangGraph**를 활용하여 개발한 **AI 사회자·판정자 기반 토론 서비스**입니다.

---

## 2️⃣ 문제 정의 (Problem Statement)

### 🔍 배경
- 기존 토론 수업/플랫폼의 문제점:
  - 토론이 감정적 말싸움으로 흐르기 쉬움
  - 주제 이탈 및 비방 발언을 실시간으로 제어하기 어려움
  - 결과 평가가 교사/운영자 개인의 주관에 크게 의존
  - 토론 과정 데이터가 구조화되어 축적되지 않음

### ❗ 문제 요약
> **“학생 토론에서 논리보다는 감정과 발언량이 결과를 좌우하고,  
> 토론 과정과 평가가 체계적으로 관리되지 않는다.”**

---

## 3️⃣ 해결 방안 (Solution)

### 💡 핵심 아이디어
- AI 사회자가 토론 전·중·후 전 과정을 구조적으로 관리
- LangGraph를 이용한 **라운드·턴 기반 토론 상태 머신** 설계
- ML + LLM 결합 전처리로 욕설·비방·문맥상 모욕 발언 필터링
- LLM 기반 토론 요약·팩트체킹·승패 판정 자동화

### ✅ 기대 효과
- 감정적 토론 감소 및 논리 중심 토론 유도
- 공정하고 일관된 평가 기준 제공
- 토론 로그 데이터의 체계적 축적 및 재활용 가능
- 교사·운영자의 토론 진행 부담 감소

---

## 4️⃣ 시스템 아키텍처 (System Architecture)

```
[Client (Web)]
↓ (HTTP / WebSocket)
[Backend API (FastAPI)]
↓
[AI / Logic Server]
├─ LangGraph (토론 플로우)
├─ LLM (사회자 / 판정자 / 욕설 비방 탐지)
└─ RAG (주제 생성)
↓
[PostgreSQL]
```

- **Frontend**: React, Vite  
- **Backend**: FastAPI, WebSocket  
- **AI / Logic**: LangGraph, LLM(OpenAI/Gemini), RAG  
- **DB**: PostgreSQL 

## 5️⃣ 주요 기능 (Key Features)

### 👤 사용자 기능
- 토론방 생성 (학년/과목/주제/라운드/인원 설정)
- 실시간 토론 참여 및 발언
- 관전 모드 참여
- 토론 결과 및 피드백 확인

### 🛠 관리자 기능
- 토론 로그 조회
- 토론 결과 및 평가 데이터 관리
- AI 판정 결과 검수

### 🤖 AI 기능
- RAG 기반 토론 주제 자동 생성
- 욕설·비방·모욕 발언 전처리
- 토론 단계별 요약 (입론/반론/최종발언)
- 웹 기반 팩트체킹
- 승·패 강제 판정 및 팀/개인별 피드백 생성

---

## 6️⃣ AI 모델 설명 (AI Model)

- **모델명**: LLM 기반 (GPT / Gemini 계열)  
- **모델 목적**:
  - 사회자 역할 수행
  - 토론 요약 및 평가
  - 팩트체킹 보조
- **학습 데이터**: 사전 학습된 상용 LLM 사용 (Fine-tuning 없음)
- **전처리 방식**:
  - ML 모델 기반 욕설/비방 1차 필터링
  - LLM 기반 문맥상 공격성 2차 판정

### 📊 성능 지표 *(정량 모델 아님 – 서비스 로직 평가 중심)*

| Metric | Value |
|------|------|
| 욕설 탐지 정확도 | 내부 테스트 기준 90% 이상 |
| 판정 일관성 | 동일 입력 반복 시 동일 결과 유지 |
| 응답 시간 | 평균 2~4초 |

---

## 7️⃣ 기술 스택 (Tech Stack)

| 구분 | 기술 |
|----|----|
| Frontend | React, Vite |
| Backend | FastAPI, Python |
| AI | LangGraph, LLM(OpenAI/Gemini), RAG |
| DB | PostgreSQL |

---

## 8️⃣ 프로젝트 구조 (Project Structure)

```
📦 project-root
┣ 📂 frontend
┣ 📂 backend
┣ 📂 shared
┗ README.md
```

---

## 9️⃣ 실행 방법 (How to Run)

### ▶ Backend
```bash
uvicorn main:app --reload
```

### ▶ Frontend
```bash
npm install
npm run dev
```

### ▶ AI Server (선택)
```bash
python main.py
```

---

## 🔟 역할 분담 (Team Roles)

| 이름 | 역할 |
|----|----|
| 김성진| RAG |
| 단해민| 프론트엔드 / 벡엔드 |
| 권나영| 프론트엔드 / 벡엔드 / RAG|
| 이재철| LangGraph / Prompting |
| 김진우| AI 로직 / LangGraph |
---

## 1️⃣1️⃣ 한계점 & 개선 방향 (Limitations & Future Work)

### ⚠️ 한계점
- LLM 응답 시간으로 인한 실시간성 한계
- 팩트체킹의 완전 자동화 어려움
- 대규모 동시 접속 시 비용 증가 
 
### 🚀 개선 방향
- 비동기 Worker 기반 평가 처리 
- 토론 데이터 기반 프롬프트 고도화
- 개인별 토론 성향 분석 및 성장 리포트 제공
- AI 참가자 기능 추가 

---

## 1️⃣2️⃣ 회고 (Retrospective)

- 프로젝트를 통해 얻은 점:
  -  
  -  

---

## 1️⃣3️⃣ 참고 자료 (References)

- LangGraph 공식 문서 
- OpenAI / Gemini API 문서
- RAG 관련 기술 블로그 
