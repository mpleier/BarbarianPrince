"""Exact DP for the temple camp: r212 offerings and r209 news.

State: (days left, gold, permanent +1 omen, one-day omen, one-day influence)

By the time the prince camps he is almost always alone (followers die or
desert), and r215/r217 only roll for follower desertion, so a lone prince can
skip food and lodging for free.  The only real currency in the camp is gold
spent on offerings and news.

Offering roll: 2d6 + 1 (for 10+ gold) + perm + omen + influence
  14+   -> Staff of Command, win
  2     -> temple defiled, party arrested (the engine has no prison, so it
           is a no-op in practice)
  7     -> +1 on tomorrow's offering
  12/13 -> +3 influence on tomorrow's offering

News roll (r209): 2d6 + 1 (if spending 5+) + 1 (if wit >= 5)
  3 -> +50 gold, 4 -> permanent +1 to offerings, 8 -> lose half gold
"""
from functools import lru_cache

DICE = tuple(zip(range(2, 13), (1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1)))
TOTAL = 36
OFFERS = (1, 5, 10, 20, 50)
GOLD_CAP = 400
WIN = 14


def win_chance(bonus):
    """P(2d6 + bonus >= 14)."""
    return sum(n for t, n in DICE if t + bonus >= WIN) / TOTAL


def _offer(days, gold, perm, omen, influence, amount):
    bonus = (1 if amount >= 10 else 0) + perm + omen + influence
    left = gold - amount
    ev = 0.0
    for roll, count in DICE:
        total = roll + bonus
        p = count / TOTAL
        if total >= WIN:
            ev += p
        elif total == 7:
            ev += p * camp_value(days - 1, left, perm, 1, 0, False)
        elif total in (12, 13):
            ev += p * camp_value(days - 1, left, perm, 0, 3, False)
        else:
            ev += p * camp_value(days - 1, left, perm, 0, 0, False)
    return ev


def _news(days, gold, perm, wit_high):
    spend = 5 if gold >= 5 else 0
    bonus = (1 if spend else 0) + (1 if wit_high else 0)
    ev = 0.0
    for roll, count in DICE:
        total = roll + bonus
        p = count / TOTAL
        ng = gold - spend
        np = perm
        if total == 3:
            ng = min(GOLD_CAP, ng + 50)
        elif total == 4:
            np = 1
        elif total == 8:
            ng = ng // 2
        ev += p * camp_value(days - 1, ng, np, 0, 0, wit_high)
    return ev


@lru_cache(maxsize=None)
def camp_value(days, gold, perm, omen, influence, wit_high):
    """P(win) with `days` days left camped at a temple."""
    if days <= 0:
        return 0.0
    gold = min(gold, GOLD_CAP)
    best = camp_value(days - 1, gold, perm, 0, 0, wit_high)   # rest
    for amount in OFFERS:
        if amount <= gold:
            v = _offer(days, gold, perm, omen, influence, amount)
            if v > best:
                best = v
    if gold >= 5 and not perm:
        v = _news(days, gold, perm, wit_high)
        if v > best:
            best = v
    return best


def camp_action(days, gold, perm, omen, influence, wit_high):
    """Best camp action for the day: 'rest', 'news' or an offering amount.

    Ties are broken towards the cheapest offering.  When the pile is smaller
    than the number of camp days the DP is often indifferent between resting
    and spending 1 gold - the days that would have been wasted are the same
    either way - and spending keeps the 7 / 12 / 13 lottery rolling.
    """
    days = max(0, days)
    gold = min(gold, GOLD_CAP)
    best = None
    act = 'rest'
    for amount in OFFERS:
        if amount <= gold:
            v = _offer(days, gold, perm, omen, influence, amount)
            if best is None or v > best:
                best, act = v, amount
    if gold >= 5 and not perm:
        v = _news(days, gold, perm, wit_high)
        if best is None or v > best:
            best, act = v, 'news'
    rest = camp_value(days - 1, gold, perm, 0, 0, wit_high)
    if best is None or rest > best + 1e-12:
        best, act = rest, 'rest'
    return act

# ---------------------------------------------------------------- ruin phase
# Ruins are the only source of gold (see _refs/gold_flow.py): a search is a
# lottery that pays nothing 97.3% of the time, 60 gold 1.75%, 500 gold 0.97%.
# So the ruin phase is a stopping problem - at every day the party either takes
# another ticket or walks to the temple and starts spending.  Solving it exactly
# beats the old "mine until gold >= X" rule, because the threshold depends on
# how many camp days the remaining travel still leaves.
LOTTERY = [(0, 0.9733), (60, 0.0175), (500, 0.0097), (-10, 0.0005)]
GOLD_CAP = 400


@lru_cache(maxsize=None)
def ruin_value(days, gold, travel):
    """P(win) with `days` left, `gold` held, standing on a ruin `travel` days
    from the nearest temple."""
    if days <= 0:
        return 0.0
    gold = min(gold, GOLD_CAP)
    camp_now = camp_value(max(0, days - travel), gold, 0, 0, 0, False)
    if days <= travel:
        return camp_now
    mine = 0.0
    for amount, p in LOTTERY:
        mine += p * ruin_value(days - 1, min(GOLD_CAP, max(0, gold + amount)),
                              travel)
    return max(camp_now, mine)


def ruin_should_mine(days, gold, travel):
    """True when another day of searching beats walking to the temple now."""
    if days <= travel:
        return False
    camp_now = camp_value(max(0, days - travel), min(gold, GOLD_CAP),
                          0, 0, 0, False)
    mine = 0.0
    for amount, p in LOTTERY:
        mine += p * ruin_value(days - 1, min(GOLD_CAP, max(0, gold + amount)),
                              travel)
    return mine > camp_now + 1e-12


def ruin_gold_target(days, travel):
    """Largest gold for which mining is still worth it with `days` left."""
    target = 0
    for g in range(0, GOLD_CAP + 1, 5):
        if ruin_should_mine(days, g, travel):
            target = g
    return target

