import ast, sys

lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
items = []
for l in lines:
    if '\t' not in l:
        continue
    pos, tok = l.split('\t', 1)
    if pos == 'None':
        continue
    items.append((ast.literal_eval(pos), tok))
items.sort(key=lambda t: (-t[0][1], t[0][0]))
for p, t in items:
    print(f"{p[0]:7.1f} {p[1]:7.1f} {t}")
