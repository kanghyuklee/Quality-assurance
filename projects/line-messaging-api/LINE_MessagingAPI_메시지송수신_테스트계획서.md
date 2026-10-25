# LINE Messaging API 메시지 송수신 테스트 계획서

**작성일** 2026-10-25 · **작성자** 이강혁 · **대상** LINE Messaging API(공개 개발자 문서 기준, api.line.me v2) · **문서 버전** v1.0

> 개인 QA 포트폴리오용 문서입니다. LINE Developers가 공개한 Messaging API 레퍼런스·가이드에서 요구사항을 역도출해 **테스트 계획과 케이스 설계까지**를 산출물로 합니다. 실행은 범위에 포함하지 않으며, 5장 실행 계획은 수행 시 따를 절차·통제 규칙을 설계 관점에서 기술한 것입니다. LY Corporation·LINE과는 무관합니다.

## 1. 개요

### 1.1 목적

- 메시지 발송(reply·push·multicast·broadcast·narrowcast) → 웹훅 수신 → 서명 검증 → 재전송·중복 처리로 이어지는 **메시지 송수신 계약**이 공개 문서(REQ-01~22)와 일치하는지 검증
- 플랫폼 API 품질의 핵심 축 — 인증·권한, 상태 코드·오류 포맷, 입력 검증·경계, **멱등성(리트라이 키)**, 비동기 상태, 페이지네이션, 레이트리밋·쿼터, **웹훅 보안·신뢰성** — 을 각각 TC 그룹으로 체계화
- 공개 문서만으로 확정할 수 없는 동작을 질의사항(Q01~Q13)으로 분리해 실제 응답을 기록
- 플랫폼(LINE) 쪽 계약과 **우리 쪽 구현(봇서버·API 클라이언트)**의 책임을 나눠, 어느 쪽 결함인지 판정할 수 있는 구조로 설계

### 1.2 배경

- Messaging API는 '우리가 호출하는 API'(발송·조회)와 '플랫폼이 우리를 호출하는 웹훅'이 한 쌍으로 동작한다. 한쪽만 테스트하면 중복 발송(리트라이 키 미사용)·웹훅 유실(비2xx 응답)·위조 웹훅 처리(서명 미검증) 같은 결함이 남는다
- 레퍼런스는 상태 코드·오류 본문·한도·만료 시간을 숫자로 명시하므로 경계값·결정 테이블·상태 전이를 적용하기 좋다. 반면 재전송 횟수·간격, reply token 만료 경계 등은 의도적으로 비공개·비보장이어서 질의로 분리했다
- 개발 가이드라인이 레이트리밋 초과 요청·부하 테스트·무효 userId 요청을 금지하므로, 한도·장애 시나리오는 **모의 서버(MK1)**에서 클라이언트 동작을 검증하고 실플랫폼에서는 1회 관찰로 제한한다
- 기존 `public-api-quality-lab`(Restful-Booker pytest 자동화 구현)과 역할을 나눠, 이 프로젝트는 **설계**(계획·케이스·노트)에 집중하고 8장에서 자동화 계층을 설계안으로 제시한다

### 1.3 범위

| 구분 | 포함 | 제외 |
|---|---|---|
| 발송 API | reply, push, multicast, broadcast, narrowcast(오디언스·속성·limit), validate 5종, 로딩 애니메이션, 읽음 처리 | Flex 메시지 레이아웃 세부, 리치 메뉴, 오디언스 관리 API 전체, 쿠폰·멤버십·인사이트 |
| 인증 | 채널 액세스 토큰 4종 발급·검증·폐기·만료, Authorization 헤더 변형, 401/403 | LINE Login(OAuth 인가 코드 흐름), LIFF |
| 공통 계약 | 상태 코드, 오류 본문 스키마, X-Line-Request-Id, Content-Type·JSON 파싱·2MB 상한, 경로 정확성, 비파괴 변경 내성 | SDK 내부 구현 |
| 멱등성·재시도 | X-Line-Retry-Key 409·24시간·본문 불일치, 상태 코드별 재시도 정책, 백오프 | 플랫폼 내부 중복 제거 알고리즘 |
| 웹훅 | 요청 형식·서명 검증(HMAC-SHA256)·빈 events·헤더 대소문자·이벤트 타입 분기·재전송 동일성·webhookEventId 중복 제거·순서 역전·설정/테스트 API | 그룹 관리 API, 계정 연동(account link), 비콘 |
| 한도·조회 | 레이트리밋 429 계약(모의)·낮은 한도 1회 관찰·월 쿼터 조회, 팔로워 ID 페이지네이션, 프로필·콘텐츠 조회 상태 | 성능·부하 테스트(가이드라인 금지), 요금제 변경 |

### 1.4 가정 및 제약

- 산출물 범위: 테스트 계획서와 테스트 케이스(설계). 수행·결함 리포트는 범위 외이며, 케이스 파일의 결과·결함 시트는 수행 시 사용할 양식으로 제공
- 환경: 개인 프로바이더의 테스트 채널(CH1)과 보조 채널(CH2), 테스트 LINE 계정 3개(U1·U2·U3), 로컬 봇서버(B1, ngrok HTTPS), LINE API 모의 서버(MK1). 실결제·유료 플랜 없이 **월 무료 메시지 한도 내**에서 수행
- 발송 TC는 테스트 계정에게만 보내고, 가이드라인에 따라 동일 사용자 대량 발송·무효 userId 반복 요청·한도 초과 요청을 하지 않는다(필요한 경우 1회 관찰로 제한)
- 팔로워 ID API(verified/premium 계정 전용) 등 계정 유형 제약이 있는 TC는 조건 미충족 시 Blocked로 사유를 기록
- 문서는 변경될 수 있으므로 조회일(2026-10-25)을 명시. 수행 시점에 문서가 바뀌면 요구사항을 갱신하고 TC 변경 이력을 비고에 남김
- 문서상 비보장·비공개 항목(reply token 1분 경계, 재전송 횟수·간격)은 Pass/Fail 대신 '관찰'로 기록하고 설계 권고로 전환
- 정책 미정 항목은 2.2 질의사항으로 관리하고, 회신(확인) 전에는 '현재 동작 기록 후 판정' 원칙 적용

## 2. 요구사항 분석

### 2.1 요구사항 추적 매트릭스

요구사항은 LINE Developers의 Messaging API reference(Common specifications, Webhooks, Channel access token, Message, Users 등)와 docs(Receive messages, Retry failed API requests, Verify webhook signature, Development guidelines, Channel access token 기초)에서 도출했다. 출처 열은 역도출 근거다.

