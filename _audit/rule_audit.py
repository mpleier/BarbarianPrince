"""Audit: map every rule section (r201-r228, r300-r343) to engine.py implementation."""
import re, json

# Load rules
with open('data/rules.json', encoding='utf-8') as f:
    rules = json.load(f)

# Load engine source
with open('src/engine.py', encoding='utf-8') as f:
    engine_src = f.read()
engine_lines = engine_src.split('\n')

# Load tables for r300+ cross-reference
with open('data/tables.json', encoding='utf-8') as f:
    tables = json.load(f)

# Build method lookup
methods = set()
for m in re.finditer(r'\bdef\s+(\w+)\s*\(', engine_src):
    methods.add(m.group(1))

# Build reference lookup - what rule references appear in engine.py?
rule_refs = set()
for m in re.finditer(r"[\"']?(r\d{3})[\"']?", engine_src):
    rule_refs.add(m.group(1))

# Map rule sections to titles
rule_map = {}
for k, v in rules.items():
    rule_map[k] = v.get('title', 'Untitled')

print("=" * 80)
print("RULE IMPLEMENTATION AUDIT")
print("=" * 80)

# Check each rule
for rcode in sorted(rules.keys()):
    title = rule_map[rcode]
    in_code = rcode in rule_refs
    
    # Check for the rule text content in the engine source
    # Look for comments or docstrings referencing the rule
    mentions = []
    for i, line in enumerate(engine_lines):
        if rcode.lower() in line.lower():
            mentions.append((i+1, line.strip()))
    
    # Check for method that likely implements this rule
    # Map common rule sections to method names
    impl_methods = []
    rule_to_method = {
        'r201': ['character', 'add_character'],
        'r202': ['prince', 'start'],
        'r203': ['daily_actions', 'do_travel', 'do_search'],
        'r204': ['travel', 'check_travel_event'],
        'r205': ['lost', 'get_lost'],
        'r206': ['transport', 'do_transport'],
        'r208': ['search_ruins', 'do_search'],
        'r209': ['news', 'seeking_news'],
        'r210': ['hire', 'hire_followers', 'seeking'],
        'r211': ['audience', 'local_lord'],
        'r212': ['offering', 'high_altar', 'altar_blessing'],
        'r213': ['raft', 'do_raft', 'rafting'],
        'r214': ['cache', 'do_cache'],
        'r215': ['food', 'feed_party', 'feed'],
        'r216': ['starvation', 'starve'],
        'r217': ['lodging', 'do_lodge'],
        'r218': ['escape', 'hide', 'do_escape'],
        'r219': ['follow', 'do_follow'],
        'r220': ['combat', 'battle', 'do_fight'],
        'r221': ['wound', 'endurance'],
        'r222': ['rest', 'heal', 'do_rest'],
        'r225': ['treasure', 'gain_treasure'],
        'r226': ['treasure', 'treasure_table'],
        'r227': ['trap', 'trap_lock'],
        'r228': ['love', 'true_love'],
    }
    if rcode in rule_to_method:
        for meth in rule_to_method[rcode]:
            if meth in methods:
                impl_methods.append(meth)
    
    status = "REFERENCED" if in_code else "NOT REFERENCED"
    print(f"\n{rcode}: {title}")
    print(f"  Status: {status}")
    if impl_methods:
        print(f"  Methods: {', '.join(impl_methods)}")
    if mentions:
        for line_num, line in mentions[:3]:
            print(f"  @ L{line_num}: {line[:100]}")

print("\n" + "=" * 80)
print("METHODS FOUND IN ENGINE")
print("=" * 80)
for m in sorted(methods):
    if not m.startswith('_'):
        print(f"  {m}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
referenced = [k for k in rules if k in rule_refs]
not_referenced = [k for k in rules if k not in rule_refs]
print(f"Rules referenced in engine.py: {len(referenced)}/{len(rules)}")
if not_referenced:
    print(f"Rules NOT referenced: {', '.join(sorted(not_referenced))}")
