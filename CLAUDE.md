# Orbit Panel (LaunchDeck)

Windows 전용 생산성 런처. Python + PySide6 데스크톱 앱.

URL과 EXE/LNK 항목을 그룹별로 관리하고, 선택적으로 Python 자동화 스크립트를 실행.

## 요구사항

- Windows
- Python 3.10+
- PySide6

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 빌드 (Windows EXE)

```powershell
# 아이콘 생성 (변경 시)
python tools/generate_app_icon.py

# EXE 패키징
powershell -ExecutionPolicy Bypass -File tools/build_release.ps1
# 결과: dist/Orbit Panel.exe
```

## 폴더 구조

```
core/
├── action_dispatcher.py         # 액션 실행 관리
├── config_loader.py             # JSON 설정 로드/저장
├── logger.py
├── models.py                    # 데이터 모델 (Item, Group 등)
├── windows_diagnostics.py
└── windows_shortcuts.py

ui/
├── card_widget.py               # 항목 카드 위젯
├── group_panel.py               # 그룹 패널
├── log_panel.py
└── styles.py                    # 다크 테마 스타일

actions/                         # 커스텀 액션 정의

config/
└── launcher_items.json          # 런타임 설정 저장소

assets/icons/                    # 앱 아이콘

scripts/
└── examples/                    # 자동화 스크립트 예시
    ├── context_dump.py
    ├── browser_login_stub.py    # Playwright 로그인 템플릿
    └── naver_login.py

tools/
├── generate_app_icon.py
└── build_release.ps1
```

## 런타임 데이터 위치

- 소스 실행 시: `config/`, `logs/` (프로젝트 루트)
- EXE 실행 시: `%AppData%\Orbit Panel`

## Python 스크립트 연동

항목별로 스크립트 실행 시 Orbit Panel이 환경 변수를 주입:

| 변수 | 설명 |
|------|------|
| `ORBIT_PANEL_ITEM_ID` | 항목 ID |
| `ORBIT_PANEL_ITEM_TITLE` | 항목 제목 |
| `ORBIT_PANEL_ITEM_TARGET` | 실행 대상 (URL/경로) |
| `ORBIT_PANEL_RUN_MODE` | `target_only` / `target_then_script` / `script_only` |
| `ORBIT_PANEL_BASE_DIR` | 앱 기준 디렉토리 |
| `ORBIT_PANEL_RUNTIME_DIR` | 런타임 데이터 디렉토리 |

## 실행 모드

- `target_only` — 대상(URL/EXE)만 실행
- `target_then_script` — 대상 실행 후 스크립트 실행
- `script_only` — 스크립트만 실행
