# Tiny Second-hand Shopping Platform

보안을 중심으로 설계한 교육용 소규모 중고거래 웹 플랫폼입니다. 회원, 상품, 1:1 채팅, 상품 신고·자동 검토, 채팅 기반 가상 포인트 송금, 검색, 관리자·감사 로그 기능을 제공합니다.

> 송금 기능은 실제 금융 거래가 아닌 교육용 가상 포인트 이동입니다.

## 주요 기능

- 회원가입, 로그인·로그아웃, 공개 프로필, 마이페이지, 비밀번호 변경
- 상품 등록·조회·검색·수정·논리 삭제와 이미지 검증
- WebSocket 기반 참여자 전용 1:1 채팅과 사용자별 말풍선 구분
- 상품 신고 대상 고정, 사유 분류, 자기·중복·대량 신고 방지 및 임계치 기반 자동 검토
- 1:1 채팅 안에서 수행하는 원자적 가상 포인트 송금, 거래 내역과 중복 송금 방지
- 마이페이지의 상품·채팅·신고·포인트 내역과 사용자 검색
- 사용자·상품·Chat·신고·거래 관리와 변경 불가능한 감사 로그

## 환경 요구사항

- Python 3.12 권장
- 개발 DB: SQLite
- 검증·운영 DB: PostgreSQL 권장
- 운영 채널 계층: Redis 권장

현재 저장소 기본 설정은 로컬 개발 편의를 위해 SQLite와 인메모리 WebSocket 채널 계층을 사용합니다. 송금 동시성 및 다중 프로세스 채팅 운영에는 각각 PostgreSQL과 Redis 설정이 필요합니다.

## 설치

Windows PowerShell 예시입니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

이 프로젝트는 별도 dotenv 패키지를 사용하지 않으므로 `.env` 파일을 자동으로 읽지 않습니다. 개발에서는 PowerShell 환경변수를 설정하거나 기본 개발값을 사용할 수 있습니다.

```powershell
$env:DJANGO_SECRET_KEY = "개발용-임의의-긴-비밀키"
$env:DJANGO_DEBUG = "True"
```

운영 환경에서는 반드시 강한 `DJANGO_SECRET_KEY`를 환경변수로 제공하고 `DJANGO_DEBUG=False`로 설정해야 합니다.

## DB 초기화 및 관리자 생성

```powershell
python manage.py migrate
python manage.py createsuperuser
```

카테고리별 시연용 상품 56개를 생성하려면 다음 명령을 실행합니다. 여러 번 실행해도 같은 샘플이 중복 생성되지 않습니다.

```powershell
python manage.py seed_sample_data --sample-password "직접_정한_안전한_테스트_비밀번호"
```

## 실행

```powershell
python manage.py runserver
```

브라우저에서 다음 주소를 엽니다.

- 서비스: `http://127.0.0.1:8000/`
- 관리자: `http://127.0.0.1:8000/admin/`

Daphne이 `INSTALLED_APPS`에 포함되어 있어 `runserver`가 HTTP와 WebSocket 요청을 함께 처리합니다.

## 테스트

```powershell
python manage.py test -v 2
python manage.py check
python manage.py check --deploy
```

`check --deploy`는 개발 설정에서는 HTTPS·HSTS·운영용 비밀키 관련 경고를 의도적으로 표시할 수 있습니다. 운영 환경변수를 적용한 상태에서 다시 확인해야 합니다.

## 주요 환경변수

| 변수 | 기본 개발값 | 설명 |
|---|---:|---|
| `DJANGO_SECRET_KEY` | 안전하지 않은 개발 키 | 운영에서는 반드시 변경 |
| `DJANGO_DEBUG` | `True` | 운영에서는 `False` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | 허용 호스트 |
| `DJANGO_HSTS_SECONDS/PRELOAD` | `0/False` | HTTPS 검증 후 운영에서 활성화 |
| `INITIAL_POINT_BALANCE` | `10000` | 가입 시 교육용 초기 포인트 |
| `PRODUCT_REPORT_THRESHOLD` | `3` | 상품 검토 전환 신고 수 |
| `USER_REPORT_THRESHOLD` | `5` | 사용자 제한 전환 신고 수 |
| `MAX_IMAGE_BYTES` | `5242880` | 이미지 최대 크기 |
| `LOGIN_RATE_COUNT/WINDOW` | `5/300` | 로그인 요청 제한 |
| `CHAT_RATE_COUNT/WINDOW` | `10/10` | 채팅 전송 제한 |
| `REPORT_RATE_COUNT/WINDOW` | `5/3600` | 신고 요청 제한 |
| `TRANSFER_RATE_COUNT/WINDOW` | `5/60` | 송금 요청 제한 |

위 정책값은 요구사항 보고서에서 미결정이었던 항목에 적용한 개발 기본값입니다. 배포 전에 운영 정책에 맞게 검토하십시오.

## 보안 설계 요약

- Django 비밀번호 해시와 세션 인증, 로그인 후 세션 키 회전
- POST 상태 변경과 CSRF 검증, GET 로그아웃 차단
- ORM 사용 및 서버 측 입력·소유권·참여자 권한 검증
- 템플릿 자동 이스케이프와 채팅 DOM `textContent` 출력
- 이미지 크기·실제 디코딩·허용 형식 검증 및 무작위 파일명
- 로그인·채팅·신고·송금 기능별 요청 제한
- 신고 중복 DB 제약과 송금 중복방지키·트랜잭션·지갑 행 잠금
- 관리자 상태 변경, 자동 제재, 송금 감사 로그
- 운영용 Secure/HttpOnly/SameSite 쿠키, HTTPS/WSS, HSTS 설정 지원

## 문서

- [요구사항 분석](docs/requirements-analysis.md)
- [시스템 설계](docs/system-design.md)
- [보안 및 테스트 보고서](docs/security-test-report.md)
- [수동 테스트 유즈케이스](docs/use-cases.md)

## 공개 저장소 주의사항

`.env`, SQLite DB, 업로드 이미지, 로그, 캐시 파일은 `.gitignore`로 제외합니다. 공개 전 `git status`에서 비밀정보와 개인정보가 포함되지 않았는지 다시 확인하십시오.
