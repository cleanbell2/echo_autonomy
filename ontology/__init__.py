"""코어 용어 레코드. 'types' 대신 'ontology'를 쓰는 이유: 최상위 types 패키지는 표준 라이브러리 types를 가린다."""
from .records import REGISTRY
from .schema import OntologyRecord
from .verify import check_evidence

__all__ = ["REGISTRY", "OntologyRecord", "check_evidence"]
