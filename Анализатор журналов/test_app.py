import io, json, os, tempfile
from datetime import datetime
from app import parse_line, analyze, save, main

SAMPLE = (
    "2026-09-01T00:00:00Z | INFO | auth-api | A | m1\n"
    "2026-09-01T01:00:00Z | ERROR | auth-api | B | m2\n"
    "2026-09-01T02:00:00Z | ERROR | orders-api | B | m3\n"
    "bad line\n\n"
)

def _file(content):
    f = tempfile.NamedTemporaryFile("w", delete=False, suffix=".log", encoding="utf-8")
    f.write(content); f.close(); return f.name

def test_parse_valid():
    ev, err = parse_line(SAMPLE.split("\n")[0], 1)
    assert err is None and ev["level"] == "INFO"

def test_parse_errors():
    assert parse_line("bad\n", 1)[1] == "expected 5 fields, got 1"
    assert "empty" in parse_line("\n", 1)[1]
    assert "timestamp" in parse_line("x | INFO | a | b | c\n", 1)[1]
    assert "level" in parse_line("2026-09-01T00:00:00Z | XX | a | b | c\n", 1)[1]
    assert "empty field" in parse_line("2026-09-01T00:00:00Z | | a | b | c\n", 1)[1]
    assert "5 fields" in parse_line("a|b|c|d|e|f\n", 1)[1]

def test_analyze_counts_and_filters():
    p = _file(SAMPLE)
    try:
        s = analyze(p)
        assert s["total_lines"] == 5 and s["valid_lines"] == 3
        assert s["invalid_lines"] == 2 and s["matched_events"] == 3
        s2 = analyze(p, frm=datetime(2026,9,1,0,30), to=datetime(2026,9,1,3,0),
                     level="ERROR", source="auth-api")
        assert s2["matched_events"] == 1
        # from inclusive / to exclusive
        assert analyze(p, frm=datetime(2026,9,1,1,0))["matched_events"] == 2
        assert analyze(p, to=datetime(2026,9,1,1,0))["matched_events"] == 1
        # top-N
        assert analyze(p, top=1)["top_codes"] == [{"code": "B", "count": 2}]
    finally: os.unlink(p)

def test_empty_and_only_bad():
    p = _file("")
    try:
        assert analyze(p)["total_lines"] == 0
    finally: os.unlink(p)
    p = _file("bad\nmore bad\n")
    try:
        s = analyze(p)
        assert s["valid_lines"] == 0 and s["invalid_lines"] == 2
    finally: os.unlink(p)

def test_save_json_csv():
    p = _file(SAMPLE)
    try:
        s = analyze(p)
        for fmt, ext in [("json", ".json"), ("csv", ".csv")]:
            out = p + ext
            save(s, fmt, out)
            assert os.path.getsize(out) > 0
            os.unlink(out)
    finally: os.unlink(p)

def test_cli_errors_and_ok(capsys):
    assert main(["/no/such/file"]) == 2
    p = _file(SAMPLE)
    try:
        out = p + ".json"
        assert main([p, "--level", "ERROR", "--format", "json", "--output", out]) == 0
        assert json.load(open(out))["matched_events"] == 2
        os.unlink(out)
        assert main([p, "--format", "json"]) == 2          # format без output
        assert main([p, "--from", "2026-09-02T00:00:00Z",
                     "--to", "2026-09-01T00:00:00Z"]) == 2  # from >= to
        assert main([p, "--top", "0"]) == 2
    finally: os.unlink(p)