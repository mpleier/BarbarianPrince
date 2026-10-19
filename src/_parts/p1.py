"""Rules-accurate Barbarian Prince game engine (r201-r228 core loop).

The engine is UI-agnostic: it maintains a queue of *prompts* that any interface
(tkinter GUI, CLI, tests) can render and answer.

Prompt kinds
  'encounter'  an event with a talk / evade / fight option matrix
  'combat'     a round-by-round battle (r220)
  'choice'     a plain decision
  'info'       text the player must acknowledge
"""
import json
import os
import random
import re

from game_model import GameModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

GAME_DAYS = 70
TARGET_GOLD = 500

# r220c Combat Results Table
COMBAT_TABLE = {-1: 1, 3: 1, 5: 1, 8: 1, 11: 1,
                10: 2, 12: 2, 13: 2, 17: 2,
                14: 3, 16: 5, 18: 5, 19: 5, 20: 6}

# r330 Battle Reference
BATTLE_REFERENCE = {2: 'r310', 3: 'r309', 4: 'r308', 5: 'r307', 6: 'r306',
                    7: 'r305', 8: 'r304', 9: 'r303', 10: 'r302', 11: 'r301',
                    12: 'r300'}

# r341 Conversation
CONVERSATION = {2: 'r310', 3: 'r308', 4: 'r305', 5: 'r331', 6: 'r332', 7: 'r333',
                8: 'r338', 9: 'r335', 10: 'r336', 11: 'r340', 12: 'r334'}

# r342 General Inquiry
INQUIRY = {2: 'r309', 3: 'r330', 4: 'r340', 5: 'r306', 6: 'r325', 7: 'r341',
           8: 'r333', 9: 'r339', 10: 'r337', 11: 'r338', 12: 'r336'}

REF_RE = re.compile(r'\b([re]\d{3})\b')
STAT_RE = re.compile(r'combat skill (\d+)(?:,\s*(?:and\s*)?endurance (\d+))?'
                     r'(?:,\s*wealth (\d+))?')
DIRECTIONS = ['N', 'NE', 'SE', 'S', 'SW', 'NW']
HUNT_TERRAIN = ('Farmland', 'Countryside', 'Forest', 'Hills')
POPULATED = ('town', 'castle', 'temple')


def threshold(spec):
    """'10+' -> 10, 'never' -> None, '-' -> None."""
    if not spec:
        return None
    m = re.search(r'\d+', spec)
    return int(m.group(0)) if m else None


def parse_options(text):
    """Extract the 'die roll / talk / evade / fight' option matrix of an event."""
    idx = text.find('Your options are:')
    if idx < 0:
        return None
    body = text[idx + len('Your options are:'):]
    star = body.find('*')
    note = body[star:].strip() if star >= 0 else ''
    if star >= 0:
        body = body[:star]
    tokens = body.split()
    i = 0
    headers = []
    while i < len(tokens) and not tokens[i].isdigit():
        h = tokens[i].strip('*').strip()
        if h.lower() not in ('die', 'roll'):
            headers.append(h)
        i += 1
    if not headers:
        return None
    rows = []
    while i < len(tokens):
        if not tokens[i].isdigit():
            i += 1
            continue
        roll = int(tokens[i])
        i += 1
        cells = []
        while i < len(tokens) and not tokens[i].isdigit():
            label = []
            while (i < len(tokens) and not tokens[i].isdigit()
                   and not re.fullmatch(r'[re]\d{3}', tokens[i])):
                label.append(tokens[i])
                i += 1
            if i < len(tokens) and re.fullmatch(r'[re]\d{3}', tokens[i]):
                cells.append((' '.join(label) or 'option', tokens[i]))
                i += 1
            else:
                break
        if cells:
            rows.append((roll, cells))
    return headers, rows, note


def parse_foes(text):
    """Parse the stat block(s) of the characters an event describes."""
    stats = [(int(s), int(e) if e else 5, int(w) if w else 0)
             for s, e, w in STAT_RE.findall(text)]
    if not stats:
        return []
    count = 1
    low = text.lower()
    if 'roll one die for the number of' in low:
        count = random.randint(1, 6)
    elif 'roll two dice for the number of' in low:
        count = random.randint(1, 6) + random.randint(1, 6)
    elif 'number in the group is one die roll plus one' in low:
        count = random.randint(1, 6) + 1
    else:
        m = re.search(r'(\d+)\s+(?:men|warriors|guards|tribesmen|bandits|horsemen|'
                      r'assassins|constables|priests|monks|witches|magicians|wizards|'
                      r'dwarves|elves|orcs|giants|trolls|centaurs|amazons|mercenaries|'
                      r'henchmen|retainers|riders|thugs|soldiers|pirates|nomads|'
                      r'bodyguards|guardsmen|peasants|villagers|outlaws|robbers)\b', low)
        if m:
            count = int(m.group(1))
    return [Character(f'Foe {i + 1}', *(stats[i % len(stats)])) for i in range(count)]