| ID | 요구사항 | 출처 | 관련 TC | 중요도 |
|---|---|---|---|---|
| REQ-01 | 모든 Messaging API 엔드포인트는 Authorization: Bearer {channel access token} 헤더가 필수이며, 유효한 토큰이 없으면 401 Unauthorized를 반환한다. 권한이 없는 리소스는 403 Forbidden이다. | 레퍼런스 > Status codes, 각 엔드포인트 Request headers | AUTH-006, AUTH-008, AUTH-009, PGN-005 | 상 |
| REQ-02 | 채널 액세스 토큰은 4종이다. v2.1(사용자 지정 만료, 최대 30일, 채널당 30개, 초과 발급 요청은 거부), stateless(15분, 발급 수 무제한, 폐기 불가), short-lived(30일, 30개, 초과 시 가장 오래된 토큰 폐기), long-lived(무기한, 1개, 재발급 시 기존 토큰 무효). 만료된 토큰은 발급 수에 포함되지 않는다. | 문서 > Basics > Channel access token | AUTH-001, AUTH-003, AUTH-005, AUTH-006, AUTH-007, AUTH-008, SEC-001 | 상 |
| REQ-03 | stateless 토큰은 POST /oauth2/v3/token에 grant_type=client_credentials와 client_id·client_secret 또는 JWT assertion(생성 후 30분 내 만료)으로 발급하며 응답은 token_type/access_token/expires_in이다. 잘못된 채널 ID·secret·JWT → 400, 미등록 서명 키 → 404. v2.1 검증(GET /oauth2/v2.1/verify)은 만료·형식 오류·미존재 토큰에 400을 반환하고, 폐기(revoke)된 토큰은 더 이상 사용할 수 없다. | 레퍼런스 > Channel access token (Issue stateless / Issue v2.1 / Verify / Revoke) | AUTH-001, AUTH-002, AUTH-003, AUTH-004, AUTH-005, AUTH-006, AUTH-008 | 상 |
| REQ-04 | HTTP 상태 코드는 RFC 7231을 따르며 200 성공, 400 요청 문제, 401 토큰 무효, 403 권한 없음, 404 리소스 없음(프로필 미조회 포함), 409 동일 리트라이 키 수락됨, 410 더 이상 사용 불가, 413 요청 2MB 초과, 415 미지원 미디어 타입, 429 레이트리밋·월 한도 초과, 500 내부 오류로 정의된다. | 레퍼런스 > Common specifications > Status codes | CMN-001, CMN-003, CMN-004, CMN-005, CMN-006 | 상 |
| REQ-05 | 오류 응답 본문은 message(필수)와 details[](조건부; 각 항목 message·property)로 구성된다. 'The request body has X error(s)', 'Invalid reply token', 'The request body could not be parsed as JSON (line, column)', 'The content type, XXX, is not supported', 'Authentication failed due to the following reason: XXX', 'The API rate limit has been exceeded. Try again later.', 'You have reached your monthly limit.', 'Not found' 등이 정의된 메시지다. 모든 응답에 X-Line-Request-Id가 포함되고, 리트라이 키로 이미 수락된 요청에는 X-Line-Accepted-Request-Id가 추가된다. | 레퍼런스 > Error responses, Error messages, Response headers | AUTH-002, AUTH-009, CMN-001, CMN-002, CMN-003, CMN-004, RPL-002, PSH-004, PSH-008, PSH-009, IDM-001, WHS-002, RLM-001, SEC-003 | 상 |
| REQ-06 | 응답 메시지(POST /v2/bot/message/reply)는 웹훅으로 받은 replyToken으로 보내며 토큰은 1회만, 웹훅 수신 후 1분 이내에 사용해야 한다(초과 시 동작 보장 안 됨). 재전송 웹훅의 토큰은 원본 토큰이 미사용이고 이벤트 발생 20분 이내일 때만 유효하다. messages는 최대 5개. 무효·만료·사용된 토큰은 400 'Invalid reply token'. 성공 시 sentMessages[].id(조건부 quoteToken)를 반환하고, 오류 시 메시지는 발송되지 않는다. | 레퍼런스 > Send reply message | RPL-001, RPL-002, RPL-003, RPL-004, RPL-005, MSG-010 | 상 |
| REQ-07 | 푸시 메시지(POST /v2/bot/message/push)는 to(userId/groupId/roomId 1개), messages(최대 5개), notificationDisabled(기본 false), customAggregationUnits(최대 1개·30자·[a-zA-Z0-9_]), X-Line-Retry-Key(선택)를 받는다. 타 프로바이더 채널의 userId, 미참여 그룹·룸, 무효 메시지 객체, 무효 유닛명은 400. 계정 삭제·차단·미친구 사용자에게는 200이 반환되지만 미도달이며, 미친구라도 7일 내 1:1 메시지를 보낸 사용자에게는 발송 가능하다. | 레퍼런스 > Send push message | PSH-001, PSH-002, PSH-003, PSH-004, PSH-005, PSH-006, PSH-007, PSH-008, PSH-009, MSG-010 | 상 |
| REQ-08 | 멀티캐스트(POST /v2/bot/message/multicast)는 to에 userId 배열 최대 500개(그룹·룸 불가), messages 최대 5개를 받고 200과 빈 객체를 반환한다. 오류 시 누구에게도 발송되지 않는다. 삭제·차단·미친구·타채널 ID는 200이지만 미도달. 레이트리밋 200 req/s. | 레퍼런스 > Send multicast message | MLT-001, MLT-002, MLT-003, MLT-004, MSG-010 | 상 |
| REQ-09 | 브로드캐스트(POST /v2/bot/message/broadcast)는 모든 친구에게 발송하며 messages 최대 5개, 레이트리밋 60 req/h, 응답 200 빈 객체. 무효 메시지 객체 400, 동일 리트라이 키 409, 한도 초과 429. | 레퍼런스 > Send broadcast message | MLT-005, MLT-006, MSG-010 | 중 |
| REQ-10 | 내로우캐스트(POST /v2/bot/message/narrowcast)는 비동기로 202를 반환한다. 속성 조건 사용 시 타깃 리치 100명 미만이면 403, 최종 수신자 50명 미만이면 202 후 발송 단계에서 실패한다. 상태는 GET /v2/bot/message/progress/narrowcast?requestId=로 조회하며 phase는 waiting/sending/succeeded/failed, 실패 시 failedDescription·errorCode(1 내부 오류, 2 수신자 부족, 3 리트라이 충돌, 4 50명 미만 오디언스, 5 부분 발송 금지로 취소). acceptedTime 기준 14일(336시간) 경과 후 404, 무효 requestId 400, 내로우캐스트가 아닌 requestId 404. limit 객체(max/upToRemainingQuota/forbidPartialDelivery)로 발송 수를 제한한다. | 레퍼런스 > Send narrowcast message, Get narrowcast message status; 문서 > Send messages > Limit object | MLT-007, MLT-008, MLT-009, MLT-010 | 중 |
| REQ-11 | X-Line-Retry-Key(16진수 UUID)는 push/multicast/narrowcast/broadcast에서 지원된다. 같은 키의 요청이 이미 수락됐으면 24시간 내 재요청은 409와 X-Line-Accepted-Request-Id(원 요청 ID), message 'The retry key is already accepted'를 반환하며 push는 원 요청과 같은 sentMessages를 포함한다. 24시간이 지나면 같은 키도 신규 요청으로 처리돼 중복 발송된다. 미지원 엔드포인트에 키를 지정하면 400. 재시도 판단: 500·타임아웃만 재시도, 2xx·409·4xx는 재시도 금지. 재시도도 레이트리밋에 1회로 집계되며 지수 백오프를 권장한다. 키 없이 보낸 첫 요청은 재시도할 수 없다. | 레퍼런스 > Retrying an API request; 문서 > Retry failed API requests | RPL-007, IDM-001, IDM-002, IDM-003, IDM-004, IDM-005, IDM-006, IDM-007, IDM-008, RLM-006 | 상 |
| REQ-12 | messages 배열은 1~5개의 메시지 객체다. 텍스트 메시지 text는 최대 5000자이며 UTF-16 코드 유닛 단위로 센다(서로게이트 쌍 이모지는 2자, LINE 이모지 $는 대체 텍스트로 치환 후 계산). emojis 최대 20개, index가 $ 위치와 다르면 400. quickReply.items 최대 13개. sender.name 최대 20자('LINE' 등 금지어), sender.iconUrl은 HTTPS·PNG·1:1·1MB 이하·2000자. 빈 text는 400 'May not be empty', 미정의 type은 400. validate 엔드포인트(POST /v2/bot/message/validate/{reply\|push\|multicast\|narrowcast\|broadcast})로 발송 없이 같은 검증을 받을 수 있다(정상 200 빈 객체). | 레퍼런스 > Message objects (Common properties, Text message), Validate message objects; 문서 > Character counting in a text | CMN-002, RPL-004, MSG-001, MSG-002, MSG-003, MSG-004, MSG-005, MSG-006, MSG-007, MSG-008, MSG-009, MSG-010, MSG-011 | 상 |
| REQ-13 | 웹훅은 LINE 플랫폼이 채널에 설정된 HTTPS URL로 보내는 POST 요청이다. 헤더 x-line-signature(필드명 대소문자는 예고 없이 바뀔 수 있어 구분 없이 처리), 본문 destination(봇 userId, U[0-9a-f]{32})과 events[] (통신 확인용으로 빈 배열일 수 있음). 봇서버는 수신 후 200을 반환해야 하며, 장기간 수신 실패 시 플랫폼이 웹훅 전송을 중단할 수 있다. 플랫폼 IP는 비공개이므로 IP 제한 대신 서명 검증을 사용한다. | 레퍼런스 > Webhooks (Request headers/body, Response); 문서 > Receive messages | WHK-001, WHK-005, WHK-006, WHK-008, WHK-010, SEC-006 | 상 |
| REQ-14 | 서명 검증: 요청 본문 원문 문자열을 입력, 채널 secret을 키로 HMAC-SHA256 다이제스트를 Base64 인코딩한 값이 x-line-signature와 일치해야 한다. 불일치·누락 시 이벤트를 처리하지 않고 오류로 종료한다. 검증 전 본문·서명을 변형(역직렬화·이스케이프·치환)하면 안 된다. secret 재발급 시 기존 secret은 무효가 된다. | 문서 > Verify webhook signature; 레퍼런스 > Signature validation; Development guidelines | WHK-002, WHK-003, WHK-004, WHK-007, SEC-002, SEC-005, SEC-006 | 상 |
| REQ-15 | 웹훅 이벤트 공통 속성: type, mode(active/standby — standby면 replyToken이 없고 봇은 메시지를 보내면 안 됨), timestamp(발생 시각 ms, 재전송이어도 원 발생 시각), source(user/group/room; 그룹·룸의 userId는 message 이벤트에만), webhookEventId(ULID, 이벤트 고유 식별자), deliveryContext.isRedelivery(true/false). message 이벤트에는 replyToken, message.id, quoteToken, 인용 시 quotedMessageId가 포함된다. | 레퍼런스 > Webhook Event Objects > Common properties, Message event | RPL-001, RPL-006, PSH-002, WHK-001, WHK-008, WHK-009, WHK-012, WHS-005 | 상 |
| REQ-16 | 웹훅 재전송은 콘솔에서 활성화했을 때 봇서버가 2xx를 반환하지 않으면 비공개된 횟수·간격으로 다시 보낸다. 재전송 이벤트는 deliveryContext.isRedelivery만 true이고 webhookEventId·replyToken 등은 동일하다. 네트워크 사유로 같은 이벤트가 중복 도착할 수 있으므로 webhookEventId로 중복을 감지하고, 순서가 역전될 수 있으므로 timestamp로 맥락을 판단해야 한다. 재전송은 전달을 보장하지 않으며 급증 시 강제 비활성화될 수 있다. 전송 실패 원인·통계는 콘솔에서 확인한다. | 문서 > Receive messages > Redeliver a webhook that failed to be received; Check webhook error statistics | RPL-005, WHS-005, WHS-006, WHS-007 | 상 |
| REQ-17 | 웹훅 설정 API: PUT /v2/bot/channel/webhook/endpoint는 유효한 HTTPS URL(500자 이하)만 받고 무효 URL은 400, 반영까지 캐시로 최대 1분이 걸린다(1,000 req/min). GET …/endpoint로 설정값을 조회한다. POST /v2/bot/channel/webhook/test는 endpoint를 지정하면 그 URL을 검증 후 테스트 이벤트를 보내고, 미지정이면 설정된 URL로 보내며 설정이 없으면 404. 응답 success/timestamp/statusCode/reason(OK, COULD_NOT_CONNECT, REQUEST_TIMEOUT, ERROR_STATUS_CODE, UNCLASSIFIED)/detail. 60 req/h. | 레퍼런스 > Webhook settings (Set/Get webhook endpoint, Test webhook endpoint); 문서 > Verify webhook URL | WHK-006, WHS-001, WHS-002, WHS-003, WHS-004 | 중 |
| REQ-18 | 레이트리밋은 엔드포인트(HTTP 메서드가 다르면 별개)×채널 단위 토큰 버킷으로 적용되며 URL 파라미터·본문·IP와 무관하다. 초과 시 429 'The API rate limit has been exceeded. Try again later.'. 기본 2,000 req/s, multicast 200 req/s, broadcast·narrowcast·webhook test 60 req/h, 로딩 애니메이션 100 req/s, short-lived 토큰 발급 370 req/s, webhook endpoint 설정·조회 1,000 req/min. 월 메시지 한도(요금제별 무료 건수+추가 한도) 초과 시에도 429 'You have reached your monthly limit.'이며 한도는 GET /v2/bot/message/quota, 사용량은 GET …/quota/consumption으로 조회한다. 개발 가이드라인상 레이트리밋을 넘는 요청·부하 테스트·동일 사용자 대량 발송·무효 userId 요청은 금지다. | 레퍼런스 > Rate limits, Status codes, Get quota/consumption; 문서 > Development guidelines, Pricing | MLT-006, RLM-001, RLM-002, RLM-003, RLM-004, RLM-005, RLM-006 | 상 |
| REQ-19 | 팔로워 ID 목록(GET /v2/bot/followers/ids)은 verified·premium 계정만 사용 가능(아니면 403). limit은 기본 300, 최대 1000. 남은 ID가 있으면 next(continuation token, 24시간 후 만료)를 반환하고 없으면 생략한다. 다음 페이지는 start=next로 요청하며 무효·만료 토큰은 400. 삭제·차단·미동의 사용자는 제외되므로 userIds 수가 limit보다 적을 수 있다. | 레퍼런스 > Users > Get a list of users who added your LINE Official Account as a friend | PGN-001, PGN-002, PGN-003, PGN-004, PGN-005 | 중 |
| REQ-20 | 프로필(GET /v2/bot/profile/{userId})은 친구이거나 메시지를 보낸(차단 제외) 사용자만 조회 가능하며 응답은 displayName/userId와 조건부 language/pictureUrl/statusMessage다. 형식 오류 userId 400, 미존재·미동의·미친구·차단 404 'Not found'. 콘텐츠(GET api-data.line.me/v2/bot/message/{messageId}/content)는 contentProvider.type이 line일 때만 가능하고, 대용량 준비 중 202, 미존재 404, 사용자가 전송 취소한 메시지 410. 텍스트는 재조회 API가 없다. 콘텐츠는 일정 기간 후 삭제된다. | 레퍼런스 > Users > Get profile; Getting content > Get content | CMN-009, PGN-006, PGN-007 | 중 |
| REQ-21 | 로딩 애니메이션(POST /v2/bot/chat/loading/start)은 chatId(userId)와 loadingSeconds(5~60의 5 단위, 기본 20)를 받아 202를 반환하며, 채팅방을 보고 있지 않거나 미친구·차단·삭제 사용자에게는 202지만 표시되지 않는다. 무효 초·무효 userId·그룹/룸 지정은 400. 읽음 처리(POST /v2/bot/chat/markAsRead)는 무효 markAsReadToken에 400. 엔드포인트 경로에 끝 슬래시 등을 붙이면 동작이 보장되지 않고, 본문 내 URL은 UTF-8 퍼센트 인코딩해야 한다. | 레퍼런스 > Display a loading animation, Mark messages as read, Other common specifications | CMN-006, MSG-011, PGN-008 | 하 |
| REQ-22 | 비파괴 변경 원칙: 신규 엔드포인트, 요청의 선택 파라미터·필드·헤더 추가, 응답 필드·헤더 추가, 웹훅 이벤트 속성 추가, 속성 순서 변경, 열거값 추가, 공백·줄바꿈 변화는 사전 고지 없이 이루어질 수 있다. 봇서버는 미지의 필드·이벤트 타입·열거값을 무시하고 정상 동작해야 하며, 요청·웹훅 로그(request id, 시각, 메서드, 경로, 상태 코드, 서명)를 보관해야 한다. | 문서 > Development guidelines (Recommended matters) | CMN-007, CMN-008, WHK-011, SEC-004 | 중 |

