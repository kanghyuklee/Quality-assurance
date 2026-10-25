# -*- coding: utf-8 -*-
"""tc_data.py → 테스트 계획서 Markdown 생성 (요구사항↔TC 매핑·건수 자동 반영)."""
import sys
from collections import Counter, OrderedDict
import tc_data as D

OUT = sys.argv[1]

def esc(s):
    return str(s).replace("|", "\\|").replace("\n", "<br>")

def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)

def tc_by_req(rid):
    ids = [t[0].replace("TC-", "") for t in D.TCS if rid in t[3]]
    return ", ".join(ids) if ids else "-"

def tc_by_q(qid):
    return ", ".join(t[0].replace("TC-", "") for t in D.TCS if qid in t[11]) or "-"

def n_pri(p): return sum(1 for t in D.TCS if t[6] == p)

cats = OrderedDict((c, Counter()) for c in D.CATEGORIES)
for t in D.TCS:
    cats[t[1]][t[6]] += 1
    cats[t[1]]["total"] += 1
exec_cnt = Counter(t[5] for t in D.TCS)
basis_cnt = Counter(t[4] for t in D.TCS)
prefix_of = OrderedDict()
for t in D.TCS:
    prefix_of.setdefault(t[1], t[0].split("-")[1])
auto_cnt = Counter(D.AUTOMATION.values())
auto_by_cat = OrderedDict((c, Counter()) for c in D.CATEGORIES)
for t in D.TCS:
    auto_by_cat[t[1]][D.AUTOMATION[t[0]]] += 1
N = len(D.TCS)

