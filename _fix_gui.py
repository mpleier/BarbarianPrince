import re
p = 'src/gui.py'
s = open(p, encoding='utf-8').read()
s = re.sub(r"\['x'\]", "['center'][0]", s)
s = re.sub(r"\['y'\]", "['center'][1]", s)
open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('patched ok')
