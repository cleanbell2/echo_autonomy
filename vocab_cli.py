# vocab_cli.py (한글 안내, 이모지 없음, ASCII 출력, 콘솔 인코딩 안전)
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys
import re
from vocab_tracker import VocabTracker

# -----------------------------
# 콘솔 인코딩 안전 (Windows)
# -----------------------------
def _safe_stdout():
    """
    Windows 콘솔에서 UnicodeEncodeError 방지.
    - 가능하면 utf-8 강제
    - 출력 불가 문자는 대체
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# -----------------------------
# 헬퍼 함수
# -----------------------------
def _read_stdin_all() -> str:
    return sys.stdin.read()

def _sanitize_json(raw: str) -> str:
    """
    붙여넣은 JSON에서 마지막 콤마 자동 제거
    - {"a":1,} 또는 [1,2,] 등
    """
    raw = raw.strip()
    if not raw:
        return raw
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return raw

def _ensure_list(data):
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []

def _coerce_item(item: dict) -> dict:
    word = (item.get("word") or "").strip()
    context = (item.get("context") or item.get("sentence") or "").strip()
    definition = (item.get("definition") or "").strip()
    tag = (item.get("tag") or "general").strip() or "general"
    return {"word": word, "context": context, "definition": definition, "tag": tag}

def _build_script(items: list[dict]) -> tuple[str, list[str]]:
    """
    iPhone 읽어주기용 스크립트 생성 (ASCII만)
    (script_text, ids_to_mark) 반환
    """
    lines = []
    lines.append(f"단어장입니다. {len(items)}개 단어 준비됨.")
    lines.append("---")

    ids_to_mark: list[str] = []

    for item in items:
        w = (item.get("word") or "").strip()
        d = (item.get("definition") or "").strip()
        ex = (item.get("context") or item.get("example") or "").strip()

        if not w or not d:
            continue

        block = (
            f"{w}.\n\n"
            f"{d}.\n\n"
            f"예문: {ex}.\n\n"
            f"다음 단어.\n"
        )
        lines.append(block)

        if isinstance(item.get("entry_ids"), list):
            ids_to_mark.extend([str(x) for x in item["entry_ids"] if x])
        elif item.get("id"):
            ids_to_mark.append(str(item["id"]))

    return "\n".join(lines), ids_to_mark

# -----------------------------
# 명령어 구현
# -----------------------------
def cmd_add(args):
    vt = VocabTracker(Path(args.journal), Path(args.reviewed))
    word = args.word or input("단어: ").strip()
    context = args.context or input("문맥/예문: ").strip()
    definition = args.definition or input("뜻: ").strip()

    if not word:
        print("[오류] 단어는 필수입니다.")
        return 1

    vt.add_entry(word, context, definition, tag=args.tag or "general")
    vt.flush_to_disk()
    print(f"[저장됨] {word}")
    return 0

def cmd_import(args):
    vt = VocabTracker(Path(args.journal), Path(args.reviewed))

    if args.file:
        try:
            raw = Path(args.file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"[오류] 파일 읽기 실패: {e}")
            return 1
    else:
        print("JSON 붙여넣고 EOF 입력 (PowerShell/CMD: Ctrl+Z + Enter, mac/Linux: Ctrl+D):")
        raw = _read_stdin_all()

    raw = _sanitize_json(raw)
    if not raw.strip():
        print("[안내] 입력 없음.")
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파싱 실패: {e}")
        print("힌트: 큰따옴표 사용, 마지막 콤마 제거.")
        return 1

    items = _ensure_list(data)
    if not items:
        print("[오류] JSON은 객체 또는 객체 리스트여야 합니다.")
        return 1

    count = 0
    skipped = 0
    for it in items:
        if not isinstance(it, dict):
            skipped += 1
            continue
        norm = _coerce_item(it)
        if not norm["word"] or not norm["definition"]:
            skipped += 1
            continue

        vt.add_entry(norm["word"], norm["context"], norm["definition"], tag=norm["tag"])
        count += 1

    vt.flush_to_disk()
    print(f"[완료] {count}개 항목 가져옴. {skipped}개 건너뜀.")
    return 0

def cmd_export(args):
    vt = VocabTracker(Path(args.journal), Path(args.reviewed))

    if args.due:
        items = vt.due_today(args.limit)
        mode = "복습(DUE)"
    else:
        items = vt.export_for_tts(max_words=args.limit, include_reviewed=False)
        mode = "신규(NEW)"

    if not items:
        print(f"[안내] {mode} 단어 없음.")
        return 0

    script, ids_to_mark = _build_script(items)

    out_path = Path(args.out)
    out_path.write_text(script, encoding="utf-8")
    print(f"[저장됨] 스크립트: {out_path}")
    print(f"모드: {mode} / 개수: {len(items)}")

    if args.mark_reviewed and ids_to_mark:
        vt.mark_reviewed(ids_to_mark, quality=3)
        print(f"[완료] 복습 처리: {len(ids_to_mark)}개 (quality=3)")

    return 0

def cmd_list(args):
    vt = VocabTracker(Path(args.journal), Path(args.reviewed))

    if args.due:
        items = vt.due_today(args.limit)
        print(f"\n오늘 복습 - {len(items)}개")
        print("-" * 70)
        for it in items:
            w = it.get("word", "")
            d = it.get("definition", "")
            nxt = str(it.get("next_review", "-") )[:10]
            rev = it.get("reviews", 0)
            print(f"- {w:<16} | 복습:{rev:<2} | 다음:{nxt} | {d[:40]}")
        print("-" * 70)
        return 0

    items = vt.export_for_tts(max_words=args.limit, include_reviewed=False)
    print(f"\n신규(미복습) - {len(items)}개")
    print("-" * 70)
    for it in items:
        w = it.get("word", "")
        d = it.get("definition", "")
        freq = it.get("frequency", 1)
        print(f"- {w:<16} | 빈도:{freq:<2} | {d[:45]}")
    print("-" * 70)
    return 0

def cmd_stats(args):
    journal = Path(args.journal)
    reviewed = Path(args.reviewed)
    vt = VocabTracker(journal, reviewed)

    total_entries = 0
    if journal.exists():
        with journal.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    total_entries += 1

    review_events = 0
    if reviewed.exists():
        with reviewed.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    review_events += 1

    unreviewed_words = len(vt.export_for_tts(max_words=99999, include_reviewed=False))

    print("\n단어장 통계")
    print("-" * 40)
    print(f"전체 단어:        {total_entries}")
    print(f"복습 이벤트:      {review_events}")
    print(f"미복습 단어:      {unreviewed_words}")
    if total_entries:
        print(f"복습/단어 비율:   {review_events/total_entries:.2f}")
    return 0

# -----------------------------
# 메인
# -----------------------------
def main():
    _safe_stdout()

    parser = argparse.ArgumentParser(description="R2D Vocab (한글, ASCII, SRS)")
    parser.add_argument("--journal", default="vocab_journal.jsonl")
    parser.add_argument("--reviewed", default="reviewed_ids.jsonl")

    sub = parser.add_subparsers(dest="command")

    p_import = sub.add_parser("import", help="JSON 붙여넣기 또는 파일 불러오기")
    p_import.add_argument("--file", help="JSON 파일 경로")

    p_export = sub.add_parser("export", help="TXT 스크립트 생성")
    p_export.add_argument("--out", default="script.txt", help="출력 TXT 파일명")
    p_export.add_argument("--limit", type=int, default=20)
    p_export.add_argument("--mark-reviewed", action="store_true", help="내보낸 단어 복습 처리(quality=3)")
    p_export.add_argument("--due", action="store_true", help="신규 대신 복습 단어 내보내기")

    p_list = sub.add_parser("list", help="단어 목록 보기")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--due", action="store_true", help="복습 단어만 보기")

    p_add = sub.add_parser("add", help="단어 직접 추가")
    p_add.add_argument("word", nargs="?")
    p_add.add_argument("context", nargs="?")
    p_add.add_argument("definition", nargs="?")
    p_add.add_argument("--tag", default="general")

    sub.add_parser("stats", help="통계 보기")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    funcs = {
        "import": cmd_import,
        "export": cmd_export,
        "list": cmd_list,
        "add": cmd_add,
        "stats": cmd_stats,
    }
    return funcs[args.command](args)

if __name__ == "__main__":
    raise SystemExit(main())
