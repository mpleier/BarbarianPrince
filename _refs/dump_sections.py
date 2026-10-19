"""Dump the readable rules sections (r201-r343) to a text file for inspection."""
import re

t = open("rules_clean.txt", encoding="utf-8").read()
start = t.find("r201 Characters")
end = t.find("Barbarian Prince Copyright 1981, Heritage USA 8700")
if end < 0:
    end = start + 60000
body = t[start:end]
body = re.sub(r"\n\s*\n", "\n", body)
open("rules_sections.txt", "w", encoding="utf-8").write(body)
print(len(body), "chars,", body.count("\n"), "lines")
