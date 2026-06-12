# autodoxc 테스트 / 평가

## 디렉토리

```
src/backend/
├── tests/
│   ├── llm_eval/             # 에이전트 평가 (B0-7)
│   │   ├── runner.py         # 메인 러너 (assertion + LLM-judge + baseline)
│   │   ├── assertions.py     # subset 매칭 + {"__contains": ...} 슈가
│   │   ├── judge.py          # rubric 기반 LLM-judge (dummy 모드는 baseline 점수)
│   │   ├── baselines.py      # 점수·assert 결과 누적
│   │   ├── baselines.json    # 자동 갱신
│   │   ├── rubrics/          # 에이전트별 평가 rubric (M5 작성)
│   │   └── test_agents.py    # pytest 진입점
│   └── round_trip/           # Pydantic 모델 JSON 라운드트립
└── fixtures/
    └── prompts/{agent}/{case}/
        ├── input.json
        ├── expected.json     # 선택 (없으면 judge만)
        └── meta.md
```

## 실행

```pwsh
cd src/backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

## 평가 정책

1. **Assertion** — `expected.json`의 subset이 결과에 존재해야 함. 부분 문자열 매칭은 `{"__contains": "..."}` 슈가
2. **LLM-judge** — `rubrics/{agent}.md`를 시스템 프롬프트로, 결과를 user message로. dummy 모드는 0.85 baseline
3. **Baseline 임계치** — judge score ≥ 0.7 (현재 정책)
4. **Baseline 갱신** — 매 실행마다 `baselines.json`에 자동 기록

## fixture 추가

```pwsh
mkdir fixtures/prompts/{agent}/{new_case}
# input.json: 에이전트 Input 모델 페이로드
# expected.json: 기대 출력 subset (선택)
# meta.md: 케이스 설명
```

`test_agents.py`의 `_RUNNERS`에 등록된 에이전트만 자동 수집됨.

## rubric 갱신

`rubrics/{agent}.md`는 M5 (domain-expert) 영역. 변경 시 평가 결과 변동 가능 — baseline 재측정 권장.