### 2.2 질의사항

공개 문서만으로 기대결과를 확정할 수 없는 항목 13건. 해당 TC의 기대결과는 'Qn 회신 후 확정'으로 표기하고, 수행 시 실제 응답(상태 코드·본문·헤더)을 실측·메모 열에 기록해 판정한다. 확인 결과는 케이스 파일의 '질의사항' 시트에 남긴다.

| ID | 질의 | 영향 | 회신 전 처리 | 영향 TC |
|---|---|---|---|---|
| Q01 | 리트라이 키 형식 검증 범위: UUID 형식이 아닌 문자열('abc'), 대문자 UUID, 중괄호 포함 UUID, 빈 문자열을 X-Line-Retry-Key에 넣었을 때 400인지 그대로 수락되는지, 수락되면 멱등 키로 동작하는지 | 멱등성·재시도 TC | 모의 서버가 아닌 테스트 채널에 1회씩 보내 상태 코드·message 기록 후 판정 | IDM-006 |
| Q02 | 같은 리트라이 키로 본문(수신자·메시지 내용)을 바꿔 재요청하면 409(키 기준 차단)인지 신규 처리인지. 문서는 '예상대로 동작하지 않을 수 있음'만 명시 | 멱등성 TC, 운영 리스크 | 현재 동작(상태 코드, accepted-request-id, 실제 도달 메시지) 기록 후 판정 | IDM-004 |
| Q03 | multicast to 배열 경계: 빈 배열, 같은 userId 중복, 유효 ID와 타채널 ID 혼합일 때 400인지 부분 발송인지, 중복이 500 한도 계산에 포함되는지 | 다중 발송 TC | 현재 동작(상태 코드, details[].property, 도달 건수) 기록 후 판정 | MLT-002, MLT-003 |
| Q04 | messages 배열 경계의 오류 표기: 빈 배열([])과 6개 초과 시 message·details[].property 값(messages 인지 messages[5] 인지), 5개 중 1개만 무효일 때 property 인덱스 표기 | 메시지 객체 검증 TC, 자동화 assertion | validate 엔드포인트로 현재 응답 본문을 기록해 assertion 기준으로 채택 | RPL-004, MSG-004 |
| Q05 | Authorization 헤더 변형 처리: 스킴 소문자('bearer'), 공백 2개, 스킴 없이 토큰만, 빈 토큰, 헤더 자체 누락일 때 모두 401인지, message가 'Authentication failed due to the following reason: XXX' 형식인지 | 인증 TC | 조회성 엔드포인트(GET /v2/bot/info)로 현재 동작 기록 후 판정 | AUTH-009 |
| Q06 | Content-Type 처리: 헤더 누락, text/plain으로 JSON 전송, application/json; charset=utf-8, multipart일 때 400/415 중 무엇이고 'The content type, XXX, is not supported' 메시지가 나오는지 | 공통 계약 TC | validate 엔드포인트로 현재 동작 기록 후 판정 | CMN-004 |
| Q07 | reply token 만료 경계: 수신 후 59초/60초/61초/20분 시점의 실제 거부 여부와 오류 message. 문서는 '1분 이후 동작 보장 안 됨'으로 비결정을 명시하고 '시간 제한에 의존하지 말 것'을 권고 | 응답 메시지 TC(비결정 영역) | 각 시점 3회 측정해 결과 분포를 기록하고 Pass/Fail 대신 '관찰'로 판정, 설계 권고(즉시 사용)로 처리 | RPL-003 |
| Q08 | 429 응답의 세부: Retry-After 헤더 포함 여부, 본문 details 유무, 토큰 버킷 보충 속도(초당 몇 건 회복), 월 한도 429와 레이트리밋 429의 message 외 구분자 | 레이트리밋 TC, 클라이언트 백오프 설계 | 가이드라인상 실플랫폼에 한도 초과 요청 금지. 한도가 낮은 webhook test(60/h)에서 1회 초과만 관찰해 헤더·본문 기록 | RLM-001, RLM-002, RLM-005 |
| Q09 | 웹훅 재전송의 횟수·간격(비공개)과 봇서버 응답 타임아웃 기준 초. 타임아웃으로 간주되는 지연 시간과 재전송 종료 후 콘솔 통계 반영 시점 | 웹훅 재전송 TC | 봇서버 지연을 5/15/30초로 바꿔 콘솔 통계(reason)와 재전송 도착 시각을 기록해 역도출 | WHS-003, WHS-005 |
| Q10 | followers/ids의 limit 범위 외 값(0, 음수, 1001, 문자열)과 start에 임의 문자열 지정 시 400인지 기본값·최대값으로 보정되는지, 오류 property 값 | 페이지네이션 TC | 현재 동작 기록 후 판정. verified 계정이 아니면 403으로 Blocked 처리 | PGN-002, PGN-004 |
| Q11 | text 길이 경계의 오류 표기: 5001자(UTF-16 유닛) 초과 시 details[].property·message, LINE 이모지 대체 텍스트 치환 후 길이가 5000을 넘는 경우의 처리, 4999자 + 서로게이트 이모지 1개(=5001유닛)의 판정 | 메시지 객체 검증 TC | validate 엔드포인트로 현재 응답 기록 후 판정 | MSG-001, MSG-002, MSG-003 |
| Q12 | 선택 파라미터 타입·조합 검증: notificationDisabled에 문자열 'true'/숫자 1, customAggregationUnits에 빈 배열·2개, to에 groupId + customAggregationUnits 조합일 때 400인지 무시되는지 | 푸시 메시지 TC | validate가 아닌 push 본문 검증이므로 테스트 사용자(U1)에게 1회씩 보내 현재 동작 기록 | PSH-007, PSH-008 |
| Q13 | webhook test 엔드포인트의 endpoint 파라미터에 http://(비HTTPS), 501자 URL, 해석 불가 도메인, 포트 포함 URL을 지정했을 때의 상태 코드(400 vs 200+success=false)와 reason 값 | 웹훅 설정 TC | 현재 동작 기록 후 판정. 60 req/h 한도 내에서 수행 | WHS-004 |

