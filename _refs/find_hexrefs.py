"""Find every 4-digit map hex reference in the events and rules text."""
import re
from collections import Counter

for name in ("events.txt", "rules.txt", "errata.txt"):
    t = open(name, encoding="utf-8", errors="replace").read()
    hits = re.findall(r"\b(\d{4})\b", t)
    c = Counter(hits)
    print(f"== {name}: {len(c)} distinct hex codes")
    for code, n in sorted(c.items()):
        # show a snippet around the first occurrence
        i = t.find(code)
        snip = t[max(0, i - 60):i + 60].replace("\n", " ")
        print(f"  {code} x{n}  ...{snip}...")
    print()
