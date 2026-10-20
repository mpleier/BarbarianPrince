"""Exact camp DP for r212 offerings at a temple.

State: (days left, gold, permanent +1 omen, one-day omen, one-day influence)

The prince is alone for the whole campaign (no follower ever survives to
matter), so r215/r217 cost nothing: starvation and rough-sleeping rolls only
apply to followers, so a lone prince can skip meals and lodging for free.
The only real currency is gold spent on offerings and news.

Offering roll: 2d6 + 1 (for 10+ gold) + perm + omen + influence.
  14+  -> Staff of Command, win
  2    -> temple defiled, party imprisoned (camp over)
  7    -> +1 tomorrow
  12/13-> +3 tomorrow
News roll (r209): 2d6 + 1 (if spending 5+) + 1 (if wit >= 5)
  3 -> +50 gold, 4 -> permanent +1, 8 -> lose half gold
"""
import sys
sys.path.insert(0, 'src')
from functools import lru_cache

DICE = [(t, n) for t, n in zip(range(2, 13), (1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1))]
TOTAL = sum(n for _, n in DICE)
OFFERS = (1, 5, 10, 20, 50)
GOLD_CAP = 400


def offer_ev(d, g, perm, omen, inf, amount):
    """Expected win probability of offering `amount` gold with d days left."""
    if amount > g:
        return -1.0
    bonus = (1 if amount >= 10 else 0) + perm + omen + inf
    ng = g - amount
    if d <= 1:
        # last day: only an immediate 14+ matters
        return sum(n / TOTAL for t, n in DICE if t + bonus >= 14)
    ev = 0.0
    for t, n in DICE:
        total = t + bonus
        p = n / TOTAL
        if total >= 14:
            ev += p * 1.0
        elif total == 2:
            # r212 result 2 says the temple is defiled and the party is
            # arrested, but the engine has no prison mechanic (e061 has no
            # options), so in practice nothing happens.
            ev += p * value(d - 1, ng, perm, 0, 0)
        elif total == 7:
            ev += p * value(d - 1, ng, perm, 1, 0)
        elif total in (12, 13):
            # r212 result 12/13: the High Priest's influence is +3 tomorrow.
            ev += p * value(d - 1, ng, perm, 0, 3)
        else:
            ev += p * value(d - 1, ng, perm, 0, 0)
    return ev


def news_ev(d, g, perm, wit_high):
    if d <= 1:
        return 0.0
    spend = 5 if g >= 5 else 0
    bonus = (1 if spend else 0) + (1 if wit_high else 0)
    ev = 0.0
    for t, n in DICE:
        total = t + bonus
        p = n / TOTAL
        ng = g - spend
        np = perm
        if total == 3:
            ng = min(GOLD_CAP, ng + 50)
        elif total == 4:
            np = 1
        elif total == 8:
            ng = ng // 2
        ev += p * value(d - 1, ng, np, 0, 0)
    return ev


@lru_cache(maxsize=None)
def value(d, g, perm, omen, inf):
    if d <= 0:
        return 0.0
    g = min(g, GOLD_CAP)
    best = value(d - 1, g, perm, 0, 0)          # rest / do nothing
    act = 'rest'
    for a in OFFERS:
        if a <= g:
            v = offer_ev(d, g, perm, omen, inf, a)
            if v > best:
                best, act = v, a
    if g >= 5 and not perm:
        for wit in (0, 1):
            v = news_ev(d, g, perm, wit)
            if v > best:
                best, act = v, 'news'
    return best


def best_action(d, g, perm, omen, inf, wit_high):
    """Return (action, win_probability) for the exact DP."""
    best = value(d - 1, g, perm, 0, 0)
    act = 'rest'
    for a in OFFERS:
        if a <= g:
            v = offer_ev(d, g, perm, omen, inf, a)
            if v > best:
                best, act = v, a
    if g >= 5 and not perm:
        v = news_ev(d, g, perm, wit_high)
        if v > best:
            best, act = v, 'news'
    return act, best


if __name__ == '__main__':
    print('P(win) for a lone prince camping C days with G gold:')
    print('C\\G    20    40    60    80   100   150   200   300   400')
    for c in (10, 15, 20, 25, 30, 35, 40, 45, 50):
        row = ' '.join(f'{value(c, g, 0, 0, 0):.3f}' for g in
                       (20, 40, 60, 80, 100, 150, 200, 300, 400))
        print(f'{c:>3}  {row}')

    print('\nOptimal first action (no modifiers, no perm):')
    for c in (10, 20, 30, 40):
        for g in (10, 20, 40, 60, 80, 100, 150, 200, 300):
            a, v = best_action(c, g, 0, 0, 0, False)
            print(f'  C={c:>2} G={g:>3} -> {str(a):>5}  P={v:.3f}')

    print('\nValue of the permanent +1 (news) at C=30, G=100:')
    print('  no perm:', value(30, 100, 0, 0, 0))
    print('  perm   :', value(30, 100, 1, 0, 0))
    print('  omen   :', value(30, 100, 0, 1, 0))
    print('  influence:', value(30, 100, 0, 0, 1))
