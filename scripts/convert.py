#!/usr/bin/env python3
"""将 src_raw/<name>.py 转换为 assets/content/<name>.json，并做 schema 校验。

用法:
  python3 scripts/convert.py            # 全量转换（题库域逐个 + projects_* 合并 + exps）
  python3 scripts/convert.py pretrain   # 转换/校验单个内容域
  python3 scripts/convert.py projects_a # 校验单个项目实战子模块（最后统一合并）
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "src_raw"
OUT = ROOT / "assets" / "content"

DOMAINS = {
    "basics": "深度学习与ML基础",
    "transformer": "Transformer与大模型结构",
    "pretrain": "预训练",
    "posttrain": "后训练与对齐",
    "rl": "强化学习与推理模型",
    "agent": "Agent与Harness",
    "embodied": "具身智能与VLA",
    "driving": "自动驾驶与世界模型",
    "handcoded": "手撕代码",
    "scenario": "场景设计与开放题",
}

Q_TYPES = ("八股", "手撕", "场景", "概念")


def load(name: str):
    path = RAW / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(f"raw_{name}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_q(q: dict, prefix: str):
    qid = q.get("id", "?")
    for k in ("id", "topic", "type", "difficulty", "frequency", "question", "answerMd", "keyPoints"):
        assert q.get(k) not in (None, "", []), f"{qid} 缺字段/为空: {k}"
    assert q["id"].startswith(prefix), f"{qid} id 前缀应为 {prefix}-"
    assert q["type"] in Q_TYPES, f"{qid} type 非法: {q['type']}"
    assert isinstance(q["difficulty"], int) and 1 <= q["difficulty"] <= 5, f"{qid} difficulty 非法"
    assert isinstance(q["frequency"], int) and 1 <= q["frequency"] <= 5, f"{qid} frequency 非法"
    assert isinstance(q["keyPoints"], list) and len(q["keyPoints"]) >= 2, f"{qid} keyPoints 至少 2 条"
    assert len(q["answerMd"]) >= 100, f"{qid} answerMd 太短"
    for fu in q.get("followUps") or []:
        assert isinstance(fu, dict) and fu.get("q") and fu.get("a"), f"{qid} followUp 格式错误"
    code = q.get("code")
    if code is not None:
        assert isinstance(code, dict) and code.get("lang") and code.get("content"), f"{qid} code 格式错误"


def check_project(p: dict):
    for k in ("id", "name", "domain", "level", "tags", "summaryMd", "bodyMd"):
        assert p.get(k) not in (None, "", []), f"{p.get('id', '?')} 缺字段 {k}"


def check_exp(e: dict):
    for k in ("id", "company", "group", "role", "questions", "focus", "advice"):
        assert e.get(k) not in (None, "", []), f"{e.get('id', '?')} 缺字段 {k}"
    assert isinstance(e["questions"], list) and len(e["questions"]) >= 5, f"{e['id']} questions 至少 5 条"


def dump(path: Path, data: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def write_domain(name: str) -> int:
    qs = load(name).QUESTIONS
    for q in qs:
        check_q(q, name + "-")
    ids = [q["id"] for q in qs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, f"{name} 重复 id: {dup}"
    dump(OUT / f"{name}.json", {"domain": name, "domainName": DOMAINS[name], "updated": "2026-08-30", "questions": qs})
    print(f"{name:12s} {len(qs):4d} 条 ✓")
    return len(qs)


def collect_projects() -> list:
    ps = []
    for path in sorted(RAW.glob("projects_*.py")):
        m = load(path.stem)
        assert hasattr(m, "PROJECTS") and m.PROJECTS, f"{path.stem} 缺 PROJECTS"
        for p in m.PROJECTS:
            check_project(p)
        ps.extend(m.PROJECTS)
    ids = [p["id"] for p in ps]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, f"projects 重复 id: {dup}"
    return ps


def write_exps() -> int:
    es = load("exps").EXPS
    for e in es:
        check_exp(e)
    dump(OUT / "exps.json", {"domain": "exps", "domainName": "面经库", "updated": "2026-08-30", "exps": es})
    print(f"{'exps':12s} {len(es):4d} 条 ✓")
    return len(es)


def main():
    names = sys.argv[1:]
    if not names:
        total = 0
        for d in DOMAINS:
            if (RAW / f"{d}.py").exists():
                total += write_domain(d)
        if list(RAW.glob("projects_*.py")):
            ps = collect_projects()
            dump(OUT / "projects.json", {"domain": "projects", "domainName": "项目实战", "updated": "2026-08-30", "projects": ps})
            print(f"{'projects':12s} {len(ps):4d} 条 ✓")
            total += len(ps)
        if (RAW / "exps.py").exists():
            total += write_exps()
        print(f"合计 {total} 条")
        return
    for n in names:
        if n in DOMAINS:
            write_domain(n)
        elif n.startswith("projects_"):
            m = load(n)
            assert hasattr(m, "PROJECTS") and m.PROJECTS, f"{n} 缺 PROJECTS"
            for p in m.PROJECTS:
                check_project(p)
            print(f"{n:12s} {len(m.PROJECTS):4d} 个项目 ✓ (已校验，全量转换时合并)")
        elif n == "projects":
            ps = collect_projects()
            dump(OUT / "projects.json", {"domain": "projects", "domainName": "项目实战", "updated": "2026-08-30", "projects": ps})
            print(f"{'projects':12s} {len(ps):4d} 条 ✓")
        elif n == "exps":
            write_exps()
        else:
            raise ValueError(f"未知内容域: {n}")


if __name__ == "__main__":
    main()
