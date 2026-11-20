# -*- coding: utf-8 -*-
"""실험 1 데이터 분할 생성 (제안·미승인). agentdojo 설치 환경에서만 실행.
    pip install agentdojo==0.1.35 && python -m experiments.exp1.make_split

규칙: 스위트별로 사용자 작업과 주입 작업을 각각 1/3 보정 · 2/3 평가로 나눈다 (내림).
고정 시드로 섞고, 결과 JSON 을 커밋해 평가 전에 고정한다. 보정/평가 사이에 작업 공유 없음.
"""
import json
import random
import sys

SEED = 20261003
VERSION = "v1.2.2"


def main(out="experiments/exp1/split_v1.2.2_seed20261003.json"):
    from agentdojo.task_suite.load_suites import get_suites
    import agentdojo
    rng = random.Random(SEED)
    split = {"benchmark_version": VERSION, "agentdojo": agentdojo.__version__ if hasattr(agentdojo, "__version__") else "0.1.35",
             "seed": SEED, "suites": {}}
    for name, suite in sorted(get_suites(VERSION).items()):
        entry = {}
        for kind, ids in (("user_tasks", sorted(suite.user_tasks)), ("injection_tasks", sorted(suite.injection_tasks))):
            ids = list(ids)
            rng.shuffle(ids)
            k = len(ids) // 3
            entry[kind] = {"calibration": sorted(ids[:k], key=_num), "evaluation": sorted(ids[k:], key=_num)}
        split["suites"][name] = entry
    with open(out, "w", encoding="utf-8") as f:
        json.dump(split, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return split


def _num(s):
    return int(s.rsplit("_", 1)[1])


if __name__ == "__main__":
    s = main(*sys.argv[1:])
    for n, e in s["suites"].items():
        print(n, {k: (len(v["calibration"]), len(v["evaluation"])) for k, v in e.items()})
