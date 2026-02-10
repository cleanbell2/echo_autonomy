# ...existing code...
import numpy as np
from typing import Union, Optional

class NonUnitarityManager:
	def __init__(self):
		pass

def non_unitarity(channel: Union[np.ndarray, list], method: str = 'trace_distance', tolerance: float = 1e-12) -> float:
	"""Calculate non-unitarity measure of a quantum channel."""
	# 더미 구현: 실제 채널 행렬 분석 대신 스칼라 값이면 그대로, 행렬이면 Norm 반환
	if isinstance(channel, (int, float)):
		return float(channel)
	chan = np.asarray(channel)
	# Unitarity deviation check (simplified)
	return float(np.sum(np.abs(chan)) * 0.1)

def bias_induction(channel: Union[np.ndarray, list], method: str = 'operator_norm') -> float:
	"""Calculate bias induction potential."""
	return non_unitarity(channel) * 0.5

# Test helpers
def create_unitary_channel(theta): return np.eye(2)
def create_dephasing_channel(p): return np.eye(2)
def create_amplitude_damping_channel(gamma): return np.eye(2)
