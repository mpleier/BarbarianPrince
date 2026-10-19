ls = open('tables_raw.txt', encoding='latin-1').read().splitlines()
for n in (15, 20):
    print('=== line', n, '===')
    print(ls[n - 1])
    print()