md = []
A = md.append
A(f"# {D.TITLE} 계획서")
A("")
A(f"**작성일** {D.DATE} · **작성자** {D.AUTHOR} · **대상** LINE Messaging API(공개 개발자 문서 기준, api.line.me v2) · **문서 버전** v1.0")
A("")
A("> 개인 QA 포트폴리오용 문서입니다. LINE Developers가 공개한 Messaging API 레퍼런스·가이드에서 요구사항을 역도출해 **테스트 계획과 케이스 설계까지**를 산출물로 합니다. 실행은 범위에 포함하지 않으며, 5장 실행 계획은 수행 시 따를 절차·통제 규칙을 설계 관점에서 기술한 것입니다. LY Corporation·LINE과는 무관합니다.")
A("")
A("## 1. 개요")
A("")
A("### 1.1 목적")
A("")
A("- 메시지 발송(reply·push·multicast·broadcast·narrowcast) → 웹훅 수신 → 서명 검증 → 재전송·중복 처리로 이어지는 **메시지 송수신 계약**이 공개 문서(REQ-01~%02d)와 일치하는지 검증" % len(D.REQS))
A("- 플랫폼 API 품질의 핵심 축 — 인증·권한, 상태 코드·오류 포맷, 입력 검증·경계, **멱등성(리트라이 키)**, 비동기 상태, 페이지네이션, 레이트리밋·쿼터, **웹훅 보안·신뢰성** — 을 각각 TC 그룹으로 체계화")
A("- 공개 문서만으로 확정할 수 없는 동작을 질의사항(Q01~Q%02d)으로 분리해 실제 응답을 기록" % len(D.QUESTIONS))
A("- 플랫폼(LINE) 쪽 계약과 **우리 쪽 구현(봇서버·API 클라이언트)**의 책임을 나눠, 어느 쪽 결함인지 판정할 수 있는 구조로 설계")
A("")
A("### 1.2 배경")
A("")
A("- Messaging API는 '우리가 호출하는 API'(발송·조회)와 '플랫폼이 우리를 호출하는 웹훅'이 한 쌍으로 동작한다. 한쪽만 테스트하면 중복 발송(리트라이 키 미사용)·웹훅 유실(비2xx 응답)·위조 웹훅 처리(서명 미검증) 같은 결함이 남는다")
A("- 레퍼런스는 상태 코드·오류 본문·한도·만료 시간을 숫자로 명시하므로 경계값·결정 테이블·상태 전이를 적용하기 좋다. 반면 재전송 횟수·간격, reply token 만료 경계 등은 의도적으로 비공개·비보장이어서 질의로 분리했다")
A("- 개발 가이드라인이 레이트리밋 초과 요청·부하 테스트·무효 userId 요청을 금지하므로, 한도·장애 시나리오는 **모의 서버(MK1)**에서 클라이언트 동작을 검증하고 실플랫폼에서는 1회 관찰로 제한한다")
A("- 기존 `public-api-quality-lab`(Restful-Booker pytest 자동화 구현)과 역할을 나눠, 이 프로젝트는 **설계**(계획·케이스·노트)에 집중하고 8장에서 자동화 계층을 설계안으로 제시한다")
A("")
A("### 1.3 범위")
A("")
A(table(["구분", "포함", "제외"], [
    ("발송 API", "reply, push, multicast, broadcast, narrowcast(오디언스·속성·limit), validate 5종, 로딩 애니메이션, 읽음 처리", "Flex 메시지 레이아웃 세부, 리치 메뉴, 오디언스 관리 API 전체, 쿠폰·멤버십·인사이트"),
    ("인증", "채널 액세스 토큰 4종 발급·검증·폐기·만료, Authorization 헤더 변형, 401/403", "LINE Login(OAuth 인가 코드 흐름), LIFF"),
    ("공통 계약", "상태 코드, 오류 본문 스키마, X-Line-Request-Id, Content-Type·JSON 파싱·2MB 상한, 경로 정확성, 비파괴 변경 내성", "SDK 내부 구현"),
    ("멱등성·재시도", "X-Line-Retry-Key 409·24시간·본문 불일치, 상태 코드별 재시도 정책, 백오프", "플랫폼 내부 중복 제거 알고리즘"),
    ("웹훅", "요청 형식·서명 검증(HMAC-SHA256)·빈 events·헤더 대소문자·이벤트 타입 분기·재전송 동일성·webhookEventId 중복 제거·순서 역전·설정/테스트 API", "그룹 관리 API, 계정 연동(account link), 비콘"),
    ("한도·조회", "레이트리밋 429 계약(모의)·낮은 한도 1회 관찰·월 쿼터 조회, 팔로워 ID 페이지네이션, 프로필·콘텐츠 조회 상태", "성능·부하 테스트(가이드라인 금지), 요금제 변경"),
]))
A("")
A("### 1.4 가정 및 제약")
A("")
A("- 산출물 범위: 테스트 계획서와 테스트 케이스(설계). 수행·결함 리포트는 범위 외이며, 케이스 파일의 결과·결함 시트는 수행 시 사용할 양식으로 제공")
A("- 환경: 개인 프로바이더의 테스트 채널(CH1)과 보조 채널(CH2), 테스트 LINE 계정 3개(U1·U2·U3), 로컬 봇서버(B1, ngrok HTTPS), LINE API 모의 서버(MK1). 실결제·유료 플랜 없이 **월 무료 메시지 한도 내**에서 수행")
A("- 발송 TC는 테스트 계정에게만 보내고, 가이드라인에 따라 동일 사용자 대량 발송·무효 userId 반복 요청·한도 초과 요청을 하지 않는다(필요한 경우 1회 관찰로 제한)")
A("- 팔로워 ID API(verified/premium 계정 전용) 등 계정 유형 제약이 있는 TC는 조건 미충족 시 Blocked로 사유를 기록")
A(f"- 문서는 변경될 수 있으므로 조회일({D.DATE})을 명시. 수행 시점에 문서가 바뀌면 요구사항을 갱신하고 TC 변경 이력을 비고에 남김")
A("- 문서상 비보장·비공개 항목(reply token 1분 경계, 재전송 횟수·간격)은 Pass/Fail 대신 '관찰'로 기록하고 설계 권고로 전환")
A("- 정책 미정 항목은 2.2 질의사항으로 관리하고, 회신(확인) 전에는 '현재 동작 기록 후 판정' 원칙 적용")
A("")
A("## 2. 요구사항 분석")
A("")
A("### 2.1 요구사항 추적 매트릭스")
A("")
A("요구사항은 LINE Developers의 Messaging API reference(Common specifications, Webhooks, Channel access token, Message, Users 등)와 docs(Receive messages, Retry failed API requests, Verify webhook signature, Development guidelines, Channel access token 기초)에서 도출했다. 출처 열은 역도출 근거다.")
A("")
A(table(["ID", "요구사항", "출처", "관련 TC", "중요도"], [
    (rid, text, src, tc_by_req(rid), imp) for rid, text, src, imp in D.REQS
]))
A("")
A("### 2.2 질의사항")
A("")
A(f"공개 문서만으로 기대결과를 확정할 수 없는 항목 {len(D.QUESTIONS)}건. 해당 TC의 기대결과는 'Qn 회신 후 확정'으로 표기하고, 수행 시 실제 응답(상태 코드·본문·헤더)을 실측·메모 열에 기록해 판정한다. 확인 결과는 케이스 파일의 '질의사항' 시트에 남긴다.")
A("")
A(table(["ID", "질의", "영향", "회신 전 처리", "영향 TC"], [
    (qid, q, impact, pre, tc_by_q(qid)) for qid, q, impact, pre in D.QUESTIONS
]))
A("")
A("## 3. 테스트 전략")
A("")
A("### 3.1 테스트 중점")
A("")
A("- **중복 발송 방지(멱등성)**: 500·타임아웃 뒤 재시도에서 메시지가 2건 가지 않아야 한다. 리트라이 키의 409·X-Line-Accepted-Request-Id·24시간 만료를 상태 전이로 설계하고, 클라이언트 재시도 정책(상태 코드별)을 모의 서버로 검증")
A("- **웹훅 보안·신뢰성**: 서명 검증은 원문 바이트로, 불일치·누락은 거부. 재전송 시 webhookEventId로 중복 제거, timestamp로 순서 판단, 200은 즉시 반환(비동기 처리). 서명 미검증은 위조 웹훅을 처리하는 S1 결함")
A("- **계약 경계**: 문서에 숫자가 있는 모든 한도(5개 메시지, 5000 UTF-16 유닛, 500 userId, 13 quick reply, 20 이모지, 30자 유닛명, limit 1000, 500자 URL, 15분·30일·24시간·14일)를 3점 경계값으로 검증")
A("- **발송 성공 ≠ 도달**: 차단·탈퇴·미친구 사용자에게 200이 반환되지만 미도달인 플랫폼 특성을 결정 테이블로 정리하고, 발송 결과 해석 규칙을 클라이언트 설계에 반영")
A("")
A("### 3.2 테스트 유형")
A("")
A(table(["유형", "내용", "TC 그룹"], [
    ("계약(스키마)", "성공·오류 응답 필드·타입, 헤더, Content-Type, 미지 필드 내성", "CMN, AUTH"),
    ("인증·권한", "토큰 발급·검증·폐기·만료, 헤더 변형, 401/403", "AUTH, PGN-005, SEC"),
    ("경계값", "메시지 수·길이(UTF-16)·수신자 수·quickReply·이모지·유닛명·limit·URL 길이·시간 한도", "MSG, RPL, PSH, MLT, PGN, WHS"),
    ("멱등성·재시도", "리트라이 키 409·24h·본문 불일치, 상태 코드별 재시도", "IDM, RPL-007"),
    ("상태 전이", "리트라이 키 요청 상태, 웹훅 전달·재전송 상태, narrowcast phase, 토큰 수명", "IDM, WHS, MLT, AUTH"),
    ("웹훅 보안·신뢰성", "서명 검증, 헤더 대소문자, 빈 events, 중복·순서, 비동기 응답", "WHK, WHS"),
    ("레이트리밋·쿼터", "429 두 종류, 토큰 버킷, 채널·메서드 단위, 월 한도 조회", "RLM, MLT-006"),
    ("페이지네이션·조회", "limit 경계, next 순회, 토큰 만료, 프로필·콘텐츠 상태 코드", "PGN"),
    ("보안·운영", "토큰·secret 교체 영향, 민감정보 노출, 로그 마스킹, 상수 시간 비교", "SEC"),
    ("회귀(스모크)", "stateless 토큰 발급 → bot info → validate → push 1건 → 웹훅 수신·서명", "AUTH-001, CMN-001, MSG-009, PSH-001, WHK-001/002"),
]))
A("")
A("### 3.3 설계 기법 — 규칙의 형태에 기법을 맞춤")
A("")
A(table(["규칙의 형태", "기법", "적용한 곳"], [
    ("조건 여러 개가 AND로 결합되어 응답이 정해짐", "결정 테이블", "푸시 발송 결과 판정(토큰 × 메시지 × 대상 존재 × 수신 가능 → 401/400/200 미도달/200 도달, 3.4), 리트라이 키 처리 판정(지원 엔드포인트 × 키 × 수락 이력, 3.5)"),
    ("숫자 한도가 명시됨", "경계값 분석(3점)", "messages 5개, text 5000 유닛, multicast 500, quickReply 13, emojis 20, 유닛명 30자, limit 1000, URL 500자, loadingSeconds 5~60, 토큰 15분·24시간·14일. ±1 단위(문자·개수) 또는 ±10초(시간)"),
    ("요청·이벤트가 시간에 따라 상태를 바꿈", "상태 전이", "리트라이 키 요청 상태(3.6), 웹훅 전달·재전송 상태(3.7), narrowcast phase(waiting→sending→succeeded/failed), 토큰 발급→유효→만료/폐기"),
    ("입력을 동작이 같은 집합으로 나눌 수 있음", "동등 분할", "메시지 타입(text/sticker/image/location/template/flex), 토큰 4종, 대상 유형(user/group/room), 429 두 종류(레이트리밋/월 한도), 재시도 가능(500·타임아웃) vs 불가(2xx·409·4xx)"),
    ("독립 변수 여러 개의 조합을 전수 검증하기엔 많음", "페어와이즈", "발송 엔드포인트(4) × 메시지 타입(6) × notificationDisabled(2) = 48조합 → 10조합(3.8, TC-MSG-010)"),
    ("문서에 없지만 구현에서 자주 틀리는 지점", "오류 추정", "재직렬화 후 서명 계산, 헤더 이름 대소문자, 특수문자 본문 서명, 같은 키·다른 본문, 첫 요청 키 누락, 동기 처리로 인한 타임아웃, 재전송 순서 역전, 24h 직후 중복"),
]))
A("")
A("### 3.4 푸시 발송 결과 판정 결정 테이블")
A("")
A(table(list(D.PUSH_DECISION[0]), D.PUSH_DECISION[1:]))
A("")
A("4조건 16조합 중 선행 조건이 N이면 후행 조건이 무의미하므로 5행으로 축약했다. 핵심은 4행 — **200이 도달을 뜻하지 않는다**는 점이며, 클라이언트는 200을 '수락'으로만 해석하고 도달 여부는 별도 지표(콘솔 통계·사용자 피드백)로 본다.")
A("")
A("### 3.5 리트라이 키 처리 판정 결정 테이블")
A("")
A(table(list(D.RETRY_DECISION[0]), D.RETRY_DECISION[1:]))
A("")
A("### 3.6 리트라이 키 요청 상태 전이")
A("")
A(table(["현재 상태", "이벤트", "다음 상태", "검증 포인트"], D.RETRY_STATES))
A("")
A("### 3.7 웹훅 전달 상태 전이")
A("")
A(table(["현재 상태", "이벤트", "다음 상태", "검증 포인트"], D.WEBHOOK_STATES))
A("")
A("### 3.8 메시지 타입 × 엔드포인트 × 알림 페어와이즈")
A("")
A("발송 엔드포인트 4종(reply/push/multicast/broadcast) × 메시지 타입 6종 × notificationDisabled 2값의 전수 48조합 대신, 모든 2-요인 쌍이 최소 1회 등장하는 10조합을 선정했다(TC-MSG-010). narrowcast는 오디언스 조건이 별도 축이라 제외하고 MLT 그룹에서 다룬다.")
A("")
A(table(["#", "엔드포인트", "메시지 타입", "notificationDisabled"], D.PAIRWISE))
A("")
A("## 4. 테스트 환경 및 데이터")
A("")
A("### 4.1 환경")
A("")
A(table(["항목", "내용"], [
    ("플랫폼", "LINE Messaging API (https://api.line.me, https://api-data.line.me). 공개 문서 조회일 " + D.DATE),
    ("채널", "CH1 메인 테스트 채널(Webhook·재전송 ON) / CH2 타 프로바이더 채널. 콘솔 Admin 권한"),
    ("계정", "테스트 LINE 계정 3개(U1 친구, U2 차단, U3 미친구 발신), 그룹 2개(G1 참여, G2 탈퇴)"),
    ("봇서버", "B1: 로컬 FastAPI + ngrok HTTPS. 서명 검증·원문 로그·중복 제거·응답 모드 전환(200/500/지연/종료)"),
    ("모의 서버", "MK1: LINE API 응답을 흉내 내는 로컬 서버. 429·500·타임아웃·409·월 한도·미지 필드·500건 수신자 시나리오"),
    ("클라이언트", "Python 3.12, httpx(요청·응답 로그, 재시도·백오프 모듈), pytest. 토큰·secret은 환경 변수"),
    ("도구", "LINE Developers Console(Verify·통계·토큰 재발급), LINE 앱(도달 확인), 요청·응답 로그 파일(증적)"),
]))
A("")
A("### 4.2 테스트 데이터")
A("")
A("채널·계정·서버·토큰·샘플은 케이스 파일의 '테스트 데이터' 시트에 조건과 사용 TC를 정리했고, 수행 전 준비 완료 여부(Y/N)와 실제 값(비밀값 제외)을 기록한다. 핵심 데이터는 다음과 같다.")
A("")
A(table(["구분", "ID", "조건", "사용 TC"], [
    (k, i, cond, use) for k, i, name, cond, use in D.TEST_DATA if i in ("CH1", "CH2", "U1", "U2", "U3", "B1", "MK1", "T1", "T2", "T3", "MS1", "RK1~RK7")
]))
A("")
A("## 5. 실행 계획")
A("")
A("### 5.1 수행 순서")
A("")
A(table(["차수", "대상", "내용", "비고"], [
    ("0차", "환경 검증", "stateless 토큰 발급 → GET /v2/bot/info → 콘솔 Verify로 B1 수신 확인(스모크 6건)", "실패 시 이후 차수 Blocked"),
    ("1차", f"무발송 TC {exec_cnt['무발송']}건", "인증·공통 계약·validate 기반 메시지 검증·웹훅 수신/서명·모의 서버 기반 재시도/429·조회 API 순으로 수행. 발송 없이 계약을 먼저 고정", "P1 우선, 질의 항목은 현재 동작 기록"),
    ("2차", f"발송 TC {exec_cnt['발송']}건", "테스트 계정에게만 발송. reply 토큰은 수신 즉시 사용, 리트라이 키 케이스는 도달 건수를 앱에서 확인. 1일 발송 상한 50건으로 월 무료 한도 보호", "같은 사용자에게 연속 대량 발송 금지"),
    ("3차", f"장기·한도 TC {exec_cnt['장기·한도']}건", "stateless 15분 만료, v2.1 30개 한도, 리트라이 키 24시간, continuation token 24시간, webhook test 60/h 1회 초과, narrowcast 14일 상태 창", "타이머·캘린더로 시각 기록, 대기 중 1차 잔여 수행"),
    ("재검증", "Fail TC", "플랫폼 결함은 수정 전제가 없으므로 재현율 확인 목적의 재수행 3회. 봇서버·클라이언트 결함은 수정 후 재검증", "재현율·X-Line-Request-Id를 결함 리포트에 기록"),
]))
A("")
A("### 5.2 발송·한도 통제 규칙")
A("")
A("- 발송 대상은 테스트 계정(U1~U3)·테스트 그룹(G1)으로 한정하고, broadcast는 친구가 테스트 계정뿐임을 확인한 뒤 수행한다")
A("- 레이트리밋 초과는 실플랫폼에서 **webhook test(60/h) 1회 초과 관찰**만 허용하고, 나머지 429·500·타임아웃 시나리오는 MK1에서 수행한다(개발 가이드라인 준수)")
A("- 무효 userId·타채널 ID·미참여 그룹 요청은 케이스당 1회로 제한한다")
A("- 모든 발송 요청에 리트라이 키를 넣고, 케이스가 끝나면 키를 재사용하지 않는다(24시간 보관으로 다음 케이스 오염 방지)")
A("- 토큰·채널 secret·개인 키는 환경 변수로만 다루고 케이스 파일·로그·증적에 평문으로 남기지 않는다")
A("")
A("### 5.3 우선순위 정의")
A("")
A(table(["우선순위", "기준", "TC 수"], [
    ("P1", "중복 발송·메시지 유실·위조 웹훅 처리·인증 우회로 이어질 수 있는 경로, 문서에 명시된 핵심 계약(상태 코드·오류 포맷·한도)", n_pri("P1")),
    ("P2", "계약 경계·조합, 재시도·재전송 복구 경로, 조회·페이지네이션 정확성", n_pri("P2")),
    ("P3", "오류 문구·선택 파라미터·드문 조건, 코드 리뷰성 항목", n_pri("P3")),
]))
A("")
A("### 5.4 결과 판정")
A("")
A("- **Pass / Fail / Blocked / N/A**를 케이스 시트의 결과 열에 기록. Blocked는 사전 조건 미충족(verified 계정 아님, 보조 계정 미확보, 모의 서버 미구현), N/A는 수행 시점에 기능·엔드포인트가 존재하지 않는 경우")
A("- 질의(Qn) 연결 TC는 실측·메모 열에 실제 상태 코드·본문·헤더를 먼저 기록하고, 문서·콘솔 안내로 근거가 확인되면 그 기준으로 판정한다. 근거가 없으면 '현재 동작 기록'으로 두고 Fail 처리하지 않는다")
A("- 문서상 비보장 항목(reply token 1분 경계, 재전송 횟수·간격)은 '관찰'로 기록하고 Pass/Fail을 매기지 않는다")
A("- 결함은 **플랫폼 / 봇서버 / 클라이언트** 중 어디 책임인지 분류해 '결함 리포트' 시트에 등록하고 TC의 결함 ID 열에 연결한다. 모든 Fail은 요청·응답 전문(X-Line-Request-Id 포함, 토큰 마스킹)을 첨부한다")
A("")
A("### 5.5 결함 심각도")
A("")
A(table(["심각도", "기준", "예시"], [
    ("S1", "중복 발송, 메시지 유실, 서명 미검증으로 위조 웹훅 처리, 토큰·secret 노출", "같은 리트라이 키 재요청이 200으로 2건 도달, 서명 불일치 웹훅을 처리해 reply 발송"),
    ("S2", "계약 위반(상태 코드·오류 포맷 불일치), 경계값 오판정, 재시도 정책 오동작", "4xx에 재시도, 5001 유닛 텍스트가 200, webhookEventId 중복 처리"),
    ("S3", "오류 메시지 문구·필드명 불일치, 우회 가능한 클라이언트 이상", "details.property 경로 표기 차이, 로그 형식 누락"),
    ("S4", "개선 제안, 사소한 표기", "로그 시각 포맷"),
]))
A("")
A("### 5.6 완료 기준")
A("")
A("- P1 TC 100% 수행(Blocked 포함 시 사유 기록), P2 90% 이상 수행")
A("- S1·S2 결함 0건 또는 각 결함에 재현 절차·재현율·X-Line-Request-Id·증적이 갖춰진 리포트 존재")
A(f"- 질의사항 Q01~Q{len(D.QUESTIONS):02d} 전부 '확인 결과' 기록")
A("- 요약 시트의 요구사항 커버리지에서 연결 TC 수 0인 요구사항 없음")
A("- 월 무료 메시지 한도를 초과하지 않음(quota/consumption으로 수행 전후 확인)")
A("")
A("### 5.7 산출물")
A("")
A("- 테스트 계획서(본 문서, Markdown)")
A("- 테스트 케이스(xlsx): 요약(자동 집계) · 테스트케이스 · 테스트 데이터 · 질의사항 · API 체크리스트 · 결함 리포트")
A("- 증적: 요청·응답 로그(토큰 마스킹), 봇서버 수신 로그, 콘솔 통계 스크린샷(파일명을 TC·결함 ID와 일치)")
A("- 결과 보고(수행 완료 후 요약 시트 기준으로 작성)")
A("")
A("## 6. 리스크 및 대응")
A("")
A(table(["리스크", "영향", "대응"], [
    ("개발 가이드라인 위반(한도 초과·부하·무효 ID 반복)", "채널 제재, 테스트 중단", "429·500·타임아웃·500건 수신자 시나리오는 MK1로 대체, 실플랫폼 초과 관찰은 1회, 무효 ID 요청은 케이스당 1회"),
    ("월 무료 메시지 한도 소진", "발송 TC Blocked", "1일 발송 상한 50건, validate로 1차 검증 후 발송, quota/consumption 수행 전후 기록"),
    ("verified/premium 계정 아님", "PGN-001~004 Blocked", "403 확인으로 PGN-005만 수행, 나머지는 사내 환경 항목으로 표시"),
    ("문서상 비보장·비공개 동작", "Pass/Fail 판정 불가", "'관찰'로 기록(Q07·Q09), 설계 권고(즉시 사용·멱등 수신)로 전환"),
    ("웹훅 재전송 발생 시점 예측 불가", "WHS-005~007 대기 시간 길어짐", "재전송 ON 상태로 1차 수행 중 병행 대기, 콘솔 통계로 발생 여부 확인"),
    ("보조 계정·그룹 확보 어려움", "U2·U3·G1·G2 의존 TC Blocked", "가족·지인 계정 협조 또는 두 번째 기기, 불가 시 Blocked 사유 기록"),
    ("문서 변경", "요구사항 근거 불일치", "조회일 명시, 불일치 발견 시 요구사항 갱신 및 변경 이력 기록"),
]))
A("")
A("## 7. 테스트 케이스 요약")
A("")
A(table(["대분류", "ID 접두", "TC 수", "P1", "P2", "P3"], [
    (c, f"TC-{prefix_of[c]}", cats[c]["total"], cats[c]["P1"], cats[c]["P2"], cats[c]["P3"]) for c in D.CATEGORIES
] + [("합계", "", N, n_pri("P1"), n_pri("P2"), n_pri("P3"))]))
A("")
A(f"설계 근거별: 요구사항 {basis_cnt['요구사항']}건 · 리스크 기반 {basis_cnt['리스크 기반']}건 · 추가 검증 {basis_cnt['추가 검증']}건 / 실행 구분별: 무발송 {exec_cnt['무발송']}건 · 발송 {exec_cnt['발송']}건 · 장기·한도 {exec_cnt['장기·한도']}건")
A("")

