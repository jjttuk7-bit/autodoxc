# #2 FactsExtractor Rubric

## 항목

1. **명시 추출 정확성 (0.4)** — 사용자가 명시한 수치·키워드를 누락 없이 잡았는가?
2. **추론 적정성 (0.2)** — `inferred` source로 분류된 값들이 정말 명시 X 추론 O인가? (명시 값을 inferred로 분류하면 감점)
3. **confidence 합당성 (0.2)** — 명시 추출은 0.85+, 추론은 0.5~0.8 범위가 적절
4. **evidence_span 보존 (0.1)** — 가능한 경우 추출 위치를 span으로 남겼는가?
5. **field_id 표준 (0.1)** — `quant:명`, `industry`, `core_skill` 등 도메인 표준 ID를 사용했는가?

## 감점

- 사용자 명시 정보 누락: -0.3
- 잘못된 값 발명 (hallucination): -0.5
