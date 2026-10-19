"""Clean tables_raw.txt into a readable file."""
import re

t = open("tables_raw.txt", encoding="latin-1", errors="replace").read()
t = re.sub(r"[^\x20-\x7e\r\n]+", " ", t)
t = re.sub(r"[ \t]{2,}", " ", t)
lines = [l.strip() for l in t.splitlines()]
lines = [l for l in lines if l]
out = "\n".join(lines)
open("tables_clean.txt", "w", encoding="utf-8").write(out)
print("lines:", len(lines), "chars:", len(out))