## 3. 테스트 전략

### 3.1 테스트 중점

- **중복 발송 방지(멱등성)**: 500·타임아웃 뒤 재시도에서 메시지가 2건 가지 않아야 한다. 리트라이 키의 409·X-Line-Accepted-Request-Id·24시간 만료를 상태 전이로 설계하고, 클라이언트 재시도 정책(상태 코드별)을 모의 서버로 검증
- **웹훅 보안·신뢰성**: 서명 검증은 원문 바이트로, 불일치·누락은 거부. 재전송 시 webhookEventId로 중복 제거, timestamp로 순서 판단, 200은 즉시 반환(비동기 처리). 서명 미검증은 위조 웹훅을 처리하는 S1 결함
- **계약 경계**: 문서에 숫자가 있는 모든 한도(5개 메시지, 5000 UTF-16 유닛, 500 userId, 13 quick reply, 20 이모지, 30자 유닛명, limit 1000, 500자 URL, 15분·30일·24시간·14일)를 3점 경계값으로 검증
- **발송 성공 ≠ 도달**: 차단·탈퇴·미친구 사용자에게 200이 반환되지만 미도달인 플랫폼 특성을 결정 테이블로 정리하고, 발송 결과 해석 규칙을 클라이언트 설계에 반영

### 3.2 테스트 유형

| 유형 | 내용 | TC 그룹 |
|---|---|---|
| 계약(스키마) | 성공·오류 응답 필드·타입, 헤더, Content-Type, 미지 필드 내성 | CMN, AUTH |
| 인증·권한 | 토큰 발급·검증·폐기·만료, 헤더 변형, 401/403 | AUTH, PGN-005, SEC |
| 경계값 | 메시지 수·길이(UTF-16)·수신자 수·quickReply·이모지·유닛명·limit·URL 길이·시간 한도 | MSG, RPL, PSH, MLT, PGN, WHS |
| 멱등성·재시도 | 리트라이 키 409·24h·본문 불일치, 상태 코드별 재시도 | IDM, RPL-007 |
| 상태 전이 | 리트라이 키 요청 상태, 웹훅 전달·재전송 상태, narrowcast phase, 토큰 수명 | IDM, WHS, MLT, AUTH |
| 웹훅 보안·신뢰성 | 서명 검증, 헤더 대소문자, 빈 events, 중복·순서, 비동기 응답 | WHK, WHS |
| 레이트리밋·쿼터 | 429 두 종류, 토큰 버킷, 채널·메서드 단위, 월 한도 조회 | RLM, MLT-006 |
| 페이지네이션·조회 | limit 경계, next 순회, 토큰 만료, 프로필·콘텐츠 상태 코드 | PGN |
| 보안·운영 | 토큰·secret 교체 영향, 민감정보 노출, 로그 마스킹, 상수 시간 비교 | SEC |
| 회귀(스모크) | stateless 토큰 발급 → bot info → validate → push 1건 → 웹훅 수신·서명 | AUTH-001, CMN-001, MSG-009, PSH-001, WHK-001/002 |

