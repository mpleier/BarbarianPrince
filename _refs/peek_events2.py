import re
t = open('events_raw.txt', encoding='latin-1').read()
i = t.find('e002')
print(repr(t[i-200:i+400]))
print('---')
i = t.find('e003')
print(repr(t[i-300:i+300]))
