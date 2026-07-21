# Tiny Second-hand Shopping Platform

## 주요 기능

- 회원가입, 로그인·로그아웃, 공개 프로필, 마이페이지, 비밀번호 변경
- 상품 등록·조회·검색·수정·논리 삭제와 이미지 검증
- WebSocket 기반 참여자 전용 1:1 채팅과 사용자별 말풍선 구분
- 상품 신고 대상 고정, 사유 분류, 자기·중복·대량 신고 방지 및 임계치 기반 자동 검토
- 1:1 채팅 안에서 수행하는 원자적 가상 포인트 송금, 거래 내역과 중복 송금 방지
- 마이페이지의 상품·채팅·신고·포인트 내역과 사용자 검색
- 사용자·상품·Chat·신고·거래 관리와 변경 불가능한 감사 로그

## 환경 요구사항

- Python 3.12 권장(최소 Python 3.10)
- Git
- 최신 Chrome, Edge 또는 Firefox
- 개발 DB: SQLite
- 검증·운영 DB: PostgreSQL 권장
- 운영 채널 계층: Redis 권장

현재 저장소 기본 설정은 로컬 개발 편의를 위해 SQLite와 인메모리 WebSocket 채널 계층을 사용합니다. 송금 동시성 및 다중 프로세스 채팅 운영에는 각각 PostgreSQL과 Redis 설정이 필요합니다.

## 저장소 내려받기

```powershell
git clone https://github.com/Jiho12315/White_Hat_School.git
Set-Location .\White_Hat_School\Secure_Coding\Tiny_Second_hand_Shopping_Platform
```


## 설치 및 가상환경 설정

Windows PowerShell 예시입니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

PowerShell에서 스크립트 실행이 차단될 때는 현재 창에만 실행 권한을 허용한 뒤 다시 활성화합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

프롬프트 앞에 `(.venv)`가 표시되면 가상환경이 활성화된 것입니다. 새 PowerShell 창을 열 때마다 프로젝트 폴더에서 활성화 명령을 다시 실행해야 합니다.

## 환경변수 설정

`.env.example`은 필요한 변수의 참고용 목록입니다. 현재 프로젝트는 `python-dotenv`를 사용하지 않으므로 `.env` 파일을 복사하는 것만으로는 값이 적용되지 않습니다. 로컬 개발에서는 서버를 실행할 PowerShell 창에 다음 값을 설정합니다.

```powershell
$env:DJANGO_SECRET_KEY = (& python -c "from secrets import token_urlsafe; print(token_urlsafe(50))")
$env:DJANGO_DEBUG = "True"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
```

환경변수는 해당 PowerShell 창을 닫으면 사라집니다. 값을 설정하지 않아도 로컬 실행은 가능하지만, 그 경우 안전하지 않은 기본 개발 키가 사용됩니다. 실제 배포에서는 반드시 강한 `DJANGO_SECRET_KEY`를 제공하고 `DJANGO_DEBUG=False`로 설정해야 합니다.

## 데이터베이스 준비 및 관리자 생성

```powershell
python manage.py migrate
python manage.py createsuperuser
```

관리자 계정의 사용자 이름·이메일·비밀번호를 안내에 따라 직접 입력합니다. 저장소에는 공용 관리자 비밀번호가 포함되지 않습니다. 비밀번호를 잊었다면 다음과 같이 변경할 수 있습니다.

```powershell
python manage.py changepassword 관리자_사용자이름
```

카테고리별 시연용 상품 56개를 생성하려면 다음 명령을 실행합니다. 여러 번 실행해도 같은 샘플이 중복 생성되지 않습니다.

```powershell
python manage.py seed_sample_data --sample-password "직접_정한_안전한_테스트_비밀번호"
```

## 실행

```powershell
python manage.py runserver 127.0.0.1:8000
```

브라우저에서 다음 주소를 엽니다.

- 서비스: `http://127.0.0.1:8000/`
- 관리자: `http://127.0.0.1:8000/admin/`

Daphne이 `INSTALLED_APPS`에 포함되어 있어 `runserver`가 HTTP와 WebSocket 요청을 함께 처리합니다.

서버를 종료하려면 서버를 실행한 PowerShell 창에서 `Ctrl+C`를 누릅니다.

## 테스트

```powershell
python manage.py check
python manage.py test -v 2
python manage.py check --deploy
```

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

## 로컬 데이터

- 사용자·상품·채팅·신고·포인트 내역은 기본적으로 `db.sqlite3`에 저장됩니다.
- 사용자가 업로드한 상품·프로필 이미지는 `media/`에 저장됩니다.
- `db.sqlite3`와 `media/`는 개인정보 및 시험 데이터가 포함될 수 있어 Git 업로드 대상에서 제외됩니다.
- 저장소를 새로 내려받은 사용자는 `migrate`와 `createsuperuser`를 실행해 각자의 로컬 DB를 준비해야 합니다.

## 자주 발생하는 문제

### `No module named 'django'`

가상환경이 활성화되지 않았거나 패키지가 설치되지 않은 상태입니다.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### CSS 또는 정적 파일이 갱신되지 않음

개발 서버를 다시 실행하고 브라우저에서 `Ctrl+F5`로 강력 새로고침합니다.

### DB 테이블 관련 오류

최신 마이그레이션을 적용합니다.

```powershell
python manage.py migrate
```

