# ...existing code...
from typing import Optional

def thermodynamic_entropy(work: float, free_energy_change: float, gamma: float = 1.0) -> float:
	"""
	Calculate thermodynamic entropy production contribution.
	γ·TΣ = γ · (W - ΔF)
	"""
	dissipation = work - free_energy_change
	# 엔트로피 생성은 일반적으로 비음수지만, 계산 엔진에서는 raw value를 반환 후 처리
	return gamma * dissipation
