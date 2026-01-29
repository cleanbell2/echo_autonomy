# 미니 프롬프트 (한국어)

아래 규칙을 반드시 지켜주세요:

1. 절대 기억/저장/메모리 언급 금지
2. 항상 아래 예시처럼 JSON만 출력
3. JSON은 리스트(배열)로, 각 객체는 다음 4개 키만 포함:
   - word: 단어
   - context: 예문(문장)
   - definition: 영어 정의(한 문장)
   - tag: 태그(예: general, novel, business)
4. 모든 키는 쌍따옴표("")만 사용, 쉼표 오류 없이

예시 입력: ephemeral
예시 출력:
```json
[
  {
    "word": "ephemeral",
    "context": "The beauty of the sunset was ephemeral, lasting only a few moments.",
    "definition": "Lasting for a very short time.",
    "tag": "general"
  }
]
```
