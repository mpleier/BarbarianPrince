"""Quick check: compare specific hex features between model and map."""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '..', 'data')

with open(os.path.join(DATA, 'features.json'), encoding='utf-8') as f:
    feats = json.load(f)

rs_set = {frozenset(p) for p in feats['river_sides']}
rds_set = {frozenset(p) for p in feats['road_sides']}

print("=" * 70)
print("RIVER VERIFICATION: Model vs barbarianprince_onepiecemap-revc.jpg")
print("=" * 70)

print("\n  Tragoth River (upper edge, labeled ~0602):")
for a, b, desc in [
    ('0102','0201','NW entry'),('0801','0902','central mt'),
    ('0901','1002','central mt'),('1001','1102','east center'),
    ('1101','1202','east center'),('1202','1303','near 1303'),
    ('1301','1302','near 1302'),('1302','1401','near 1401'),
    ('1603','1703','SE gap'),('1703','1802','SE gap'),
    ('1802','1902','SE gap'),('1902','2001','NE exit'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Nesser River (center→SW, labeled ~0511):")
for a, b, desc in [
    ('1005','1006','upstream'),('0608','0709','mid-SW'),
    ('0709','0810','mid-SW'),('0411','0510','Branwyns'),
    ('0510','0511','Branwyns'),('0113','0213','left edge'),
    ('0113','0214','left edge'),('0213','0313','left edge'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Nesser upstream (from 0806→center):")
for a, b, desc in [
    ('0806','0906','upstream'),('0906','1005','up→center'),
    ('1005','1007','center→S'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Greater Nesser (bottom center, labeled ~1322):")
for a, b, desc in [
    ('1020','1021','upstream'),('1021','1022','mt'),
    ('1022','1122','mt'),('1022','1123','east'),
    ('1122','1223','east'),('1422','1423','Samain'),
    ('1423','1523','east marsh'),('1522','1622','east'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Argos River (right side, labeled ~1814):")
for a, b, desc in [
    ('1813','1914','upper'),('1814','1815','mid'),
    ('1815','1914','mid'),('1815','1816','mid'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")
print("  Checking southward extension on map:")
for a, b, desc in [
    ('1913','1914','S1'),('1914','2014','S2'),('1915','2015','S3'),
    ('1916','2016','S4'),('2016','2017','S5'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Dinsol Branch (labeled ~1418):")
for a, b, desc in [
    ('1017','1117','up'),('1018','1118','center'),
    ('1118','1119','south'),('1418','1517','lower'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rs_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n" + "=" * 70)
print("ROAD VERIFICATION: Model vs barbarianprince_onepiecemap-revc.jpg")
print("=" * 70)

print("\n  Dead Plains Road (NW, labeled 0307):")
for a, b, desc in [
    ('0104','0205','NW'),('0105','0106','north'),
    ('0107','0207','west'),('0207','0307','Dead Plains'),
    ('0307','0308','east'),('0307','0407','east'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Main road Cawther → Huldra Castle → South:")
for a, b, desc in [
    ('1009','1010','Cawther S'),('1009','1109','Cawther SE'),
    ('1010','1011','south'),('1011','1111','south'),
    ('1011','1112','south'),('1112','1211','Huldra area'),
    ('1113','1213','Huldra SE'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  CRITICAL: Huldra Castle (1212) road connections:")
for a, b, desc in [
    ('1112','1212','1112→1212'),('1211','1212','1211→1212'),
    ('1212','1213','1212→1213'),('1212','1112','1212→1112'),
    ('1213','1212','1213→1212'),('1213','1313','1213→1313'),
    ('1112','1113','1112→1113'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Road Huldra→Aeravir (SE):")
for a, b, desc in [
    ('1113','1213','Huldra SE'),('1213','1314','SE'),
    ('1614','1714','east'),('1711','1811','east'),
    ('1719','1818','south'),('1820','1921','Aeravir app'),
    ('1922','2022','Aeravir'),('1923','2022','to Aeravir'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Drogat Castle road (SW):")
for a, b, desc in [
    ('0222','0323','to Drogat'),('0323','0423','to Lower'),
    ('0422','0423','east from Drogat'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print("\n  Southern roads:")
for a, b, desc in [
    ('0819','0820','Brigud S'),('0820','0921','Sulwyth'),
    ('0922','1022','east Sulwyth'),('1320','1420','east'),
]:
    print(f"    {'✓' if frozenset([a,b]) in rds_set else '✗ MISSING'} {a}|{b} ({desc})")

print(f"\n=== SUMMARY ===")
print(f"River sides: {len(feats['river_sides'])}")
print(f"Road sides:  {len(feats['road_sides'])}")
print(f"Road hexes:  {len(feats['road_hexes'])}")
hc = '1212' if '1212' in feats['road_hexes'] else ('1213' if '1213' in feats['road_hexes'] else 'neither')
print(f"Huldra hex as road_hex: {hc}")
