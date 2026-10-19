"""Print a slice of the cleaned rules text to inspect the tail after r342."""
import re, sys

t = open("rules_clean.txt", encoding="utf-8").read()
i = t.find("r343 Victim Selection")
print(repr(t[i:i + 1500]))
print("----")
print("total len:", len(t))
