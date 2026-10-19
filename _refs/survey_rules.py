"""Survey the cleaned rules text: list every rNNN section header and its length."""
import re

t = open("rules_clean.txt", encoding="utf-8").read()
hits = [(m.start(), m.group(1)) for m in re.finditer(r"\n\s*(r\d{3})\s", t)]
print("section headers found:", len(hits))
for i, (pos, code) in enumerate(hits):
    end = hits[i + 1][0] if i + 1 < len(hits) else len(t)
    body = t[pos:end]
    print(f"{code} @ {pos} len={len(body)} :: {body[:90].strip()!r}")
