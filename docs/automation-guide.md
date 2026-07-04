# Orbit Panel 자동화 가이드

시나리오와 자동 로그인 스크립트로 "원클릭 루틴"을 만드는 방법을 정리한 문서입니다.

## 1. 시나리오 — 항목을 순서대로 실행하기

시나리오는 등록된 URL/EXE 항목들을 **정해진 순서와 딜레이로 실행**하는 묶음입니다.

1. 메인 화면 상단의 **Scenarios** 줄에서 `+ New Scenario` 클릭
2. 이름 입력 (예: `출근 루틴`)
3. `+ Add Step`으로 항목을 순서대로 추가
   - 각 스텝의 **N s wait**: 이 스텝을 실행하기 전에 기다릴 시간
     (예: 앱이 뜨는 데 시간이 걸리면 다음 스텝에 3~5초 대기를 줌)
4. 저장하면 칩이 생기고, **Run** 클릭 한 번으로 전체가 순서대로 실행됨

시나리오는 **트레이 아이콘 우클릭 → Run Scenario**에서도 실행할 수 있습니다.
항목을 삭제하면 시나리오에서 해당 스텝은 자동으로 제거됩니다.

## 2. 내장 액션 — 코딩 없이 쓰는 후처리

항목 편집에서 `Script Type = Built-in Action`을 선택하면 사용 가능합니다.

| 액션 | 동작 |
|------|------|
| `wait_2_seconds` / `wait_5_seconds` | 대기 (페이지/앱 로딩 대기용) |
| `copy_target_to_clipboard` | 항목의 URL/경로를 클립보드에 복사 |
| `copy_title_to_clipboard` | 항목 제목을 클립보드에 복사 |
| `open_target_folder` | 탐색기에서 대상 파일을 선택한 채로 열기 |
| `focus_window_matching_title` | 제목에 항목 이름이 포함된 창을 앞으로 가져오기 |
| `browser_login_placeholder_action` | Playwright 로그인 자동화용 템플릿 훅 |

## 3. 상주 기능 — 트레이 · 핫키 · 자동 시작

- **창 닫기(X)** → 종료되지 않고 트레이로 숨음 (완전 종료는 트레이 우클릭 → Quit)
- **Ctrl+Alt+O** → 어디서든 창 표시/숨김
- **Settings** 버튼 (메인 화면 우측 상단):
  - URL을 열 브라우저 선택: 시스템 기본 / Chrome / Edge / 커스텀 EXE
  - Windows 시작 시 자동 실행
  - 트레이 상주 여부, 핫키 사용 여부

## 4. GitHub 자동 로그인

`scripts/examples/github_login.py` — **세션 유지 방식**이라 비밀번호 저장 없이도 동작합니다.

### 원리

1. Orbit Panel 전용 브라우저 프로필로 GitHub을 엶
2. **첫 실행 때 한 번만** 직접 로그인 (2FA 포함)
3. 세션이 프로필에 저장되어, 이후에는 항상 로그인된 상태로 열림

### 설정 방법

1. 필요 패키지: `pip install playwright` (별도 브라우저 다운로드 불필요 — 설치된 Chrome 사용)
2. Orbit Panel에서 카드 추가/편집:
   - **Type**: URL, **Target**: `https://github.com`
   - **Script Type**: `Python File` → `scripts/examples/github_login.py` 선택
   - **Run Mode**: `Script Only`  ← 중요: 스크립트가 직접 브라우저를 열기 때문
3. 카드 실행 → 첫 로그인 한 번 → 끝. 시나리오에 넣으면 루틴의 일부가 됨

### 선택: 자격 증명 자동 입력

세션이 만료됐을 때 아이디/비번(+TOTP 2FA 코드)까지 자동으로 채우려면:

```bash
pip install keyring pyotp
python scripts/examples/github_login.py --setup
```

- 자격 증명은 **Windows 자격 증명 관리자**(사용자별 암호화)에 저장됩니다. 파일에 평문 저장되지 않습니다.
- 삭제하려면: Windows 자격 증명 관리자에서 `orbit-panel-github` 항목 제거

## 5. 회사 그룹웨어 로그인 + 회의실 예약

`scripts/examples/company_room_booking.py` — 로그인 세션 유지까지는 동작하는 상태이고,
예약 클릭 단계는 사이트마다 다르므로 **녹화로 채우는 구조**입니다.

### 1단계: 예약 과정 녹화

```bash
python -m playwright codegen --channel chrome https://회사예약페이지주소
```

- 브라우저와 함께 **코드가 실시간 생성되는 창**이 뜸
- 평소처럼 로그인하고 회의실 예약을 **한 번 끝까지** 진행
- 모든 클릭/입력이 Python 코드로 자동 변환됨

### 2단계: 생성된 코드를 스크립트에 병합

- codegen 창의 코드를 복사해서 `book_room()` 함수 안에 붙여넣기
  (또는 AI 어시스턴트에게 전달해 날짜 자동 계산 등 파라미터화 요청)
- 스크립트 상단의 `AUTO_BOOK = False`를 `True`로 변경
- **주의**: 녹화 코드에 입력한 비밀번호가 평문으로 남아 있으면 그 줄은 삭제할 것
  (로그인은 세션 유지 방식이라 최종 스크립트에 비밀번호가 필요 없음)

### 3단계: Orbit Panel 카드 연결

- **Type**: URL, **Target**: 회사 예약 페이지 URL
- **Script Type**: `Python File` → `scripts/examples/company_room_booking.py`
- **Run Mode**: `Script Only`

### 팁

- 첫 실행 때 로그인 한 번 → 이후엔 로그인 생략됨
- 예약 페이지가 사내망/VPN 전용이면 접속 가능한 상태에서 실행
- 예약 조건이 매번 거의 같다면 시나리오에 넣어 완전 원클릭화 가능

## 6. 다른 사이트로 확장하기

`github_login.py`를 복사해서 상수만 바꾸면 어떤 사이트든 같은 패턴을 적용할 수 있습니다:

- `LOGIN_URL`, `DEFAULT_TARGET` — 사이트 주소
- `profile_dir()`의 프로필 폴더명 — 사이트별로 분리 (예: `browser_profiles/jira`)
- `try_credential_login()`의 셀렉터 — 해당 사이트 로그인 폼에 맞게 (codegen으로 확인)
- `KEYRING_SERVICE` — 자격 증명 저장 키 이름

## 보안 노트

- **세션 프로필**은 런타임 디렉토리(`%AppData%\Orbit Panel` 또는 프로젝트 폴더)의
  `browser_profiles/`에 저장됩니다. 공용 PC에서는 사용하지 마세요.
- 자격 증명은 keyring(Windows 자격 증명 관리자)을 통해서만 저장하고,
  스크립트/환경 변수에 평문으로 넣지 않는 것을 권장합니다.
- TOTP 시크릿 저장은 편의 기능입니다. 저장하지 않아도 세션 유지 덕분에
  수동 2FA는 세션이 만료될 때만 필요합니다.
