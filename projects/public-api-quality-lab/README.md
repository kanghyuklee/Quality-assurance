# Public API Quality Lab

**Python-Based REST API Test Automation Framework**

## 1. 프로젝트 개요

공개 REST API를 대상으로 기능 검증, 예외 처리, 응답 계약 검증 및 회귀 테스트를 자동화하는 QA 프로젝트입니다.

단순 API 요청 실행이 아닌, 재사용 가능한 테스트 프레임워크와 CI 기반 품질 검증 체계를 구현하는 것을 목표로 합니다.

## 2. 테스트 대상

**Restful-Booker**

[https://restful-booker.herokuapp.com/](https://restful-booker.herokuapp.com/)

예약 관리 기능을 제공하는 공개 API 테스트 환경입니다.

테스트 범위:

- Health Check
- 인증
- 예약 생성
- 예약 조회
- 예약 수정
- 예약 삭제
- 잘못된 요청 및 경계값 검증

## 3. 기술 스택

| 영역 | 기술 |
| --- | --- |
| 언어 | Python |
| 테스트 프레임워크 | Pytest |
| HTTP Client | HTTPX |
| 데이터 검증 | Pydantic |
| 테스트 리포트 | Allure, JUnit XML |
| CI | GitHub Actions |
| 코드 품질 | Ruff |

## 4. 프레임워크 설계 원칙

### 재사용성

API 요청과 테스트 로직을 분리하고 공통 Client를 구현합니다.

### 독립성

각 테스트가 자체 테스트 데이터를 사용하도록 구성하고, 테스트 순서에 따른 의존성을 최소화합니다.

### 확장성

API 기능별 테스트 모듈을 분리하고 Pytest Fixture 및 Parametrize를 활용합니다.

### 관측 가능성

실패 시 요청·응답 정보, 상태 코드, 검증 항목을 수집합니다. 인증정보는 로그에서 마스킹합니다.

### CI 자동화

Smoke Test와 Functional Test를 구분해 GitHub Actions에서 실행합니다.

## 5. 테스트 분류

- Smoke Test: 핵심 API 정상 동작 확인
- Functional Test: CRUD 기능 검증
- Negative Test: 잘못된 입력 및 예외 처리
- Contract Test: API 명세와 응답 구조 비교
- Integration Test: 예약 생성부터 삭제까지의 흐름 검증
- Regression Test: 변경 이후 기존 기능 검증

## 6. 테스트 결과 관리

다음 항목을 기록합니다.

- 전체 테스트 수
- Pass / Fail / Skip
- 실패 유형 및 원인
- 요청·응답 증거
- 재현 절차
- 명세와 구현의 불일치
- 테스트 환경의 제약사항

공개 테스트 서버의 초기화 및 공유 상태에 의한 실패는 제품 결함과 구분합니다.

## 7. 개발 단계

1. 테스트 대상 API 분석
2. Pytest 프로젝트 초기화
3. 공통 API Client 및 Fixture 구현
4. Smoke Test 구현
5. CRUD 기능 테스트 구현
6. Negative 및 Contract Test 확장
7. 리포트·로그 자동화
8. GitHub Actions CI 구성
9. 회귀 안정성 검증 및 결함 분석

## 8. 프로젝트 상태

**Status: Planning**

현재 문서는 초기 설계안입니다. 실제 테스트 실행 결과와 발견 결함은 구현 이후 추가합니다.
