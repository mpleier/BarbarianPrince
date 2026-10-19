"""Unified hex-grid model for the BarbarianPrince board.

Geometry (verified against the two board scans):
  flat-top hexes, 20 columns x 23 rows = 460 hexes
  hex id = CCRR (column 01-20, row 01-23)
  map1.jpg holds rows 01-12, map2.jpg holds rows 12-23 (row 12 straddles the fold)
"""
import json
import math
import numpy as np
from PIL import Image

SQ3 = math.sqrt(3.0)
R = 106.0
NC, NR = 20, 23
DX, DY = 1.5 * R, SQ3 * R

# x0, y0 of the (col=1, row=r0) hex centre in that scan
PAR = {'map1.jpg': (377.0, 96.0, 1), 'map2.jpg': (377.0, 199.0, 13)}
IMG = {p: np.asarray(Image.open(p).convert('RGB'), dtype=np.int16) for p in PAR}
SZ = {p: IMG[p].shape[:2] for p in PAR}

SIDE_ANGLE = [30, 90, 150, 210, 270, 330]
SIDE_NAME = ['SE', 'S', 'SW', 'NW', 'N', 'NE']


def centre(col, row, scan):
    x0, y0, r0 = PAR[scan]
    i = col - 1
    return x0 + DX * i, y0 + DY * (row - r0) + (i % 2) * DY / 2.0


def best_scan(col, row):
    """Pick the scan in which this hex is most completely visible."""
    best, bs = -1, None
    for p in PAR:
        H, W = SZ[p]
        cx, cy = centre(col, row, p)
        area = max(0, min(H, cy + R) - max(0, cy - R)) * max(0, min(W, cx + R) - max(0, cx - R))
        if area > best:
            best, bs = area, p
    return bs


def sample_hex(col, row, rad=0.72):
    scan = best_scan(col, row)
    A = IMG[scan]
    H, W = A.shape[:2]
    cx, cy = centre(col, row, scan)
    x1, x2 = max(0, int(cx - rad * R)), min(W, int(cx + rad * R))
    y1, y2 = max(0, int(cy - rad * R)), min(H, int(cy + rad * R))
    sub = A[y1:y2, x1:x2].astype(np.float32)
    if sub.size == 0:
        return np.zeros((0, 3))
    ys, xs = np.mgrid[y1:y2, x1:x2]
    m = np.hypot(xs - cx, ys - cy) <= rad * R
    px = sub[m]
    keep = px.min(axis=1) < 195          # drop white grid lines / label text
    return px[keep]

def feats(px):
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    lum = px.mean(axis=1)
    return np.array([
        r.mean(), g.mean(), b.mean(),
        (lum < 90).mean(),                              # very dark ink (tree canopies)
        (lum > 200).mean(),                             # white (snow, water glare)
        ((r > g + 12) & (r > b + 12)).mean(),           # red-brown
        ((g > r + 12) & (g > b + 12)).mean(),           # bright grass green
        ((b > g + 8) & (b > r + 8)).mean(),             # blue
        ((r > 150) & (g > 150) & (b < 130)).mean(),     # yellow-green
    ])




