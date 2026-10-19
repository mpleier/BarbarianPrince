import re

t = open('_refs/rules_raw.txt', 'rb').read().decode('latin-1')
clean = re.sub(r'[^\x09\x0a\x20-\x7e]', ' ', t)
clean = re.sub(r'\s+', ' ', clean)

print('Four wounds:', [m.start() for m in re.finditer('Four wounds', clean)])
print('wounds count:', len(re.findall('wounds', clean)))
print('--- TREASURE ---')
print(clean[44600:46400])
print('--- HIRING r210 ---')
i = clean.find('r210 Seeking to Hire')
print(i, clean[i-200:i+2500] if i >= 0 else clean[clean.find('Hire'):clean.find('Hire')+2500])
print('--- AUDIENCE r211 ---')
i = clean.find('r211')
print(i, clean[i-200:i+2500])
print('--- OFFERINGS r212 ---')
i = clean.find('r212')
print(i, clean[i-200:i+2500])
