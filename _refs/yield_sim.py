"""Measure the real per-day yield of each repeatable action using the engine.

The engine rolls 2d6 for ruins/news/audience (r208, r209, r211), so the
expected gold per day has to be measured, not guessed.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game

TRIALS = 30000
rng = random.Random(11)

RUINS = {int(k): v for k, v in Game().model.tables['ruins_search'].items()}
NEWS = {int(r['roll']): r['text'] for r in Game().model.tables['news']}

# Hand-rolled expected value of each ruins event (gold only, ignoring risk).
RUINS_EV = {
    'e131': 0,      # empty ruins
    'e132': 0,      # organised search: extra roll if party > 1
    'e133': 50,     # plague: 50 gold, party madness
    'e134': 0,      # unstable ruins, injuries
    'e135': 0,      # broken columns (only useful with a scholar)
    'e136': 500 / 6,  # 1-e037 2-e038 3-e039 4-e044 5-500 6-nothing
    'e137': 0,      # inhabitants: combat
    'e138': 0,      # unclean: combat, then search again
    'e139': (25 + 60) / 6,  # minor treasure
    'e035': 0,      # spell of chaos: party destroyed
}

print('=== r208 ruins search (2d6 + skill-6+ followers) ===')
for bonus in (0, 1, 2):
    gold = 0.0
    rolls = 0
    disaster = 0
    for _ in range(TRIALS):
        total = rng.randint(1, 6) + rng.randint(1, 6) + bonus
        rolls += 1
        code = RUINS.get(min(12, max(2, total)), 'e133')
        gold += RUINS_EV.get(code, 0)
        if code == 'e035':
            disaster += 1
        if code in ('e132', 'e138'):
            # extra search the same day
            t2 = rng.randint(1, 6) + rng.randint(1, 6) + bonus
            rolls += 1
            gold += RUINS_EV.get(RUINS.get(min(12, max(2, t2)), 'e133'), 0)
    print(f'  bonus {bonus}: {gold / TRIALS:6.2f} gold/day  '
          f'({disaster / TRIALS:.3f} chaos-disasters per day)')

print()
print('=== r209 news seek (2d6 + gold/wit bonus) ===')
for bonus in (0, 1, 2):
    gold = 0.0
    omen = 0
    for _ in range(TRIALS):
        total = rng.randint(1, 6) + rng.randint(1, 6) + bonus
        text = NEWS.get(min(12, max(2, total)), '').lower()
        if 'gain 50 gold' in text:
            gold += 50
        if 'lose half your wealth' in text:
            gold -= 25
        if 'add one (+1)' in text and 'offerings' in text:
            omen += 1
    print(f'  bonus {bonus}: {gold / TRIALS:6.2f} gold/day, '
          f'omen chance {omen / TRIALS:.4f} (1 in {TRIALS / max(1, omen):.1f})')