# ---------------- 8. 자동화 전략 ----------------
A("## 8. 자동화 전략")
A("")
A(f"본 설계의 {N}건 중 대부분은 '요청 → 응답'이 결정적인 API 계약이므로 자동화 적합도가 높다. 어떤 케이스를 어느 계층에서 돌릴지 정해 두면 회귀 비용이 줄고, LINE 앱·콘솔에서 사람이 확인해야 하는 영역이 분명해진다. 케이스 시트의 '자동화 구분' 열과 요약 시트의 구분별 집계가 이 장의 근거다.")
A("")
A("### 8.1 선정 기준")
A("")
A("- **결정성**: 상태 코드·오류 본문·헤더가 문서로 확정된 케이스는 API 1순위. 질의(Qn) 연결 케이스는 응답을 기록해 기대값이 확정된 뒤 assertion으로 승격")
A("- **발송 없이 검증 가능한가**: validate 엔드포인트·토큰 API·조회 API·모의 서버 케이스는 월 한도를 쓰지 않으므로 PR마다 돌릴 수 있다")
A("- **도달 확인 필요 여부**: 메시지가 실제로 사용자 화면에 표시됐는지는 API로 알 수 없다(200 ≠ 도달). 이 확인이 필요한 케이스는 UI(앱 확인)로 남긴다")
A("- **시간·운영 통제**: 24시간·14일 경과, 콘솔 재발급, 코드 리뷰는 수동")
A("")
A("### 8.2 계층 배치(테스트 피라미드)")
A("")
A(table(["계층", "TC 수", "비율", "대상", "도구·전제"], [
    ("API", auto_cnt["API"], f"{auto_cnt['API']/N:.0%}", "토큰 발급·검증·폐기, 공통 계약(스키마·오류 포맷), validate 기반 메시지 경계, 리트라이 키 409 계약, 웹훅 서명·중복 제거(봇서버 로컬 주입), 모의 서버 기반 재시도·429 정책, 조회·페이지네이션", "pytest + httpx, 테스트 채널 CH1, 봇서버 B1(테스트 클라이언트로 직접 호출), 모의 서버 MK1(respx 또는 로컬 FastAPI). 데이터 주도(parametrize), TC ID 1:1"),
    ("UI", auto_cnt["UI"], f"{auto_cnt['UI']/N:.0%}", "실제 발송 후 LINE 앱 도달·렌더링·알림 확인, 콘솔 Verify·토큰 재발급·secret 재발급, 차단·그룹 조작이 필요한 이벤트", "LINE 앱(테스트 계정 기기) + Developers Console. API 호출은 자동, 확인만 사람이 수행하는 반자동"),
    ("수동", auto_cnt["수동"], f"{auto_cnt['수동']/N:.0%}", "15분·24시간·14일 경과, 30개 토큰 한도, 재전송 대기, 한도 1회 초과 관찰, 코드·설정 리뷰", "타이머·캘린더, 코드 리뷰 체크리스트. 릴리스 전 또는 분기 1회"),
]))
A("")
A("대분류별 배치:")
A("")
A(table(["대분류", "API", "UI", "수동"], [(c, auto_by_cat[c]["API"], auto_by_cat[c]["UI"], auto_by_cat[c]["수동"]) for c in D.CATEGORIES]))
A("")
A("### 8.3 API 계층 설계")
A("")
A("Messaging API 호출은 '요청(헤더·본문) → 상태 코드·헤더·본문'으로 닫히는 순수 함수에 가깝다. 세 가지 장치로 설계 문서와 코드를 1:1로 잇는다.")
A("")
A("- **validate를 1차 게이트로**: 메시지 객체 경계(MSG 그룹)는 모두 `POST /v2/bot/message/validate/{type}`으로 검증한다. 발송이 없어 월 한도를 쓰지 않고, TC-MSG-008로 validate와 실제 발송의 400 본문이 같음을 먼저 확인해 근거를 만든다")
A("- **오류 응답 공통 스키마 검증**: 모든 4xx 케이스에 `message: str` 필수, `details[].property`가 요청 JSON 경로와 일치, `X-Line-Request-Id` 존재를 공통 assertion으로 건다(TC-CMN-002의 자동화 형태)")
A("- **리트라이 키 멱등성**: 같은 키로 2회 호출해 첫 응답 200, 둘째 409, `X-Line-Accepted-Request-Id == 첫 X-Line-Request-Id`, push는 `sentMessages` 동일을 검증한다. 발송 1건이 필요하므로 나이틀리에만 포함")
A("- **웹훅은 봇서버를 직접 호출**: 저장한 원문 웹훅 샘플(MS3)에 유효·변조·누락 서명을 붙여 B1에 POST하고 응답 코드와 처리 여부(저장소·reply 호출 횟수)를 검증한다. LINE 플랫폼을 거치지 않으므로 결정적이고 빠르다")
A("- **클라이언트 정책은 모의 서버로**: 500→200, 타임아웃→200, 409, 429(두 종류)를 MK1이 순서대로 돌려주고 클라이언트의 요청 횟수·헤더·간격을 MK1 로그로 assert한다(IDM-007, RLM 그룹)")
A("- **비밀값**: 토큰·secret은 환경 변수, 로그는 Authorization 마스킹(TC-SEC-004가 이를 검증)")
A("")
A("예시 — TC-MSG-001(text 길이)과 TC-MSG-004(messages 수)를 하나의 파라미터 테이블로:")
A("")
A("```python")
A("@pytest.mark.parametrize(\"tc_id, messages, expected_status, expected_property\", [")
A("    (\"TC-MSG-001-1\", [text(\"a\" * 4999)], 200, None),")
A("    (\"TC-MSG-001-2\", [text(\"a\" * 5000)], 200, None),")
A("    (\"TC-MSG-001-3\", [text(\"a\" * 5001)], 400, \"messages[0].text\"),")
A("    (\"TC-MSG-001-5\", [text(\"\")],         400, \"messages[0].text\"),")
A("    (\"TC-MSG-004-1\", [text(\"ok\")] * 5,   200, None),")
A("    (\"TC-MSG-004-2\", [text(\"ok\")] * 6,   400, \"messages\"),      # Q04 확정 후 기대값 고정")
A("])")
A("def test_validate_push(line, tc_id, messages, expected_status, expected_property):")
A("    r = line.post(\"/v2/bot/message/validate/push\", json={\"messages\": messages})")
A("    assert r.status_code == expected_status")
A("    assert r.headers[\"x-line-request-id\"]")
A("    if expected_status == 400:")
A("        body = r.json()")
A("        assert isinstance(body[\"message\"], str)")
A("        assert any(d[\"property\"] == expected_property for d in body[\"details\"])")
A("```")
A("")
A("웹훅 서명 검증(TC-WHK-002~004)은 봇서버를 테스트 클라이언트로 직접 호출한다:")
A("")
A("```python")
A("def sign(body: bytes, secret: str) -> str:")
A("    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()")
A("")
A("@pytest.mark.parametrize(\"tc_id, mutate_body, mutate_sig, expected\", [")
A("    (\"TC-WHK-002\", lambda b: b, lambda s: s, 200),")
A("    (\"TC-WHK-003-1\", lambda b: b, lambda s: s[:-1] + (\"A\" if s[-1] != \"A\" else \"B\"), 400),")
A("    (\"TC-WHK-003-2\", lambda b: b.replace(b\"hello\", b\"hellp\"), lambda s: s, 400),")
A("    (\"TC-WHK-004\", lambda b: b, lambda s: None, 400),")
A("])")
A("def test_webhook_signature(bot_client, raw_webhook, secret, tc_id, mutate_body, mutate_sig, expected):")
A("    body = mutate_body(raw_webhook)")
A("    sig = mutate_sig(sign(raw_webhook, secret))")
A("    headers = {\"x-line-signature\": sig} if sig is not None else {}")
A("    r = bot_client.post(\"/webhook\", content=body, headers=headers)")
A("    assert r.status_code == expected")
A("```")
A("")
A("### 8.4 UI(앱·콘솔) 계층 설계")
A("")
A("- **범위**: API 호출은 자동으로 수행하고 '도달·표시·알림'만 사람이 LINE 앱에서 확인하는 반자동. 케이스 시트의 실측·메모 열에 도달 건수·스크린샷 파일명을 기록")
A("- **절차 고정**: reply 케이스는 테스트 사용자가 봇에 메시지를 보내는 수동 트리거가 필요하므로, 수행자가 앱에서 보낸 뒤 자동 스크립트가 B1 로그에서 replyToken을 집어 1분 내 호출한다")
A("- **콘솔 조작**: Verify 버튼, long-lived 토큰 재발급, secret 재발급, 재전송 ON/OFF는 콘솔 UI뿐이므로 체크리스트로 유지하고 결과(401 전환, 서명 거부)는 API로 확인")
A("- **사내 환경이라면**: 테스트용 LINE 계정의 수신 메시지를 읽는 내부 도구가 있으면 도달 확인도 자동화 가능. 외부에서는 불가")
A("")
A("### 8.5 수동으로 남기는 영역과 이유")
A("")
A(table(["영역", "TC", "이유"], [
    ("시간 경과", "AUTH-008, IDM-005, PGN-004, MLT-009(3단계)", "15분·24시간·14일 대기가 필요. 스케줄러로 자동화할 수 있으나 외부 포트폴리오에서는 캘린더 기록으로 대체"),
    ("한도 도달", "AUTH-005, RLM-002", "30개 토큰·60/h 한도 소진은 다른 테스트에 영향을 주므로 격리된 시간대에 1회만 수행"),
    ("재전송 대기", "RPL-005, WHS-005, WHS-007", "재전송 시점이 비공개라 대기 시간 예측 불가. 재전송 도착 후 검증 자체는 자동(WHS-006)"),
    ("비결정 관찰", "RPL-003, PSH-006", "문서가 보장하지 않는 경계(1분·7일)는 분포를 기록하는 관찰 항목"),
    ("코드·설정 리뷰", "SEC-005, SEC-006", "상수 시간 비교·IP 제한 여부는 정적 검토 항목"),
]))
A("")
A("### 8.6 CI 운영")
A("")
A("- **PR 단위**: 무발송 API 스위트(토큰·공통 계약·validate·웹훅 서명·모의 서버 정책). 월 한도를 쓰지 않고 수 분 내 완료")
A("- **나이틀리**: 발송 1건이 필요한 멱등성 케이스(IDM-001~003)와 페어와이즈 스모크(MSG-010 일부)를 테스트 계정으로 수행. 1일 발송 상한을 코드로 강제")
A("- **리포트**: TC ID별 결과·X-Line-Request-Id·요청/응답 전문(마스킹)을 Allure 첨부로 모으고, 결과를 케이스 시트의 결과 열에 역반영하는 스크립트를 둔다")
A("- **실패 분류**: 플랫폼 결함 / 봇서버 결함 / 클라이언트 결함 / 테스트 데이터 / 환경(ngrok·네트워크) / 플래키를 태깅. 플랫폼 결함은 수정 전제가 없으므로 재현율과 문서 불일치로 보고")
A("")
A("### 8.7 외부 포트폴리오로서의 제약")
A("")
A("API 계층의 대부분은 테스트 채널만 있으면 **외부에서도 실제 구현 가능**하다(토큰·validate·조회·웹훅 서명·모의 서버). 실제 구현은 `public-api-quality-lab` 프레임워크 위에 올리는 것을 전제로 하며, 이 프로젝트는 그 입력이 되는 설계를 담당한다. 구현 시 가장 먼저 올릴 것은 8.3의 validate 기반 경계 테이블과 웹훅 서명 테스트다 — 월 한도를 쓰지 않고, 중복 발송·위조 웹훅이라는 S1 결함 영역을 직접 막기 때문이다.")
A("")
A("---")
A("")
A("**참고 출처(조회일 " + D.DATE + ")**")
A("")
A("- Messaging API reference: https://developers.line.biz/en/reference/messaging-api/")
A("- Receive messages (webhook) · Webhook redelivery: https://developers.line.biz/en/docs/messaging-api/receiving-messages/")
A("- Verify webhook signature: https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/")
A("- Retry failed API requests: https://developers.line.biz/en/docs/messaging-api/retrying-api-request/")
A("- Channel access token (Basics): https://developers.line.biz/en/docs/basics/channel-access-token/")
A("- Character counting in a text: https://developers.line.biz/en/docs/messaging-api/text-character-count/")
A("- Messaging API development guidelines: https://developers.line.biz/en/docs/messaging-api/development-guidelines/")
A("- Send messages · Verify webhook URL · Pricing: https://developers.line.biz/en/docs/messaging-api/")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")
print("md written:", OUT, "| lines:", len(md))
