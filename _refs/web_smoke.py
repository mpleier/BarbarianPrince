"""Smoke test for the web front-end: drive the FastAPI server end to end.

    python src/web.py --port 8011        (in one terminal)
    python _refs/web_smoke.py --port 8011
"""
import argparse
import json
import urllib.request

def make(base):
    def get(path):
        return urllib.request.urlopen(base + path).read()

    def post(path, body):
        req = urllib.request.Request(base + path,
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(req).read().decode())
    return get, post


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8011)
    args = ap.parse_args()
    base = f'http://127.0.0.1:{args.port}'
    get, post = make(base)

    board = json.loads(get('/api/board').decode())
    print('board: %d hexes, %d road sides, %d river sides, bounds %s'
          % (len(board['hexes']), len(board['roads']), len(board['rivers']),
             (board['minx'], board['miny'], board['maxx'], board['maxy'])))
    terrains = sorted({h['terrain'] for h in board['hexes']})
    print('terrains:', terrains)
    print('terrain colours cover all:', all(t in board['terrain_colors'] for t in terrains))
    print('scan underlay:', board['scan'])

    st = post('/api/game', {'seed': 42})
    print('\nnew game %s: day %d hex %s gold %d' % (st['session'], st['status']['day'],
                                                    st['status']['hex'], st['status']['gold']))
    print('first prompt:', st['prompt']['title'])
    for i, o in enumerate(st['prompt']['options']):
        print('   %d. %s  (hex=%s)' % (i, o['label'], o['hex']))
    print('highlighted moves:', st['moves'])

    turns = 0
    while not st['status']['game_over'] and st['prompt'] and turns < 60:
        st = post('/api/game/%s/answer' % st['session'], {'index': 0})
        turns += 1
    print('\nafter %d choices: day %d hex %s gold %d food %d party %s'
          % (turns, st['status']['day'], st['status']['hex'], st['status']['gold'],
             st['status']['food'], st['status']['party']))
    print('game_over:', st['status']['game_over'], '| reason:', st['status']['reason'])
    print('log lines:', st['log_count'])

    print('\nref r204:', get('/api/ref/r204').decode()[:80])
    print('hex 1212:', json.loads(get('/api/hex/1212').decode()))

    html = get('/').decode()
    print('\nindex.html:', len(html), 'bytes')
    print('app.js:', len(get('/app.js').decode()), 'bytes')
    print('style.css:', len(get('/style.css').decode()), 'bytes')
    print('scan jpg:', len(get('/scan/board.jpg')), 'bytes')


if __name__ == '__main__':
    main()
