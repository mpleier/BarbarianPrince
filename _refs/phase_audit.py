"""Where the campaign's 70 days actually go, phase by phase.

Phases:  start -> planned ruin  |  mining  |  ruin -> temple  |  camping.
Wandering days (travel that is not on the planned route) are counted
separately, because every one of them costs gold in food and lodging.
"""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from engine import Game
from autoplay import Bot


def trace(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    ruin = plan[1] if plan else None
    temple = plan[2] if plan else None
    phase = 'approach'
    counts = {'approach': 0, 'mine': 0, 'transit': 0, 'camp': 0, 'other': 0}
    while not g.game_over:
        g.advance()
        if not g.prompts:
            break
        p = g.current()
        idx = b.choose(p)
        title = p.get('title', '')
        if 'action in hex' in title.lower():
            kind = g.place_kind(g.hex)
            if kind == 'ruins' and g.hex == ruin:
                phase = 'mine'
            elif kind == 'temple':
                phase = 'camp'
            elif phase == 'mine':
                phase = 'transit'
            elif phase == 'approach':
                phase = 'approach'
            counts[phase] += 1
        g.answer(idx)
    return counts, ruin, temple, g.staff, g.gold


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    tot = {'approach': 0, 'mine': 0, 'transit': 0, 'camp': 0, 'other': 0}
    wins = 0
    for s in range(1, N + 1):
        c, ruin, temple, w, gold = trace(s)
        for k in tot:
            tot[k] += c[k]
        wins += w
    print(f'{N} campaigns, {wins} wins ({wins/N:.3f})')
    for k, v in tot.items():
        print(f'  {k:<9} {v/N:6.1f} days')
