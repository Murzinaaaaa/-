"""Потоковый анализатор логов: timestamp | level | source | code | message"""
import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime

LEVELS = ("TRACE", "DEBUG", "INFO", "WARN", "ERROR")


def parse_line(line, n):
    """Возвращает (event_dict, None) или (None, reason)."""
    parts = [p.strip() for p in line.rstrip("\n").split("|")]
    if not line.strip():
        return None, "empty line"
    if len(parts) != 5:
        return None, f"expected 5 fields, got {len(parts)}"
    ts, lvl, src, code, msg = parts
    if not all(parts):
        return None, "empty field"
    if lvl not in LEVELS:
        return None, f"invalid level: {lvl}"
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None, f"invalid timestamp: {ts}"
    return {"ts": dt, "level": lvl, "source": src, "code": code,
            "message": msg, "line": n}, None


def analyze(path, frm=None, to=None, level=None, source=None, top=5):
    """Читает файл построчно, возвращает сводку."""
    stats = dict(total=0, valid=0, invalid=0, matched=0,
                 levels=Counter(), sources=Counter(), codes=Counter(),
                 bad_samples=[])
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            stats["total"] += 1
            ev, err = parse_line(line, n)
            if err:
                stats["invalid"] += 1
                if len(stats["bad_samples"]) < 20:
                    stats["bad_samples"].append((n, err))
                continue
            stats["valid"] += 1
            if frm and ev["ts"] < frm: continue
            if to and ev["ts"] >= to: continue
            if level and ev["level"] != level: continue
            if source and ev["source"] != source: continue
            stats["matched"] += 1
            stats["levels"][ev["level"]] += 1
            stats["sources"][ev["source"]] += 1
            stats["codes"][ev["code"]] += 1

    return {
        "total_lines": stats["total"],
        "valid_lines": stats["valid"],
        "invalid_lines": stats["invalid"],
        "matched_events": stats["matched"],
        "by_level": dict(sorted(stats["levels"].items())),
        "by_source": dict(sorted(stats["sources"].items())),
        "top_codes": [{"code": c, "count": n} for c, n in
                      sorted(stats["codes"].items(), key=lambda x: (-x[1], x[0]))[:top]],
        "invalid_samples": [{"line": n, "reason": r} for n, r in stats["bad_samples"]],
    }


def save(summary, fmt, path):
    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    else:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["metric", "key", "value"])
            for k in ("total_lines", "valid_lines", "invalid_lines", "matched_events"):
                w.writerow([k, "", summary[k]])
            for k, v in summary["by_level"].items(): w.writerow(["by_level", k, v])
            for k, v in summary["by_source"].items(): w.writerow(["by_source", k, v])
            for c in summary["top_codes"]: w.writerow(["top_code", c["code"], c["count"]])


def _dt(s):
    try: return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError: raise argparse.ArgumentTypeError(f"bad datetime: {s}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="log-analyzer")
    p.add_argument("input")
    p.add_argument("--from", dest="frm", type=_dt)
    p.add_argument("--to", dest="to", type=_dt)
    p.add_argument("--level", choices=LEVELS)
    p.add_argument("--source")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--format", choices=["json", "csv"])
    p.add_argument("--output")
    a = p.parse_args(argv)

    if (a.format is None) != (a.output is None):
        print("error: --format and --output must be used together", file=sys.stderr); return 2
    if a.frm and a.to and a.frm >= a.to:
        print("error: --from must be < --to", file=sys.stderr); return 2
    if a.top <= 0:
        print("error: --top must be > 0", file=sys.stderr); return 2

    try:
        summary = analyze(a.input, a.frm, a.to, a.level, a.source, a.top)
    except FileNotFoundError:
        print(f"error: file not found: {a.input}", file=sys.stderr); return 2
    except IsADirectoryError:
        print(f"error: is a directory: {a.input}", file=sys.stderr); return 2

    print("=" * 50)
    print(f"Total lines    : {summary['total_lines']}")
    print(f"Valid lines    : {summary['valid_lines']}")
    print(f"Invalid lines  : {summary['invalid_lines']}")
    print(f"Matched events : {summary['matched_events']}")
    print(f"By level  : {summary['by_level']}")
    print(f"By source : {summary['by_source']}")
    print(f"Top codes : {summary['top_codes']}")
    for s in summary["invalid_samples"]:
        print(f"  bad line {s['line']}: {s['reason']}")

    if a.format:
        save(summary, a.format, a.output)
        print(f"\nSaved {a.format.upper()} report to {a.output}", file=sys.stderr)
    return 0