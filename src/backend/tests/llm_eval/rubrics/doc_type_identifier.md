# #1a DocTypeIdentifier Rubric

다음 기준으로 0.0~1.0 점수를 매겨라.

## 항목 (가중치)

1. **분류 정확성 (0.5)** — `doc_type.id`가 사용자 입력의 의도에 부합하는가?
2. **confidence 합당성 (0.2)** — 분류 신뢰도가 분류 정확성과 일관되는가? (틀린 분류에 0.9는 부적합)
3. **signals 투명성 (0.2)** — `signals`에 어떤 단서로 분류했는지 설명되어 있는가?
4. **fallback 처리 (0.1)** — 모호한 입력에는 `generic-administrative-doc`이나 낮은 confidence가 적절한가?

## 감점 사유

- 명백히 잘못된 분류 (-0.5)
- signals 비어있음 (-0.2)
- confidence가 0.95 이상인데 모호한 입력 (-0.3)
