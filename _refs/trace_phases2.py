"""Print the phase transitions of a campaign so we can see where days leak."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

for seed in (int(x) for x in sys.argv[1:]):
    g = Game(seed=seed)
    bot = Bot(g, 'cautious')
    rows = []

    def wrapped(prompt):
        i = bot.choose(prompt)
        title = prompt.get('title', '').lower()
        if 'action in hex' in title:
            rows.append((g.day, g.hex, g.place_kind(g.hex) or 'open',
                         g.gold, len(bot.party()),
                         g.offering_bonus, g.influence_bonus, g.omen_bonus,
                         prompt['options'][i]['label']))
        return i

    g.run_until_idle(max_steps=6000, chooser=wrapped)
    print(f'=== seed {seed}  win={bool(g.staff)}  gold={g.gold} ===')
    prev = None
    for d, h, k, gold, party, pb, ib, ob, label in rows:
        if prev is None or prev[1] != h or prev[4] != label.split('(')[0]:
            print(f'  day {d:>3} {h} {k:<7} gold {gold:>4} party {party} '
                  f'perm {pb} infl {ib} omen {ob}  -> {label}')
        prev = (d, h, k, gold, label.split('(')[0])
    print(f'  total action days: {len(rows)}')
