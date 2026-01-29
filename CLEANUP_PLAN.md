# 🧹 Code Cleanup Plan

## 1. 삭제할 파일 (Redundant Files)
- [ ] `bcdsi/monitor.py.bak` - 백업 파일
- [ ] `q_quantum/quantum/anchor.py.bak` - 백업 파일

## 2. 정리할 문서 (Documentation)
- [ ] `3단계자율의상재설정.txt` → `docs/`로 이동
- [ ] `html!-- 초간단 HTML 버전 --.txt` → 삭제 또는 정리

## 3. HTML 도구 (Tools)
- [ ] `ai_safety_scanner.html` → `tools/` 폴더로 이동
- [ ] `safety_scanner_v2.html` → `tools/` 폴더로 이동

## 4. 구조화 제안 (Structure)
```
echo_autonomy/
├── bcdsi/              # Core module (keep as is)
├── q_quantum/          # Quantum components
├── sicl/               # SICL components
├── tests/              # Test files
├── docs/               # Documentation (NEW)
│   └── 3단계자율의상재설정.txt
├── tools/              # Utilities (NEW)
│   ├── ai_safety_scanner.html
│   └── safety_scanner_v2.html
├── examples/           # Example scripts (NEW)
│   ├── example_usage.py
│   └── example_bcdsi_usage.py
└── scripts/            # Run scripts (NEW)
    ├── run_echo.py
    └── run_echo_v2.py
```

## 5. 버전 파일 처리
- [ ] `non_unitarity_original.py` - 유지 필요 여부 확인
- [ ] `run_echo_v2.py` vs `run_echo.py` - 어느 것이 최신인지 확인

## 6. 추가 정리
- [ ] `__pycache__/` 제거 (이미 .gitignore에 있음)
- [ ] 사용하지 않는 import 정리
- [ ] 코드 포맷팅 (black/ruff)

