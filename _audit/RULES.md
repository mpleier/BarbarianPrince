# Rules conformance audit

Every numbered section in `data/rules.json` mapped to its implementation, the
test that pins it, and any simplification that remains.  The goal is that a
rule regression breaks a named test rather than quietly changing the game.

## Core loop (r201-r228)

| Rule | Subject | Implementation | Test |
|---|---|---|---|
| r201 | Characters | `Character` (skill, endurance, wealth, mounts, wounds, poison) | `test_rules.CharacterTests` |
| r202 | Your Character | `Game.start` — skill 8, endurance 9, wealth 2, wit 1d6 (1→2), purse from the Treasure Table | `test_prince_starts_with_skill_8_endurance_9`, `test_starting_gold_comes_from_the_wealth_2_treasure_row` |
| r203 | Daily Actions | `daily_menu` — actions filtered by hex kind | `test_rules.DailyActionTests` |
| r204 | Travel | `begin_travel`, `speed` (1 / 2 / 3), `move`, road and river sides | `test_speed_on_foot_mounted_and_winged`, `test_no_lost_check_on_a_road` |
| r205 | Lost | `check_lost` (2d6 vs terrain, guide −1, no check on roads or a raft), `move` (airborne drift) | `test_guide_subtracts_one_from_the_lost_roll` |
| r206 | Transport | `current_loads` (food 1, gold ceil/100), `max_capacity` (10 on foot, 10 net for a mount) | `test_load_weights`, `test_capacity_of_a_man_and_a_mount` |
| r208 | Searching a Ruins | `search_ruins` — 2d6 straight on the ruins table; `e132` organised-search reroll when the die is under the party size | `test_roll_maps_straight_to_the_table`, `test_no_bonus_for_strong_followers` |
| r209 | News | `seek_news` — 2d6, +1 for 5 gold, +1 for wit 5+ | `test_bonuses_and_cost` |
| r210 | Hiring | `seek_hire` — 2d6 (+1 with the local news bonus) on the hiring table | `test_events` (hire prompts) |
| r211 | Audience | `seek_audience` — local table; temples +1 for a priest/monk, −2 for a magician/wizard/witch; at Huldra (1212) a dismissed wizard adds +1, and `dismiss` implements r201's voluntary dismissal | `test_rules.AudienceTests`, `HuldraAudienceTests` |
| r212 | Offerings | `offering` — 2d6 +1 (10 gold) + omen + influence, 14+ wins the Staff, 5 arrests, 2 defiles | `test_rules.OfferingTests` |
| r213 | Rafting | `begin_raft` / `move` — river hexsides only, 3 a day downriver / 2 upriver (flow from `features.river_flow`), no lost check, 12 stops the raft, events on the "Rafting" travel row | `test_rules.RaftTests` |
| r214 | Cache | `cache`, `recover_cache` — 1-4 intact, 5 not found, 6 looted | `test_rules.CacheTests` |
| r215 | Food | `food_need`, `feed_party`, `hunt` (skill + ½ endurance − 2d6, guide +1, rest-day helpers); farmland hunt event 1-4 nothing / 5 e017 / 6 e050 with **+2 on that die** | `test_rules.HuntingTests`, `FarmlandHuntTests` |
| r216 | Starvation | `starve` — followers roll 2d6 − wit (4+ deserts), everyone else starves (−1 skill, half loads); the Prince never deserts | `test_rules.StarvationTests` |
| r217 | Lodging | `lodging` (one room for the Prince and each priest/magician, two followers a room, one stable a mount), `sleep_rough` (desertion and mount theft) | `test_rules.LodgingTests` |
| r218 | Escape & Hiding | `escape`, `hide` (r311-r320 option verbs) | `test_events` (escape/hide options resolve) |
| r219 | Following | `do_follow` | `test_events` |
| r220 | Combat | `Combat.strike` (skill difference + 2d6 + modifiers), `pairing_of`, round order | `test_rules.CombatTests` |
| r221 | Wounds & Endurance | `Character.serious / unconscious / dead`, unconscious skill 0, Prince-down follower roll | `test_wound_thresholds` |
| r222 | Rest | `rest` — heals one wound per character unless disturbed; poison wounds never heal | `test_rules.RestTests` |
| r225 | Acquiring Treasure | `gain_treasure`, `loot` from defeated characters via the Treasure Table | `test_events` (treasure events) |
| r226 | Treasure Table | `treasure_roll` — wealth code row, one die, letter codes for special possessions | `test_starting_gold_comes_from_the_wealth_2_treasure_row` |
| r227 | Trap Locks | `do_trap_lock` — one die per trap, poison needle/gas | `test_events` (trap events) |
| r228 | True Love | event text only (e158/r228) | `test_events` |

## Combat and encounter tables (r300-r343)

