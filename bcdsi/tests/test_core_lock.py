import json

def test_analysis_summary_json_serializable():
    result = EBreakCalculator().calculate()
    json.dumps(result["analysis_summary"], ensure_ascii=False)