### 3.3 설계 기법 — 규칙의 형태에 기법을 맞춤

| 규칙의 형태 | 기법 | 적용한 곳 |
|---|---|---|
| 조건 여러 개가 AND로 결합되어 응답이 정해짐 | 결정 테이블 | 푸시 발송 결과 판정(토큰 × 메시지 × 대상 존재 × 수신 가능 → 401/400/200 미도달/200 도달, 3.4), 리트라이 키 처리 판정(지원 엔드포인트 × 키 × 수락 이력, 3.5) |
| 숫자 한도가 명시됨 | 경계값 분석(3점) | messages 5개, text 5000 유닛, multicast 500, quickReply 13, emojis 20, 유닛명 30자, limit 1000, URL 500자, loadingSeconds 5~60, 토큰 15분·24시간·14일. ±1 단위(문자·개수) 또는 ±10초(시간) |
| 요청·이벤트가 시간에 따라 상태를 바꿈 | 상태 전이 | 리트라이 키 요청 상태(3.6), 웹훅 전달·재전송 상태(3.7), narrowcast phase(waiting→sending→succeeded/failed), 토큰 발급→유효→만료/폐기 |
| 입력을 동작이 같은 집합으로 나눌 수 있음 | 동등 분할 | 메시지 타입(text/sticker/image/location/template/flex), 토큰 4종, 대상 유형(user/group/room), 429 두 종류(레이트리밋/월 한도), 재시도 가능(500·타임아웃) vs 불가(2xx·409·4xx) |
| 독립 변수 여러 개의 조합을 전수 검증하기엔 많음 | 페어와이즈 | 발송 엔드포인트(4) × 메시지 타입(6) × notificationDisabled(2) = 48조합 → 10조합(3.8, TC-MSG-010) |
| 문서에 없지만 구현에서 자주 틀리는 지점 | 오류 추정 | 재직렬화 후 서명 계산, 헤더 이름 대소문자, 특수문자 본문 서명, 같은 키·다른 본문, 첫 요청 키 누락, 동기 처리로 인한 타임아웃, 재전송 순서 역전, 24h 직후 중복 |

### 3.4 푸시 발송 결과 판정 결정 테이블

| 토큰 유효 | 메시지 객체 유효 | 대상 ID가 채널 내 존재 | 대상 수신 가능(친구·미차단) | 결과 |
|---|---|---|---|---|
| N | - | - | - | 401, 미발송 |
| Y | N | - | - | 400 'The request body has X error(s)', 미발송 |
| Y | Y | N | - | 400 'Failed to send messages', 미발송 |
| Y | Y | Y | N | 200 + sentMessages, 그러나 미도달(차단·탈퇴·미친구) |
| Y | Y | Y | Y | 200 + sentMessages, 도달 |

4조건 16조합 중 선행 조건이 N이면 후행 조건이 무의미하므로 5행으로 축약했다. 핵심은 4행 — **200이 도달을 뜻하지 않는다**는 점이며, 클라이언트는 200을 '수락'으로만 해석하고 도달 여부는 별도 지표(콘솔 통계·사용자 피드백)로 본다.

### 3.5 리트라이 키 처리 판정 결정 테이블

| 지원 엔드포인트 | X-Line-Retry-Key 포함 | 24h 내 같은 키 수락 이력 | 결과 |
|---|---|---|---|
| N | Y | - | 400, 미발송(reply 등) |
| Y | N | - | 신규 처리. 이후 재시도 불가 |
| Y | Y | N | 신규 처리(200/202), 키 24h 보관 |
| Y | Y | Y | 409 + X-Line-Accepted-Request-Id, 미발송(push는 원 sentMessages 반환) |

### 3.6 리트라이 키 요청 상태 전이

| 현재 상태 | 이벤트 | 다음 상태 | 검증 포인트 |
|---|---|---|---|
| 미요청 | 키 포함 요청 → 200 | 수락됨(키 24h 보관) | sentMessages·X-Line-Request-Id 저장 |
| 미요청 | 키 포함 요청 → 500/타임아웃 | 미확정 | 플랫폼이 수락했을 수도 있음 → 같은 키로 재시도 |
| 미확정 | 같은 키 재시도 → 200 | 수락됨 | 최초 수락. 1건만 도달 |
| 미확정 | 같은 키 재시도 → 409 | 수락됨 | 이전 요청이 수락됐었음. X-Line-Accepted-Request-Id로 원 요청 식별, 중복 없음 |
| 수락됨 | 같은 키 재요청(24h 내) | 수락됨 | 409, 도달 1건 유지 |
| 수락됨 | 24h 경과 후 같은 키 요청 | 신규 수락(중복 발송) | 200. 클라이언트 재시도 창을 24h보다 짧게 제한 |
| 미요청 | 키 없는 요청 → 500/타임아웃 | 재시도 불가 | 키를 넣어 재요청하면 신규 요청 → 중복 위험 |
| 미요청 | 요청 → 4xx(400/401/429) | 거부 | 재시도해도 결과 불변. 429만 백오프 후 재개 |

### 3.7 웹훅 전달 상태 전이

| 현재 상태 | 이벤트 | 다음 상태 | 검증 포인트 |
|---|---|---|---|
| 이벤트 발생 | 플랫폼 전송 | 전송 중 | x-line-signature 포함 POST |
| 전송 중 | 봇서버 2xx | 전달 완료 | isRedelivery=false |
| 전송 중 | 비2xx / 타임아웃 / 연결 실패 (재전송 OFF) | 유실 | 콘솔 통계에 reason 기록 |
| 전송 중 | 비2xx / 타임아웃 / 연결 실패 (재전송 ON) | 재전송 대기 | 횟수·간격 비공개(Q09) |
| 재전송 대기 | 재전송 → 봇서버 2xx | 전달 완료 | isRedelivery=true, webhookEventId·replyToken 동일 |
| 재전송 대기 | 재전송 횟수 소진 | 유실 | 전달 비보장. 급증 시 강제 비활성화 가능 |
| 전달 완료 | 네트워크 사유 중복 도착 | 중복 수신 | webhookEventId로 1회만 처리 |
| 전달 완료 | 후속 이벤트가 먼저 도착한 뒤 재전송 도착 | 순서 역전 | timestamp(원 발생 시각)로 정렬 |

### 3.8 메시지 타입 × 엔드포인트 × 알림 페어와이즈

발송 엔드포인트 4종(reply/push/multicast/broadcast) × 메시지 타입 6종 × notificationDisabled 2값의 전수 48조합 대신, 모든 2-요인 쌍이 최소 1회 등장하는 10조합을 선정했다(TC-MSG-010). narrowcast는 오디언스 조건이 별도 축이라 제외하고 MLT 그룹에서 다룬다.

| # | 엔드포인트 | 메시지 타입 | notificationDisabled |
|---|---|---|---|
| 1 | reply | text | false |
| 2 | reply | flex | true |
| 3 | push | sticker | true |
| 4 | push | template(buttons) | false |
| 5 | multicast | image | false |
| 6 | multicast | text | true |
| 7 | broadcast | location | true |
| 8 | broadcast | flex | false |
| 9 | push | location | false |
| 10 | reply | image | true |

## 4. 테스트 환경 및 데이터

### 4.1 환경

