"""Dump raw (line-preserving) slices of rules_raw.txt around a heading."""
import re
import sys

t = open("rules_raw.txt", encoding="latin-1", errors="replace").read()
key = sys.argv[1]
i = t.find(key)
if i < 0:
    print("NOT FOUND:", key)
else:
    print(t[max(0, i - 200): i + 2500])
