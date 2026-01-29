# vocab_tracker.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
import json
from collections import defaultdict
from typing import Dict, List, Iterable, Optional, Tuple, Union

# --- 유틸리티 함수 ---
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _today_utc() -> date:
    return datetime.now(timezone.utc).date()

def _parse_iso_date(s: str) -> Optional[date]:
    if not s: return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None

def _jsonl_iter(path: Path) -> Iterable[dict]:
    if not path.exists(): return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

def _jsonl_append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# --- SRS 데이터 클래스 ---
@dataclass
class SRSState:
    reviews: int = 0
    interval_days: int = 0
    ef: float = 2.5
    next_review: Optional[str] = None

# --- SRS 로직 (SM-2 알고리즘) ---
def _sm2_update(state: SRSState, quality: int, today: date) -> SRSState:
    q = quality
    reviews = state.reviews
    interval = state.interval_days
    ef = state.ef

    if q < 3: # 0: 어려움/망각 -> 리셋
        return SRSState(reviews=0, interval_days=1, ef=max(1.3, ef), 
                       next_review=(today + timedelta(days=1)).isoformat())

    # 성공 (3 or 4)
    reviews += 1
    if reviews == 1:
        interval = 1
    elif reviews == 2:
        interval = 6
    else:
        interval = max(1, int(round(interval * ef)))

    # Easiness Factor 조정
    ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    ef = max(1.3, min(2.8, ef))

    next_day = today + timedelta(days=interval)
    return SRSState(reviews=reviews, interval_days=interval, ef=ef, next_review=next_day.isoformat())


class VocabTracker:
    def __init__(self, journal_path: Path = Path("vocab_journal.jsonl"), reviewed_path: Path = Path("reviewed_ids.jsonl")):
        self.journal_path = journal_path
        self.reviewed_path = reviewed_path
        self.session_buffer = []

    def add_entry(self, word: str, context: str, definition: str, tag: str = ""):
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"), # ID 생성
            "timestamp": _utc_now_iso(),
            "word": word,
            "context": context,
            "definition": definition,
            "tag": tag
        }
        self.session_buffer.append(entry)
        return entry

    def flush_to_disk(self) -> int:
        if not self.session_buffer: return 0
        for entry in self.session_buffer:
            _jsonl_append(self.journal_path, entry)
        count = len(self.session_buffer)
        self.session_buffer.clear()
        return count

    def mark_reviewed(self, entry_ids: List[str], quality: int = 3) -> int:
        ts = _utc_now_iso()
        count = 0
        for eid in entry_ids:
            _jsonl_append(self.reviewed_path, {"id": eid, "ts": ts, "q": quality})
            count += 1
        return count

    # 내부용: 리뷰 로그 로드
    def _load_review_events(self) -> Dict[str, List[Tuple[date, int]]]:
        events = defaultdict(list)
        for row in _jsonl_iter(self.reviewed_path):
            eid = str(row.get("id", "")).strip()
            if not eid: continue
            
            ts = row.get("ts") or row.get("timestamp") or ""
            day = _parse_iso_date(ts) or _today_utc()
            
            # 품질 점수 파싱 (기본값 3)
            q_val = row.get("q")
            q = 3
            if isinstance(q_val, int): q = q_val
            elif isinstance(q_val, str) and q_val.isdigit(): q = int(q_val)
            
            events[eid].append((day, q))
        
        # 날짜순 정렬
        for eid in events:
            events[eid].sort(key=lambda x: x[0])
        return events

    # 내부용: 단어별 현재 SRS 상태 계산
    def _srs_state_for_id(self, entry_id: str, events_map: Dict) -> SRSState:
        today = _today_utc()
        st = SRSState(reviews=0, interval_days=0, ef=2.5, next_review=today.isoformat())
        for (day, q) in events_map.get(entry_id, []):
            st = _sm2_update(st, q, day)
        return st

    # --- 기능 1: TTS 내보내기 (신규 + 복습필요 제외 등) ---
    def export_for_tts(self, max_words: int = 20, include_reviewed: bool = False) -> List[dict]:
        entries = []
        # 최신 단어부터 로드
        all_rows = list(_jsonl_iter(self.journal_path))
        
        events_map = self._load_review_events()
        
        # 단어 중복 제거 (최신 정의 사용)
        unique_map = {}
        for row in all_rows:
            unique_map[row['word']] = row
        
        candidates = list(unique_map.values())
        
        out = []
        for item in candidates:
            eid = item.get("id")
            # 리뷰 여부 체크
            has_review = eid in events_map and len(events_map[eid]) > 0
            
            if (not include_reviewed) and has_review:
                continue # 이미 본 것은 건너뜀
            
            # 출력 포맷 맞춤
            item['entry_ids'] = [eid] 
            item['frequency'] = 1
            out.append(item)
            
            if len(out) >= max_words: break
            
        return out

    # --- 기능 2: 오늘 복습할 단어 (Due Today) ---
    def due_today(self, limit: int = 20) -> List[dict]:
        all_rows = list(_jsonl_iter(self.journal_path))
        events_map = self._load_review_events()
        today = _today_utc()
        
        due_list = []
        seen_words = set()

        for row in all_rows:
            eid = row.get("id")
            if not eid or row['word'] in seen_words: continue
            
            # 리뷰 기록이 없으면 SRS 대상 아님 (신규 학습 대상)
            if eid not in events_map: continue
            
            st = self._srs_state_for_id(eid, events_map)
            next_due_date = _parse_iso_date(st.next_review)
            
            # 만기일이 오늘이거나 지났으면 추가
            if next_due_date and next_due_date <= today:
                row['reviews'] = st.reviews
                row['interval_days'] = st.interval_days
                row['next_review'] = st.next_review
                due_list.append(row)
                seen_words.add(row['word'])

        # 오래 밀린 순서로 정렬
        due_list.sort(key=lambda x: x['next_review'])
        return due_list[:limit]
