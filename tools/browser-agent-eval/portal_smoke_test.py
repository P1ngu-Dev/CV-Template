#!/usr/bin/env python3
"""Smoke-test browser tools against job portals and record compactness.

This is intentionally simple: it compares whether tools can load a portal/search
page and how large the agent-facing text output is. It does not submit forms or
log into anything.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "browser-agent-eval" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

URLS = {
    "getonbrd_programming": "https://www.getonbrd.com/jobs/programming",
    "chiletrabajos_practica_informatica": "https://www.chiletrabajos.cl/trabajo/practica-informatica",
    "computrabajo_practica_informatica": "https://cl.computrabajo.com/trabajo-de-practica-informatica",
}

COMMANDS = {
    "obscura_text": lambda url: ["obscura", "fetch", url, "--dump", "text", "--wait", "3", "--timeout", "30", "--stealth"],
    "lightpanda_semantic": lambda url: ["lightpanda", "fetch", url, "--dump", "semantic_tree_text", "--wait-ms", "3000"],
    "agent_browser_snapshot": lambda url: ["bash", "-lc", f"agent-browser close --all >/dev/null 2>&1 || true; agent-browser open {url!r} >/dev/null; agent-browser wait --load domcontentloaded >/dev/null; agent-browser snapshot -i -u -c -d 4; agent-browser close >/dev/null"],
}


def run(cmd: list[str], timeout: int = 90) -> dict:
    if cmd[0] not in {"bash"} and shutil.which(cmd[0]) is None:
        return {"ok": False, "exit_code": None, "error": f"missing command: {cmd[0]}", "stdout": "", "stderr": ""}
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {"ok": p.returncode == 0, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "exit_code": None, "error": "timeout", "stdout": e.stdout or "", "stderr": e.stderr or ""}


def summarize(text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    keywords = ["pract", "intern", "software", "developer", "desarroll", "inform", "python", "ingenier"]
    hits = [ln for ln in lines if any(k.lower() in ln.lower() for k in keywords)]
    return {
        "chars": len(text),
        "nonempty_lines": len(lines),
        "keyword_lines_found": len(hits),
        "sample_keyword_lines": hits[:8],
    }


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {"created_at": datetime.now().isoformat(), "results": []}
    for url_name, url in URLS.items():
        for tool_name, make_cmd in COMMANDS.items():
            print(f"== {url_name} / {tool_name} ==", flush=True)
            res = run(make_cmd(url))
            stdout = res.get("stdout") or ""
            stderr = res.get("stderr") or ""
            out_file = OUT / f"{stamp}_{url_name}_{tool_name}.txt"
            out_file.write_text(stdout + ("\n\n--- STDERR ---\n" + stderr if stderr else ""), encoding="utf-8")
            row = {
                "url_name": url_name,
                "url": url,
                "tool": tool_name,
                "ok": res.get("ok"),
                "exit_code": res.get("exit_code"),
                "output_file": str(out_file),
                **summarize(stdout),
            }
            if not res.get("ok"):
                row["error"] = res.get("error") or stderr[:500]
            results["results"].append(row)
            print(json.dumps(row, ensure_ascii=False)[:1000], flush=True)
    summary_file = OUT / f"{stamp}_summary.json"
    summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUMMARY={summary_file}")


if __name__ == "__main__":
    main()
