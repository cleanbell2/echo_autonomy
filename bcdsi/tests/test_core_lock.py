import json
import dataclasses
from bcdsi.ebreak_calculator import EBreakCalculator

def test_analysis_summary_json_serializable():
    """
    E-Break 계산 결과가 JSON으로 직렬화(변환) 가능한지 확인
    """
    # 1. 계산기 생성
    calc = EBreakCalculator()
    
    # 2. 계산 실행 (SSOT API에 맞춰 필수 인자 전달)
    result = calc.calculate(base=0.5, shock=0.0)
    
    # 3. dataclass를 딕셔너리로 변환
    data = dataclasses.asdict(result)
    
    # 4. JSON 변환 테스트
    json_str = json.dumps(data)
    assert isinstance(json_str, str)
    assert "ebreak" in json_str
    assert "level" in json_str
import json

def test_analysis_summary_json_serializable():
    result = EBreakCalculator().calculate()
    json.dumps(result["analysis_summary"], ensure_ascii=False)