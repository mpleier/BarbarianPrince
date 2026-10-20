"""Trace every hire attempt and every horse-dealer appearance.

The horse dealer (r210, hire roll 5 or 10) is the only way to get a mount, so
this answers the two questions the detour logic depends on: how often the bot
stands in a town with 10+ gold, and how often it actually rolls 5 or 10.
"""
import sys
sys.path.insert(0, 'src')

from engine import Game
from autoplay import Bot


def run(seed):
    g = Game(seed=seed)
    b = Bot(g, 'balanced')
    stats = {'town_days': 0, 'hire_attempts': 0, 'dealers': 0,
             'bought': 0, 'wants': 0, 'at_town_with_gold': 0}
    orig_menu = g.daily_menu
    orig_choose = b.choose

    def menu():
        if g.place_kind(g.hex) in ('town', 'castle') and g.gold >= 10 \
                and len(g.living()) == 1:
            stats['at_town_with_gold'] += 1
            if b.wants_horse():
                stats['wants'] += 1
        return orig_menu()

    def choose(prompt, record=True):
        idx = orig_choose(prompt, record)
        if 'hiring' in prompt.get('title', '').lower():
            stats['hire_attempts'] += 1
        if 'horse' in prompt.get('title', '').lower():
            stats['dealers'] += 1
            label = prompt['options'][idx]['label'].lower()
            if 'buy' in label:
                stats['bought'] += 1
        return idx

    g.daily_menu = menu
    b.choose = choose
    g.run_until_idle(max_steps=6000, chooser=b.choose)
    return stats, g.speed(), g.staff


def main(n):
    tot = {}
    dealers = 0
    mounted = 0
    wins = 0
    for s in range(1, n + 1):
        st, speed, win = run(s)
        for k, v in st.items():
            tot[k] = tot.get(k, 0) + v
        if speed >= 2:
            mounted += 1
        wins += win
    print(f'{n} campaigns')
    for k, v in tot.items():
        print(f'  {k:<20} {v/n:8.2f} per campaign')
    print(f'  ended mounted: {mounted}/{n}')
    print(f'  wins: {wins}/{n}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
