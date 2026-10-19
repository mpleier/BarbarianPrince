"""Clean the raw DOC dumps into readable text so tables can be parsed."""
import re

SRC = "rules_raw.txt"
OUT = "rules_clean.txt"

t = open(SRC, encoding="latin-1", errors="replace").read()

# Drop the OLE/Word binary preamble.
t = t[t.find("EMBED Microsoft Word Picture"):] if "EMBED Microsoft Word Picture" in t else t

# Keep printable ascii, collapse whitespace.
t = re.sub(r"[^\x20-\x7e\r\n]+", " ", t)
t = t.replace("\r", "\n")
t = re.sub(r"[ \t]{2,}", " ", t)
t = re.sub(r"\n{3,}", "\n\n", t)

open(OUT, "w", encoding="utf-8").write(t)
print(len(t), "chars ->", OUT)
