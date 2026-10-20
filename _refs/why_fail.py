"""Diagnose why campaigns fail: where the days and the gold go."""
import sys
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
strategy = sys.argv[2] if len(sys.argv) > 2 else 'balanced'

wins = 0
reasons = Counter()
camp_days = []
ruin_days = 0
travel_days = 0
offer_days = 0
news_days = 0
modifier_games = 0
win_days = []

for seed in range(1, N + 1):
    g = Game(seed=seed)
    b = Bot(g, strategy)
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    if g.staff:
        wins += 1
        win_days.append(g.day)
    reasons[g.reason] += 1
    camp_days.append(b.camp_days())
    ruin_days += sum(1 for l in g.log if 'Searching the ruins' in l)
    travel_days += sum(1 for l in g.log if l.startswith('Travel action'))
    offer_days += sum(1 for l in g.log if 'Offering of' in l)
    news_days += sum(1 for l in g.log if 'Seeking news' in l)
    if g.offering_bonus:
        modifier_games += 1

print(f'{N} games, {strategy}: wins {wins} ({wins / N:.1%})')
print('reasons:', reasons.most_common(6))
print(f'avg ruin-search days {ruin_days / N:.1f}, avg travel actions {travel_days / N:.1f}')
print(f'avg offering attempts {offer_days / N:.1f}, avg news attempts {news_days / N:.1f}')
print(f'avg camp days {sum(camp_days) / N:.1f}')
print(f'games with the permanent news omen: {modifier_games} ({modifier_games / N:.1%})')
if win_days:
    print(f'avg win day {sum(win_days) / len(win_days):.1f}')