TRAIN = {
    'desert': ['0106','0206','1406','1606','0307','0407','1307','1407','1507','1607',
               '1208','1308','1408','1508','1209','1309','1409','1509','1210','1310','1410','1710'],
    'badlands': ['0801','0901','1002','1103','1602','0204','0804','1604','1904','2003',
                 '0105','0205','0505','1305','1805','2005','0306','0406','0506','0806','1306',
                 '1107','1608','1808','2008','1009','1109','1609','1809','2009','1010','1110',
                 '1510','2010','1613','1713','1913','1113','1615','1715'],
    'mountains': ['0201','0301','1401','1701','1801','1901','1006','1106','1206','1506','1706',
                  '1007','1207','1707','1807','1907','0403','0503','0703','1603','1703','1903',
                  '0304','0404','0704','1104','1708','1908','1709','1909','1610','1810','0103',
                  '1111','1211','1511','2011','1012','1112','1512','2012'],
    'forest': ['0401','0501','0202','0302','0802','0902','1102','0203','0303','0803','0903',
               '1203','1503','1204','1304','1404','1504','0405','0605','0705','0606','0408',
               '0508','0708','0808','0209','0309','0409','0609','0709','0809','0310','0410',
               '0710','0810','0111','0711','0811','0112','0513','0613','0813','0314','0414',
               '0514','0814','0215','0315','0515','0715','0815','0516','0716','1315','1616',
               '1816','1717','1817','2017','0117','0517','1117'],
    'countryside': ['0102','0104','0110','0210','0402','0502','0601','0701','0702','0905',
                    '0906','1301','1303','1403','1803','2001','2004','0108','0208','0308',
                    '0909','0910','0510','1910','1806','1906','2006','0507','0607','0707',
                    '0907','1004','0608','0101','1001','1302','1704','1501','1502','1005',
                    '0504','0604','0405','0805','1705','1905','0211','0311','0611','0911',
                    '1311','1411','1711','1911','0212','0512','0413','0713','1413','1513',
                    '1813','0714','0914','1014','1314','1514','1914','2014','0415','1015',
                    '1215','1515','1715','1915','0316','0416','1116','1216','1516','1716',
                    '0417','0617','0717','1217','1517'],
    'farmland': ['0216','0217','0317','0816','0916','0917','1316','1416','1317','1417','0817',
                 '0915','1415'],
    'swamp': ['0213','0313','0613','0114','0214','0614','0115','0615','0616','1016','1017',
              '1616','1916','0411','0511','0312'],
}


def centroids():
    C = {}
    for name, hs in TRAIN.items():
        fs = []
        for h in hs:
            px = sample_hex(int(h[:2]), int(h[2:]))
            if len(px) > 3000:
                fs.append(feats(px))
        C[name] = np.mean(fs, axis=0)
    return C


def neighbour(col, row, side):
    i, j = col - 1, row - 1
    if side == 1:   ni, nj = i, j + 1
    elif side == 4: ni, nj = i, j - 1
    elif side == 0: ni, nj = i + 1, j if i % 2 == 0 else j + 1
    elif side == 5: ni, nj = i + 1, j if i % 2 == 0 else j - 1
    elif side == 2: ni, nj = i - 1, j if i % 2 == 0 else j + 1
    else:           ni, nj = i - 1, j if i % 2 == 0 else j - 1
    if 1 <= ni + 1 <= NC and 1 <= nj + 1 <= NR:
        return ni + 1, nj + 1
    return None


def build():
    C = centroids()
    names = list(C)
    hexes = []
    for col in range(1, NC + 1):
        for row in range(1, NR + 1):
            px = sample_hex(col, row)
            hid = f'{col:02d}{row:02d}'
            nb = {}
            for s in range(6):
                n = neighbour(col, row, s)
                if n:
                    nb[SIDE_NAME[s]] = f'{n[0]:02d}{n[1]:02d}'
            if len(px) < 1500:
                t, dist = 'unknown', 999.0
            else:
                f = feats(px)
                d = {n: float(np.linalg.norm(f - C[n])) for n in names}
                t = min(d, key=d.get)
                dist = d[t]
            hexes.append({'id': hid, 'col': col, 'row': row, 'terrain': t,
                          'dist': round(dist, 2), 'neighbors': nb})
    return hexes


if __name__ == '__main__':
    hexes = build()
    json.dump(hexes, open('hexes.json', 'w'), indent=1)
    from collections import Counter
    print(Counter(h['terrain'] for h in hexes))
    print('total', len(hexes))
    for h in hexes:
        if h['dist'] > 55:
            print('low confidence:', h['id'], h['terrain'], h['dist'])