| 항목 | 내용 |
|---|---|
| 플랫폼 | LINE Messaging API (https://api.line.me, https://api-data.line.me). 공개 문서 조회일 2026-10-25 |
| 채널 | CH1 메인 테스트 채널(Webhook·재전송 ON) / CH2 타 프로바이더 채널. 콘솔 Admin 권한 |
| 계정 | 테스트 LINE 계정 3개(U1 친구, U2 차단, U3 미친구 발신), 그룹 2개(G1 참여, G2 탈퇴) |
| 봇서버 | B1: 로컬 FastAPI + ngrok HTTPS. 서명 검증·원문 로그·중복 제거·응답 모드 전환(200/500/지연/종료) |
| 모의 서버 | MK1: LINE API 응답을 흉내 내는 로컬 서버. 429·500·타임아웃·409·월 한도·미지 필드·500건 수신자 시나리오 |
| 클라이언트 | Python 3.12, httpx(요청·응답 로그, 재시도·백오프 모듈), pytest. 토큰·secret은 환경 변수 |
| 도구 | LINE Developers Console(Verify·통계·토큰 재발급), LINE 앱(도달 확인), 요청·응답 로그 파일(증적) |

### 4.2 테스트 데이터

채널·계정·서버·토큰·샘플은 케이스 파일의 '테스트 데이터' 시트에 조건과 사용 TC를 정리했고, 수행 전 준비 완료 여부(Y/N)와 실제 값(비밀값 제외)을 기록한다. 핵심 데이터는 다음과 같다.

| 구분 | ID | 조건 | 사용 TC |
|---|---|---|---|
| 채널 | CH1 | 개인 프로바이더의 Messaging API 채널. Webhook 사용 ON·재전송 ON, 채널 ID·secret·long-lived 토큰 확보, assertion 서명 키 등록. 월 무료 메시지 한도 내 운영 | 대부분의 TC |
| 채널 | CH2 | 다른 프로바이더 아래 두 번째 채널(userId가 CH1과 다름). verified 아님 | TC-PSH-004, TC-MLT-003, TC-RLM-003, TC-PGN-005 |
| 계정 | U1 | 본인 LINE 계정. CH1 친구, 프로필 동의, 알림 허용. userId는 웹훅 source.userId에서 확보 | 발송·웹훅 TC 전반 |
| 계정 | U2 | 보조 계정. CH1 친구 추가 후 차단(필요 시 해제). 그룹 G1 구성원 | TC-PSH-003, TC-MLT-001/004, TC-WHK-009, TC-PGN-006 |
| 계정 | U3 | 보조 계정. CH1을 친구 추가하지 않고 1:1 메시지를 보낸 지 7일 이내 | TC-PSH-006, TC-PGN-006 |
| 서버 | B1 | 로컬 FastAPI + ngrok HTTPS. 서명 검증, 원문 body·헤더·IP 로그, webhookEventId 중복 제거, 응답 모드(200/500/지연 5·15·30초/종료)를 설정으로 전환 | 웹훅 TC 전반 |
| 서버 | MK1 | LINE API 응답을 흉내 내는 로컬 서버. 429·500·타임아웃·409·월 한도 429·필드 추가·to 500건 시나리오를 재현. 가이드라인상 실플랫폼 부하·무효 ID 요청 금지를 대체 | TC-CMN-008, TC-MLT-002/006/010, TC-IDM-007/008, TC-RLM-001/003/005/006 |
| 토큰 | T1 | 콘솔에서 발급. 기본 인증용 | 기본 |
| 토큰 | T2 | POST /oauth2/v3/token으로 발급(15분) | TC-AUTH-001, 007, 008 |
| 토큰 | T3 | JWT assertion으로 발급(token_exp 3600) | TC-AUTH-003~006 |
| 샘플 | MS1 | ASCII 0/1/4999/5000/5001자, '🍎' 2500/2501개, 한글 5000자, 결합 이모지 625/626개 | TC-MSG-001/002 |
| 키 | RK1~RK7 | uuid4()로 생성한 소문자 하이픈 UUID. 케이스마다 새 값 | TC-IDM 그룹, 발송 TC |

## 5. 실행 계획

### 5.1 수행 순서

| 차수 | 대상 | 내용 | 비고 |
|---|---|---|---|
| 0차 | 환경 검증 | stateless 토큰 발급 → GET /v2/bot/info → 콘솔 Verify로 B1 수신 확인(스모크 6건) | 실패 시 이후 차수 Blocked |
| 1차 | 무발송 TC 69건 | 인증·공통 계약·validate 기반 메시지 검증·웹훅 수신/서명·모의 서버 기반 재시도/429·조회 API 순으로 수행. 발송 없이 계약을 먼저 고정 | P1 우선, 질의 항목은 현재 동작 기록 |
| 2차 | 발송 TC 27건 | 테스트 계정에게만 발송. reply 토큰은 수신 즉시 사용, 리트라이 키 케이스는 도달 건수를 앱에서 확인. 1일 발송 상한 50건으로 월 무료 한도 보호 | 같은 사용자에게 연속 대량 발송 금지 |
| 3차 | 장기·한도 TC 6건 | stateless 15분 만료, v2.1 30개 한도, 리트라이 키 24시간, continuation token 24시간, webhook test 60/h 1회 초과, narrowcast 14일 상태 창 | 타이머·캘린더로 시각 기록, 대기 중 1차 잔여 수행 |
| 재검증 | Fail TC | 플랫폼 결함은 수정 전제가 없으므로 재현율 확인 목적의 재수행 3회. 봇서버·클라이언트 결함은 수정 후 재검증 | 재현율·X-Line-Request-Id를 결함 리포트에 기록 |

### 5.2 발송·한도 통제 규칙

- 발송 대상은 테스트 계정(U1~U3)·테스트 그룹(G1)으로 한정하고, broadcast는 친구가 테스트 계정뿐임을 확인한 뒤 수행한다
- 레이트리밋 초과는 실플랫폼에서 **webhook test(60/h) 1회 초과 관찰**만 허용하고, 나머지 429·500·타임아웃 시나리오는 MK1에서 수행한다(개발 가이드라인 준수)
- 무효 userId·타채널 ID·미참여 그룹 요청은 케이스당 1회로 제한한다
- 모든 발송 요청에 리트라이 키를 넣고, 케이스가 끝나면 키를 재사용하지 않는다(24시간 보관으로 다음 케이스 오염 방지)
- 토큰·채널 secret·개인 키는 환경 변수로만 다루고 케이스 파일·로그·증적에 평문으로 남기지 않는다

### 5.3 우선순위 정의

| 우선순위 | 기준 | TC 수 |
|---|---|---|
| P1 | 중복 발송·메시지 유실·위조 웹훅 처리·인증 우회로 이어질 수 있는 경로, 문서에 명시된 핵심 계약(상태 코드·오류 포맷·한도) | 37 |
| P2 | 계약 경계·조합, 재시도·재전송 복구 경로, 조회·페이지네이션 정확성 | 46 |
| P3 | 오류 문구·선택 파라미터·드문 조건, 코드 리뷰성 항목 | 19 |

### 5.4 결과 판정

- **Pass / Fail / Blocked / N/A**를 케이스 시트의 결과 열에 기록. Blocked는 사전 조건 미충족(verified 계정 아님, 보조 계정 미확보, 모의 서버 미구현), N/A는 수행 시점에 기능·엔드포인트가 존재하지 않는 경우
- 질의(Qn) 연결 TC는 실측·메모 열에 실제 상태 코드·본문·헤더를 먼저 기록하고, 문서·콘솔 안내로 근거가 확인되면 그 기준으로 판정한다. 근거가 없으면 '현재 동작 기록'으로 두고 Fail 처리하지 않는다
- 문서상 비보장 항목(reply token 1분 경계, 재전송 횟수·간격)은 '관찰'로 기록하고 Pass/Fail을 매기지 않는다
- 결함은 **플랫폼 / 봇서버 / 클라이언트** 중 어디 책임인지 분류해 '결함 리포트' 시트에 등록하고 TC의 결함 ID 열에 연결한다. 모든 Fail은 요청·응답 전문(X-Line-Request-Id 포함, 토큰 마스킹)을 첨부한다

### 5.5 결함 심각도

| 심각도 | 기준 | 예시 |
|---|---|---|
| S1 | 중복 발송, 메시지 유실, 서명 미검증으로 위조 웹훅 처리, 토큰·secret 노출 | 같은 리트라이 키 재요청이 200으로 2건 도달, 서명 불일치 웹훅을 처리해 reply 발송 |
| S2 | 계약 위반(상태 코드·오류 포맷 불일치), 경계값 오판정, 재시도 정책 오동작 | 4xx에 재시도, 5001 유닛 텍스트가 200, webhookEventId 중복 처리 |
| S3 | 오류 메시지 문구·필드명 불일치, 우회 가능한 클라이언트 이상 | details.property 경로 표기 차이, 로그 형식 누락 |
| S4 | 개선 제안, 사소한 표기 | 로그 시각 포맷 |

### 5.6 완료 기준

- P1 TC 100% 수행(Blocked 포함 시 사유 기록), P2 90% 이상 수행
- S1·S2 결함 0건 또는 각 결함에 재현 절차·재현율·X-Line-Request-Id·증적이 갖춰진 리포트 존재
- 질의사항 Q01~Q13 전부 '확인 결과' 기록
- 요약 시트의 요구사항 커버리지에서 연결 TC 수 0인 요구사항 없음
- 월 무료 메시지 한도를 초과하지 않음(quota/consumption으로 수행 전후 확인)

### 5.7 산출물

- 테스트 계획서(본 문서, Markdown)
- 테스트 케이스(xlsx): 요약(자동 집계) · 테스트케이스 · 테스트 데이터 · 질의사항 · API 체크리스트 · 결함 리포트
- 증적: 요청·응답 로그(토큰 마스킹), 봇서버 수신 로그, 콘솔 통계 스크린샷(파일명을 TC·결함 ID와 일치)
- 결과 보고(수행 완료 후 요약 시트 기준으로 작성)

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 개발 가이드라인 위반(한도 초과·부하·무효 ID 반복) | 채널 제재, 테스트 중단 | 429·500·타임아웃·500건 수신자 시나리오는 MK1로 대체, 실플랫폼 초과 관찰은 1회, 무효 ID 요청은 케이스당 1회 |
| 월 무료 메시지 한도 소진 | 발송 TC Blocked | 1일 발송 상한 50건, validate로 1차 검증 후 발송, quota/consumption 수행 전후 기록 |
| verified/premium 계정 아님 | PGN-001~004 Blocked | 403 확인으로 PGN-005만 수행, 나머지는 사내 환경 항목으로 표시 |
| 문서상 비보장·비공개 동작 | Pass/Fail 판정 불가 | '관찰'로 기록(Q07·Q09), 설계 권고(즉시 사용·멱등 수신)로 전환 |
| 웹훅 재전송 발생 시점 예측 불가 | WHS-005~007 대기 시간 길어짐 | 재전송 ON 상태로 1차 수행 중 병행 대기, 콘솔 통계로 발생 여부 확인 |
| 보조 계정·그룹 확보 어려움 | U2·U3·G1·G2 의존 TC Blocked | 가족·지인 계정 협조 또는 두 번째 기기, 불가 시 Blocked 사유 기록 |
| 문서 변경 | 요구사항 근거 불일치 | 조회일 명시, 불일치 발견 시 요구사항 갱신 및 변경 이력 기록 |

## 7. 테스트 케이스 요약

| 대분류 | ID 접두 | TC 수 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| 인증·토큰 | TC-AUTH | 9 | 5 | 3 | 1 |
| 공통 계약 | TC-CMN | 9 | 2 | 5 | 2 |
| 응답 메시지 | TC-RPL | 7 | 3 | 3 | 1 |
| 푸시 메시지 | TC-PSH | 9 | 3 | 5 | 1 |
| 다중 발송 | TC-MLT | 10 | 3 | 4 | 3 |
| 멱등성·재시도 | TC-IDM | 8 | 4 | 3 | 1 |
| 메시지 객체 검증 | TC-MSG | 11 | 5 | 4 | 2 |
| 웹훅 수신·서명 | TC-WHK | 12 | 5 | 5 | 2 |
| 웹훅 설정·재전송 | TC-WHS | 7 | 2 | 4 | 1 |
| 레이트리밋·쿼터 | TC-RLM | 6 | 1 | 3 | 2 |
| 조회·페이지네이션 | TC-PGN | 8 | 2 | 5 | 1 |
| 보안·운영 | TC-SEC | 6 | 2 | 2 | 2 |
| 합계 |  | 102 | 37 | 46 | 19 |

설계 근거별: 요구사항 83건 · 리스크 기반 16건 · 추가 검증 3건 / 실행 구분별: 무발송 69건 · 발송 27건 · 장기·한도 6건

## 8. 자동화 전략

본 설계의 102건 중 대부분은 '요청 → 응답'이 결정적인 API 계약이므로 자동화 적합도가 높다. 어떤 케이스를 어느 계층에서 돌릴지 정해 두면 회귀 비용이 줄고, LINE 앱·콘솔에서 사람이 확인해야 하는 영역이 분명해진다. 케이스 시트의 '자동화 구분' 열과 요약 시트의 구분별 집계가 이 장의 근거다.

### 8.1 선정 기준

- **결정성**: 상태 코드·오류 본문·헤더가 문서로 확정된 케이스는 API 1순위. 질의(Qn) 연결 케이스는 응답을 기록해 기대값이 확정된 뒤 assertion으로 승격
- **발송 없이 검증 가능한가**: validate 엔드포인트·토큰 API·조회 API·모의 서버 케이스는 월 한도를 쓰지 않으므로 PR마다 돌릴 수 있다
- **도달 확인 필요 여부**: 메시지가 실제로 사용자 화면에 표시됐는지는 API로 알 수 없다(200 ≠ 도달). 이 확인이 필요한 케이스는 UI(앱 확인)로 남긴다
- **시간·운영 통제**: 24시간·14일 경과, 콘솔 재발급, 코드 리뷰는 수동

### 8.2 계층 배치(테스트 피라미드)

| 계층 | TC 수 | 비율 | 대상 | 도구·전제 |
|---|---|---|---|---|
| API | 67 | 66% | 토큰 발급·검증·폐기, 공통 계약(스키마·오류 포맷), validate 기반 메시지 경계, 리트라이 키 409 계약, 웹훅 서명·중복 제거(봇서버 로컬 주입), 모의 서버 기반 재시도·429 정책, 조회·페이지네이션 | pytest + httpx, 테스트 채널 CH1, 봇서버 B1(테스트 클라이언트로 직접 호출), 모의 서버 MK1(respx 또는 로컬 FastAPI). 데이터 주도(parametrize), TC ID 1:1 |
| UI | 22 | 22% | 실제 발송 후 LINE 앱 도달·렌더링·알림 확인, 콘솔 Verify·토큰 재발급·secret 재발급, 차단·그룹 조작이 필요한 이벤트 | LINE 앱(테스트 계정 기기) + Developers Console. API 호출은 자동, 확인만 사람이 수행하는 반자동 |
| 수동 | 13 | 13% | 15분·24시간·14일 경과, 30개 토큰 한도, 재전송 대기, 한도 1회 초과 관찰, 코드·설정 리뷰 | 타이머·캘린더, 코드 리뷰 체크리스트. 릴리스 전 또는 분기 1회 |

대분류별 배치:

| 대분류 | API | UI | 수동 |
|---|---|---|---|
| 인증·토큰 | 7 | 0 | 2 |
| 공통 계약 | 9 | 0 | 0 |
| 응답 메시지 | 3 | 2 | 2 |
| 푸시 메시지 | 4 | 4 | 1 |
| 다중 발송 | 5 | 4 | 1 |
| 멱등성·재시도 | 3 | 4 | 1 |
| 메시지 객체 검증 | 10 | 1 | 0 |
| 웹훅 수신·서명 | 9 | 3 | 0 |
| 웹훅 설정·재전송 | 5 | 0 | 2 |
| 레이트리밋·쿼터 | 5 | 0 | 1 |
| 조회·페이지네이션 | 5 | 2 | 1 |
| 보안·운영 | 2 | 2 | 2 |

### 8.3 API 계층 설계

Messaging API 호출은 '요청(헤더·본문) → 상태 코드·헤더·본문'으로 닫히는 순수 함수에 가깝다. 세 가지 장치로 설계 문서와 코드를 1:1로 잇는다.

- **validate를 1차 게이트로**: 메시지 객체 경계(MSG 그룹)는 모두 `POST /v2/bot/message/validate/{type}`으로 검증한다. 발송이 없어 월 한도를 쓰지 않고, TC-MSG-008로 validate와 실제 발송의 400 본문이 같음을 먼저 확인해 근거를 만든다
- **오류 응답 공통 스키마 검증**: 모든 4xx 케이스에 `message: str` 필수, `details[].property`가 요청 JSON 경로와 일치, `X-Line-Request-Id` 존재를 공통 assertion으로 건다(TC-CMN-002의 자동화 형태)
- **리트라이 키 멱등성**: 같은 키로 2회 호출해 첫 응답 200, 둘째 409, `X-Line-Accepted-Request-Id == 첫 X-Line-Request-Id`, push는 `sentMessages` 동일을 검증한다. 발송 1건이 필요하므로 나이틀리에만 포함
- **웹훅은 봇서버를 직접 호출**: 저장한 원문 웹훅 샘플(MS3)에 유효·변조·누락 서명을 붙여 B1에 POST하고 응답 코드와 처리 여부(저장소·reply 호출 횟수)를 검증한다. LINE 플랫폼을 거치지 않으므로 결정적이고 빠르다
- **클라이언트 정책은 모의 서버로**: 500→200, 타임아웃→200, 409, 429(두 종류)를 MK1이 순서대로 돌려주고 클라이언트의 요청 횟수·헤더·간격을 MK1 로그로 assert한다(IDM-007, RLM 그룹)
- **비밀값**: 토큰·secret은 환경 변수, 로그는 Authorization 마스킹(TC-SEC-004가 이를 검증)

예시 — TC-MSG-001(text 길이)과 TC-MSG-004(messages 수)를 하나의 파라미터 테이블로:

```python
@pytest.mark.parametrize("tc_id, messages, expected_status, expected_property", [
    ("TC-MSG-001-1", [text("a" * 4999)], 200, None),
    ("TC-MSG-001-2", [text("a" * 5000)], 200, None),
    ("TC-MSG-001-3", [text("a" * 5001)], 400, "messages[0].text"),
    ("TC-MSG-001-5", [text("")],         400, "messages[0].text"),
    ("TC-MSG-004-1", [text("ok")] * 5,   200, None),
    ("TC-MSG-004-2", [text("ok")] * 6,   400, "messages"),      # Q04 확정 후 기대값 고정
])
def test_validate_push(line, tc_id, messages, expected_status, expected_property):
    r = line.post("/v2/bot/message/validate/push", json={"messages": messages})
    assert r.status_code == expected_status
    assert r.headers["x-line-request-id"]
    if expected_status == 400:
        body = r.json()
        assert isinstance(body["message"], str)
        assert any(d["property"] == expected_property for d in body["details"])
```

웹훅 서명 검증(TC-WHK-002~004)은 봇서버를 테스트 클라이언트로 직접 호출한다:

```python
def sign(body: bytes, secret: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()

@pytest.mark.parametrize("tc_id, mutate_body, mutate_sig, expected", [
    ("TC-WHK-002", lambda b: b, lambda s: s, 200),
    ("TC-WHK-003-1", lambda b: b, lambda s: s[:-1] + ("A" if s[-1] != "A" else "B"), 400),
    ("TC-WHK-003-2", lambda b: b.replace(b"hello", b"hellp"), lambda s: s, 400),
    ("TC-WHK-004", lambda b: b, lambda s: None, 400),
])
def test_webhook_signature(bot_client, raw_webhook, secret, tc_id, mutate_body, mutate_sig, expected):
    body = mutate_body(raw_webhook)
    sig = mutate_sig(sign(raw_webhook, secret))
    headers = {"x-line-signature": sig} if sig is not None else {}
    r = bot_client.post("/webhook", content=body, headers=headers)
    assert r.status_code == expected
```

### 8.4 UI(앱·콘솔) 계층 설계

- **범위**: API 호출은 자동으로 수행하고 '도달·표시·알림'만 사람이 LINE 앱에서 확인하는 반자동. 케이스 시트의 실측·메모 열에 도달 건수·스크린샷 파일명을 기록
- **절차 고정**: reply 케이스는 테스트 사용자가 봇에 메시지를 보내는 수동 트리거가 필요하므로, 수행자가 앱에서 보낸 뒤 자동 스크립트가 B1 로그에서 replyToken을 집어 1분 내 호출한다
- **콘솔 조작**: Verify 버튼, long-lived 토큰 재발급, secret 재발급, 재전송 ON/OFF는 콘솔 UI뿐이므로 체크리스트로 유지하고 결과(401 전환, 서명 거부)는 API로 확인
- **사내 환경이라면**: 테스트용 LINE 계정의 수신 메시지를 읽는 내부 도구가 있으면 도달 확인도 자동화 가능. 외부에서는 불가

### 8.5 수동으로 남기는 영역과 이유

| 영역 | TC | 이유 |
|---|---|---|
| 시간 경과 | AUTH-008, IDM-005, PGN-004, MLT-009(3단계) | 15분·24시간·14일 대기가 필요. 스케줄러로 자동화할 수 있으나 외부 포트폴리오에서는 캘린더 기록으로 대체 |
| 한도 도달 | AUTH-005, RLM-002 | 30개 토큰·60/h 한도 소진은 다른 테스트에 영향을 주므로 격리된 시간대에 1회만 수행 |
| 재전송 대기 | RPL-005, WHS-005, WHS-007 | 재전송 시점이 비공개라 대기 시간 예측 불가. 재전송 도착 후 검증 자체는 자동(WHS-006) |
| 비결정 관찰 | RPL-003, PSH-006 | 문서가 보장하지 않는 경계(1분·7일)는 분포를 기록하는 관찰 항목 |
| 코드·설정 리뷰 | SEC-005, SEC-006 | 상수 시간 비교·IP 제한 여부는 정적 검토 항목 |

### 8.6 CI 운영

- **PR 단위**: 무발송 API 스위트(토큰·공통 계약·validate·웹훅 서명·모의 서버 정책). 월 한도를 쓰지 않고 수 분 내 완료
- **나이틀리**: 발송 1건이 필요한 멱등성 케이스(IDM-001~003)와 페어와이즈 스모크(MSG-010 일부)를 테스트 계정으로 수행. 1일 발송 상한을 코드로 강제
- **리포트**: TC ID별 결과·X-Line-Request-Id·요청/응답 전문(마스킹)을 Allure 첨부로 모으고, 결과를 케이스 시트의 결과 열에 역반영하는 스크립트를 둔다
- **실패 분류**: 플랫폼 결함 / 봇서버 결함 / 클라이언트 결함 / 테스트 데이터 / 환경(ngrok·네트워크) / 플래키를 태깅. 플랫폼 결함은 수정 전제가 없으므로 재현율과 문서 불일치로 보고

### 8.7 외부 포트폴리오로서의 제약

API 계층의 대부분은 테스트 채널만 있으면 **외부에서도 실제 구현 가능**하다(토큰·validate·조회·웹훅 서명·모의 서버). 실제 구현은 `public-api-quality-lab` 프레임워크 위에 올리는 것을 전제로 하며, 이 프로젝트는 그 입력이 되는 설계를 담당한다. 구현 시 가장 먼저 올릴 것은 8.3의 validate 기반 경계 테이블과 웹훅 서명 테스트다 — 월 한도를 쓰지 않고, 중복 발송·위조 웹훅이라는 S1 결함 영역을 직접 막기 때문이다.

---

**참고 출처(조회일 2026-10-25)**

- Messaging API reference: https://developers.line.biz/en/reference/messaging-api/
- Receive messages (webhook) · Webhook redelivery: https://developers.line.biz/en/docs/messaging-api/receiving-messages/
- Verify webhook signature: https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/
- Retry failed API requests: https://developers.line.biz/en/docs/messaging-api/retrying-api-request/
- Channel access token (Basics): https://developers.line.biz/en/docs/basics/channel-access-token/
- Character counting in a text: https://developers.line.biz/en/docs/messaging-api/text-character-count/
- Messaging API development guidelines: https://developers.line.biz/en/docs/messaging-api/development-guidelines/
- Send messages · Verify webhook URL · Pricing: https://developers.line.biz/en/docs/messaging-api/
