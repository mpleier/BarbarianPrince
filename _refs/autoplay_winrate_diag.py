"""Win-rate harness with diagnostics: where does the bot lose its days?

Usage: python _refs/autoplay_winrate_diag.py [N]
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def run(strategy, seed):
    g = Game(seed=seed)
    bot = Bot(g, strategy)
    g.run_until_idle(max_steps=6000, chooser=bot.choose)
    offerings = sum(1 for line in g.log if 'Offering of' in line)
    temple_days = 0
    first_temple = None
    for i, line in enumerate(g.log):
        if 'begins in hex' in line:
            hex_ = line.split('hex ')[1].strip('.')
            if g.place_kind(hex_) == 'temple':
                temple_days += 1
                if first_temple is None:
                    first_temple = g.day
    omens = sum(1 for line in g.log if 'Favourable omens' in line)
    influence = sum(1 for line in g.log if 'influence' in line.lower())
    news_omen = sum(1 for line in g.log if 'omen' in line.lower()
                     and 'news' in line.lower())
    return dict(won=g.won, day=g.day, gold=g.gold, peak=g.peak_gold,
                offerings=offerings, temple_days=temple_days,
                first_temple=first_temple, omens=omens, influence=influence,
                news_omen=news_omen, hex=g.hex)


for strategy in ('cautious', 'balanced', 'aggressive'):
    games = [run(strategy, s) for s in range(1, N + 1)]
    wins = sum(1 for x in games if x['won'])
    off = sum(x['offerings'] for x in games)
    td = sum(x['temple_days'] for x in games)
    reached = sum(1 for x in games if x['temple_days'])
    print(f'{strategy:11} wins {wins}/{N}  offerings {off}  '
          f'temple days {td}  reached temple {reached}/{N}')
    print('    avg gold %.1f  peak %.1f  avg first temple day %s'
          % (sum(x['gold'] for x in games) / N,
             sum(x['peak'] for x in games) / N,
             round(sum(x['first_temple'] or 0 for x in games)
                   / max(1, reached), 1)))
    never = [x for x in games if not x['temple_days']]
    if never:
        print('    stuck games: final gold %s, final hex %s'
              % (round(sum(x['gold'] for x in never) / len(never)),
                 Counter(x['hex'] for x in never).most_common(5)))
