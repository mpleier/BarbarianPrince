import sys, random, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

pc = collections.Counter()
mounts = collections.Counter()
travel = collections.Counter()
ruins = collections.Counter()
templ = collections.Counter()
gold_at_temple = []
wins = 0
paths = []

for s in range(1, N + 1):
    g = Game(seed=s)
    b = Bot(g, strategy)
    try:
        g.run_until_idle(max_steps=6000, chooser=b.choose)
    except Exception as exc:
        print(f'seed {seed} crashed: {exc}')
        continue
    wins += 1 if g.staff else 0
    pc[len(g.living())] += 1
    mounts[tuple(sorted(set(c.mount for c in g.living())))] += 1
    ru = sum(1 for l in g.log if 'Search the ruins' in l)
    tp = sum(1 for l in g.log if 'Offering of' in l)
    tr = sum(1 for l in g.log if l.startswith('Travel action'))
    ruins[ru] += 1
    templ[tp] += 1
    travel[tr] += 1
    first_t = next((i for i, l in enumerate(g.log) if 'Offering of' in l), None)
    if first_t is not None:
        gold_at_temple.append(gold_at_temple and 0 or 0)
    paths.append((g.hex, ru, tp, tr, g.gold, g.day))

print(f'seeds {N}  strategy {strategy}  wins {wins} ({wins/N:.1%})')
print('party size:', sorted(pc.items()))
print('mounts:', mounts.most_common(6))
print('travel days:', sorted(travel.items())[:14])
print('ruin days dist:', sorted(ruins.items())[:14])
print('temple days dist:', sorted(templ.items())[:14])
print('final hexes:', collections.Counter(p[0] for p in paths).most_common(10))
print('avg ruin days %.1f, avg temple days %.1f, avg travel days %.1f' % (
    sum(p[1] for p in paths) / N, sum(p[2] for p in paths) / N,
    sum(p[3] for p in paths) / N))
