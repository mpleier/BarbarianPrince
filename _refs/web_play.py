"""Play a scripted game through the web API to exercise the whole engine.

    python src/web.py --port 8011
    python _refs/web_play.py --port 8011 --seed 7
"""
import argparse
import json
import urllib.request


def post(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8011)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--turns', type=int, default=200)
    args = ap.parse_args()
    base = f'http://127.0.0.1:{args.port}'

    st = post(base, '/api/game', {'seed': args.seed})
    move_prompts = 0
    clicks = 0
    for _ in range(args.turns):
        if st['status']['game_over'] or not st['prompt']:
            break
        opts = st['prompt']['options']
        idx = 0
        if st['moves']:
            move_prompts += 1
            visited = set(st['status']['visited'])
            fresh = [i for i, o in enumerate(opts)
                     if o['hex'] in st['moves'] and o['hex'] not in visited]
            idx = fresh[0] if fresh else next(
                i for i, o in enumerate(opts) if o['hex'] in st['moves'])
            clicks += 1
        st = post(base, '/api/game/%s/answer' % st['session'], {'index': idx})

    print('day %d  hex %s  gold %d  food %d  wit %d' %
          (st['status']['day'], st['status']['hex'], st['status']['gold'],
           st['status']['food'], st['status']['wit']))
    print('party:', ', '.join(st['status']['party']))
    print('visited:', len(st['status']['visited']), 'hexes')
    print('caches:', st['status']['caches'], 'items:', st['status']['items'])
    print('move prompts (map-clickable):', move_prompts)
    print('game_over:', st['status']['game_over'], '|', st['status']['reason'])
    print('log lines:', st['log_count'])
    print('\nlast 12 log lines:')
    for line in st['log'][-12:]:
        print('  ', line)


if __name__ == '__main__':
    main()
