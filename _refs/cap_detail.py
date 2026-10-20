"""Detailed macro sweep: for each ruin cap, report the campaign shape."""
import sys
sys.path.insert(0, 'src')
from engine import Game
from autoplay import Bot

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200

def avg(xs):
    return sum(xs) / len(xs) if xs else 0.0

for cap in (10, 30, 60, 100, 200, None):
    wins = 0
    t_days = []
    r_days = []
    offer_n = []
    offer_sum = []
    final_gold = []
    for seed in range(1, N + 1):
        g = Game(seed=seed)
        bot = Bot(g, 'balanced')
        if cap is not None:
            bot.ruins_cap = lambda cap=cap: cap
        st = {'day': g.day, 't': 0, 'r': 0, 'offers': 0, 'gold_spent': 0}

        def wrapped(prompt):
            i = bot.choose(prompt)
            title = prompt.get('title', '')
            if 'action in hex' in title.lower():
                label = prompt['options'][i]['label']
                kind = g.place_kind(g.hex)
                if g.day != st['day']:
                    st['day'] = g.day
                    if kind == 'temple':
                        st['t'] += 1
                    elif kind == 'ruins':
                        st['r'] += 1
                if 'Offer' in label:
                    st['offers'] += 1
                    st['gold_spent'] += int(label.split()[1])
            return i

        g.run_until_idle(max_steps=6000, chooser=wrapped)
        t_days.append(st['t'])
        r_days.append(st['r'])
        offer_n.append(st['offers'])
        offer_sum.append(st['gold_spent'])
        final_gold.append(g.gold)
        if g.staff:
            wins += 1

    print(f'cap {str(cap):>5}: win {100*wins/N:5.2f}%  temple days {avg(t_days):5.1f}  '
          f'ruin days {avg(r_days):5.1f}  offerings {avg(offer_n):5.1f}  '
          f'gold offered {avg(offer_sum):6.1f}  final gold {avg(final_gold):6.1f}')
