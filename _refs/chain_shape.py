"""Analyse the traced river chains: build the side-adjacency graph of each chain
(two sides are adjacent when they share a hex and a vertex) and print the
resulting paths / junctions."""
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from geometry import board_xy

SIDES = json.load(open('_refs/sides_traced.json', encoding='utf-8'))


def shared_edge(a, b):
    p1, p2 = board_xy(*a), board_xy(*b)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    vx, vy = p2[0] - p1[0], p2[1] - p1[1]
    n = math.hypot(vx, vy)
    px, py = -vy / n, vx / n
    return (mx + px * 106.0 / 2, my + py * 106.0 / 2), \
           (mx - px * 106.0 / 2, my - py * 106.0 / 2)


def analyse(chain):
    sides = [tuple(map(tuple, s)) for s in chain]
    pts = {s: shared_edge(*s) for s in sides}
    adj = defaultdict(set)
    for i, s1 in enumerate(sides):
        for s2 in sides[i + 1:]:
            if set(s1) & set(s2):
                p1, q1 = pts[s1]
                p2, q2 = pts[s2]
                d = min(math.hypot(p1[0]-p2[0], p1[1]-p2[1]),
                        math.hypot(p1[0]-q2[0], p1[1]-q2[1]),
                        math.hypot(q1[0]-p2[0], q1[1]-p2[1]),
                        math.hypot(q1[0]-q2[0], q1[1]-q2[1]))
                if d < 25:
                    adj[s1].add(s2)
                    adj[s2].add(s1)
    deg = {s: len(adj[s]) for s in sides}
    ends = [s for s in sides if deg[s] <= 1]
    junc = [s for s in sides if deg[s] >= 3]
    return sides, adj, ends, junc


def walk(adj, start):
    seen = [start]
    cur = start
    while True:
        nxt = [n for n in adj[cur] if n not in seen]
        if not nxt:
            break
        cur = nxt[0]
        seen.append(cur)
    return seen


for ci, chain in enumerate(SIDES['chains']):
    sides, adj, ends, junc = analyse(chain)
    print('--- chain %d: %d sides, %d ends, %d junctions' % (ci, len(sides), len(ends), len(junc)))
    for e in ends:
        path = walk(adj, e)
        print('  path %d: %s' % (len(path), ' '.join('%s%s-%s%s' % (a[0], a[1], b[0], b[1]) for a, b in path)))
    print()
