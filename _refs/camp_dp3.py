"""Exact DP for the temple-camp phase.

Each day at a temple the party pays lodging and then either
  - seeks news (r209): 4 -> permanent +1 to offerings, 3 -> +50 gold, 8 -> lose half
  - submits an offering (r212): 2d6 + 1 (10+ gold) + perm + omen + influence, 14+ wins

Compares the true optimum against the two obvious greedy policies so the bot's
weights can be derived from measured value rather than guesswork.
"""
from functools import lru_cache

DICE = {}
for a in range(1, 7):
    for b in range(1, 7):
        DICE[a + b] = DICE.get(a + b, 0) + 1
TOTAL = 36
GOLD_CAP = 300
STEP = 10
LODGING = 2


def q(g):
    return min(GOLD_CAP, int(g // STEP) * STEP)


def news_value(f, d, gold, perm, infl, omen):
    """One news-seeking day under continuation policy f."""
    nb = 1 if gold >= 5 else 0
    p = 0.0
    for dice, ways in DICE.items():
        total = min(12, max(2, dice + nb))
        ng = q(gold - LODGING)
        if total == 4:
            p += ways / TOTAL * f(d - 1, ng, 1, infl, omen)
        elif total == 3:
            p += ways / TOTAL * f(d - 1, q(ng + 50), perm, infl, omen)
        elif total == 8:
            p += ways / TOTAL * f(d - 1, q(ng // 2), perm, infl, omen)
        else:
            p += ways / TOTAL * f(d - 1, ng, perm, infl, omen)
    return p


def offer_value(f, d, gold, perm, infl, omen, amount):
    bonus = (1 if amount >= 10 else 0) + perm + omen + infl
    p = 0.0
    for dice, ways in DICE.items():
        total = dice + bonus
        ng = q(gold - amount - LODGING)
        if total >= 14:
            p += ways / TOTAL
        elif total == 7:
            p += ways / TOTAL * f(d - 1, ng, perm, 0, 1)
        elif total in (12, 13):
            p += ways / TOTAL * f(d - 1, ng, perm, 3, 0)
        else:
            p += ways / TOTAL * f(d - 1, ng, perm, 0, 0)
    return p


@lru_cache(maxsize=None)
def optimal(d, gold, perm, infl, omen):
    if d == 0:
        return 0.0
    best = news_value(optimal, d, gold, perm, infl, omen)
    for amount in (1, 5, 10, 20, 50):
        if amount <= gold:
            best = max(best, offer_value(optimal, d, gold, perm, infl, omen, amount))
    return best


def run(policy, d, gold):
    memo = {}

    def f(d, gold, perm, infl, omen):
        key = (d, gold, perm, infl, omen)
        if key in memo:
            return memo[key]
        if d == 0:
            return 0.0
        amount = policy(gold, perm, infl, omen)
        if amount is None or amount > gold:
            p = news_value(f, d, gold, perm, infl, omen)
        else:
            p = offer_value(f, d, gold, perm, infl, omen, amount)
        memo[key] = p
        return p
    return f(d, gold, 0, 0, 0)


offer10 = lambda gold, perm, infl, omen: 10 if gold >= 10 else (1 if gold >= 1 else None)
news_first = lambda gold, perm, infl, omen: None if not perm else (
    10 if gold >= 10 else (1 if gold >= 1 else None))
offer1_only = lambda gold, perm, infl, omen: 1 if gold >= 1 else None

print(f'{"days":>5} {"gold":>5} {"optimal":>8} {"offer10":>8} {"news-first":>11} {"offer1":>7}')
for days in (10, 20, 30, 40, 50, 60):
    for gold in (0, 50, 100, 150, 200, 300):
        print(f'{days:>5} {gold:>5} {optimal(days, q(gold), 0, 0, 0):>8.4f} '
              f'{run(offer10, days, q(gold)):>8.4f} '
              f'{run(news_first, days, q(gold)):>11.4f} '
              f'{run(offer1_only, days, q(gold)):>7.4f}')
    print()

# ---------------------------------------------------------------- macro plan
# 70 days total.  R days digging ruins, T days travelling, C = 70-R-T days
# camping at a temple.  Ruins measured at ~3.3 gold/search (balanced party).
print('=== macro plan: how many days should go to ruins vs. the temple? ===')
for travel in (10, 13, 16):
    D = 70 - travel
    print(f'travel {travel} days, {D} usable days')
    best = None
    for R in range(0, D + 1):
        C = D - R
        gold = 3.3 * R
        p = optimal(C, q(gold), 0, 0, 0)
        if best is None or p > best[0]:
            best = (p, R, C, gold)
        if R % 5 == 0:
            print(f'  R={R:3} C={C:3} gold {gold:6.1f}  P(win) {p:.4f}')
    print(f'  BEST: R={best[1]} C={best[2]} gold {best[3]:.0f} P={best[0]:.4f}\n')

def show_policy(d, gold, perm=0, infl=0, omen=0, depth=0):
    if d == 0 or depth > 12:
        return
    opts = [('news', news_value(optimal, d, gold, perm, infl, omen))]
    for amount in (1, 5, 10, 20, 50):
        if amount <= gold:
            opts.append((f'offer {amount}',
                         offer_value(optimal, d, gold, perm, infl, omen, amount)))
    opts.sort(key=lambda x: -x[1])
    print(f'  d={d:3} gold={gold:4} perm={perm} infl={infl} omen={omen} -> '
          + ', '.join(f'{k}:{v:.4f}' for k, v in opts[:4]))
    best = opts[0]
    if best[0] == 'news':
        show_policy(d - 1, q(gold - LODGING), 1, infl, omen, depth + 1)
    else:
        amount = int(best[0].split()[1])
        show_policy(d - 1, q(gold - amount - LODGING), perm, 0, 0, depth + 1)


print('=== optimal camp policy ===')
show_policy(30, 300)
show_policy(20, 200)
show_policy(15, 150)
print()

print('=== value of the permanent offering omen ===')
for days in (10, 20, 30, 40):
    for gold in (100, 150, 200, 300):
        no_omen = optimal(days, q(gold), 0, 0, 0)
        with_omen = optimal(days, q(gold), 1, 0, 0)
        print(f'{days:>4} days {gold:>4} gold: no omen {no_omen:.4f}  '
              f'omen {with_omen:.4f}  gain {with_omen - no_omen:+.4f}')
print()
print('=== paying for news: N days of news (5 gold + 2 lodging each) then camp ===')
for days in (57, 50, 45):
    for gold in (0, 100, 150):
        best = None
        for n in range(0, days):
            ng = max(0, gold - 7 * n)
            p = optimal(days - n, q(ng), 1, 0, 0)
            if best is None or p > best[0]:
                best = (p, n)
        print(f'{days:>4} days {gold:>4} gold: best {best[1]} news days -> {best[0]:.4f} '
              f'(vs 0 news days -> {optimal(days, q(gold), 0, 0, 0):.4f})')