These sections are *tables*, not procedures: the option matrices in
`data/events.json` name a section (`pass`, `hide`, `bribe to pass`, `ally`,
`looter`, `conversation`, ...) and `engine.py` resolves the verb through
`OPTION_VERBS` / `option_choice`.  Every referenced section resolves, and the
audit script checks that no event option points at a section that is missing.

| Rules | Subject | Resolution |
|---|---|---|
| r300-r303 | Surprise | `start_combat` surprise flags |
| r304-r310 | Attack / Attacked / Surprised | round order from the event option |
| r311-r315 | Escape | `escape` (mounted, flying and on-foot variants) |
| r316-r320 | Hide | `hide` |
| r321-r329 | Bribe / Pass | `bribe`, `pass` |
| r330 | Battle Reference | `parse_foes` + combat setup |
| r331-r339 | Bribe to join/hire, hirelings, ally, escapee, plead, convince | option handlers |
| r340 | Looter | `looter` (loot roll) |
| r341-r343 | Conversation, general inquiry, victim selection | option handlers |

## Reference tables

| Section | Table | Notes |
|---|---|---|
| r207 | `tables.travel_table` | per-terrain lost / event thresholds |
| r231-r280 | `tables.travel_event_refs` | one-die event reference per terrain result |
| r282-r299 | — | do not exist in the booklet |

## Defects found and fixed in this pass

1. **r202** — the Prince started with 0 gold; his wealth code 2 now rolls the
   Treasure Table (0-4 gold).
2. **r208** — ruin searches added an invented "+1 per follower with skill 6+".
   Removed; `e132` now rolls the organised-search die (`die < party size`)
   instead of always retrying.
3. **r211** — audiences added the same invented skill bonus. Replaced with the
   real temple modifiers (+1 priest/monk, −2 magician/wizard/witch).
4. **r213** — "raft lost on a roll of 10 or less" is not in the rules: the raft
   now travels river hexsides (three a day), never gets lost and only stops on
   a 12.
5. **r214** — cache recovery ignored the recovery die; it now follows 1-4
   intact / 5 not found / 6 looted.
6. **r215** — hunting added +1 per guide in the party instead of +1 for a guide
   hunter, and ignored the rest-day extra hunters.
7. **r216** — the Prince was skipped entirely when starving; he now suffers the
   starvation penalties (he still never deserts).
8. **r217** — a lone Prince was charged for two rooms; followers are now
   counted separately from the Prince. His mount can also be stolen when
   sleeping rough.
9. **r206** — gold loads used `floor` instead of "fraction thereof": 150 gold
   is two loads, not one.
10. **r220** — an unconscious character kept full combat skill; r221b makes it
    zero.
11. **r222** — rest healed poison wounds; a poisoned wound is now a floor.
12. **Game.start** — was not idempotent, so calling it twice (as the CLI and the
    old tests did) created two Princes.
13. **r215c / e050** — the farmland hunt's constabulary event was a dead end:
    `parse_options` only looked for "options are", so e050's matrix (which the
    booklet introduces with "select your option") was never parsed and the
    event arrived as plain text.  The parser now tries every "die roll" header
    and keeps the one whose columns are option verbs, and it splits glued cells
    such as `hider318`.  e050 now also enforces its own rules: it only fires
    within three hexes of a town/castle/temple, Ogon and Weshor send e002
    instead, the option die gets +2 for a place visited before and +1 for one
    never visited, and the hunt itself adds the r215c +2.
14. **r211 Huldra bonus** — the data carried the Baron's note ("+1 if you
    dismiss any wizard, magician or witch") but nothing implemented it, and
    recruits arrived as "Hired 1" with no calling, so even the temple ±modifiers
    could never fire.  `Character` now records a `kind` ('magician' or
    'priest') from the recruiting event, `party_kinds` reads it, r201's
    voluntary `dismiss` exists, and an audience at 1212 offers to give the
    wizard to the Baron for +1.
15. **r213 flow** — the first version took "top to bottom" literally, which sent
    six of the Tragoth's 43 sides east (and six of the Largos' twelve south),
    against the booklet's "east to west" and "toward the north-east".  The flow
    map now recognises the northern staircase and the eastern block and orients
    them as the booklet describes.

## Known simplifications

* **r213 river flow** — the booklet names the flow of each river, but the traces
  carry no names, so `features.river_flow` derives the direction from the
  layout: the northern staircase (both hexes in rows 1-3) drains **west** (the
  Tragoth, 43/43 sides), the separate eastern block drains **north-east** (the
  Largos, 12/12 sides), and everything else drains **south** (the Nesser and
  the southern network).  This replaced a plain "top to bottom" rule that sent
  six Tragoth sides east and six Largos sides south.
  *Remaining gap:* the Dienstal Branch, which the booklet says flows *into* the
  Nesser, cannot be told apart from the Nesser traces, so it inherits the
  southward flow.
