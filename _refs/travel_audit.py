"""Diagnose the travel legs: planned vs actual, and whether horses are bought.

For each campaign we compare the expected travel days the bot's Dijkstra model
predicts with the days it actually spends walking, and record how often the
party ever gets mounted (r204a doubles the daily move once every survivor has a
mount).
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot, TOTAL_DAYS


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    plan = b.plan()
    if not plan:
        return None
    _, ruin, temple = plan
    planned = b.travel_days(ruin).get(g.hex, 999.0) + \
        b.travel_days(temple).get(ruin, 999.0)
    orig = g.daily_menu
    days = []

    def wrapped():
        days.append((g.day, g.hex, g.place_kind(g.hex), g.gold,
                     len(g.party), sum(1 for c in g.living() if c.mount != 'none'),
                     g.speed()))
        return orig()
    g.daily_menu = wrapped
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    first_ruin = next((d for d, h, k, *_ in days if k == 'ruins'), None)
    first_temple = next((d for d, h, k, *_ in days if k == 'temple'), None)
    travel = sum(1 for d, h, k, gold, n, m, sp in days
                 if k not in ('ruins', 'temple'))
    return dict(planned=planned, first_ruin=first_ruin, first_temple=first_temple,
               travel=travel, party=len(g.living()),
               mounted=any(sp >= 2 for *_, sp in days),
               speed_days=sum(1 for *_, sp in days if sp >= 2),
               win=g.staff, gold=g.gold)


def main(n):
    rows = [r for r in (run(s) for s in range(1, n + 1)) if r]
    print(f'{n} campaigns')
    print(f'  planned travel (model)   {sum(r["planned"] for r in rows)/n:6.1f} days')
    print(f'  actual travel days       {sum(r["travel"] for r in rows)/n:6.1f}')
    print(f'  reached ruin on day      {sum(r["first_ruin"] for r in rows if r["first_ruin"])/max(1,sum(1 for r in rows if r["first_ruin"])):6.1f}')
    print(f'  reached temple on day    {sum(r["first_temple"] for r in rows if r["first_temple"])/max(1,sum(1 for r in rows if r["first_temple"])):6.1f}')
    print(f'  campaigns ever mounted   {sum(1 for r in rows if r["mounted"])}/{n}')
    print(f'  days at speed >= 2       {sum(r["speed_days"] for r in rows)/n:6.1f}')
    print(f'  final party size         {sum(r["party"] for r in rows)/n:6.1f}')
    print(f'  wins                     {sum(1 for r in rows if r["win"])}/{n}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
