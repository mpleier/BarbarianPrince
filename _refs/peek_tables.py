"""Print raw context around key table headings so the numeric tables can be recovered."""
import re

t = open("rules_raw.txt", encoding="latin-1", errors="replace").read()
t = re.sub(r"[^\x20-\x7e\r\n]+", " ", t)
t = re.sub(r"[ \t]{2,}", " ", t)

for key in ["Combat Table", "Treasure Table", "wealth code", "Trap Locks", "Food", "Lodging",
            "Starvation", "Transport Capacities", "Searching a Ruins", "Seeking News",
            "Make at Offering", "Rafting on the Rivers", "Cache", "Escape & Hiding",
            "Wounds & Endurance", "Rest & Healing"]:
    i = t.find(key)
    print("=" * 70)
    print("KEY:", key, "at", i)
    if i >= 0:
        print(t[max(0, i - 100): i + 1600])
    print()
