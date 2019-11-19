game_mode_map = {
    0: "Unknown",
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captains Mode",
    9: "Greeviling",
    10: "Tutorial Mode",
    11: "Mid only",
    12: "Least Played",
    13: "Limited Heroes",
    14: "Compendium Matchmaking",
    15: "Custom Mode",
    16: "Captains Draft",
    17: "Balanced Draft",
    18: "Ability Draft",
    19: "Event",
    20: "Random Death Match",
    21: "1v1 Mid",
    22: "All Draft",
    23: "Turbo Mode",
    24: "Mutation Mode"
}

lobby_type_map = {
-1: "Invalid",
0: "Public matchmaking",
1:"Practice",
2: "Tournament",
3: "Tutorial",
4: "Co-op with bots",
5: "Team match",
6: "Solo Queue",
7: "Ranked",
8: "1v1 Mid",
9: "Battle Cup"
}

slot_radiant_map = {i: f'r{i+1}' for i in range(5)}
slot_dire_map = {i:f'd{j+1}' for j, i in enumerate(range(128, 133))}
# Map slot to hero identifier
slot_hero = {**slot_radiant_map, **slot_dire_map}

team_identifier = {2: 'r', 3: 'd'}

barracks_map = {
    "1": "Dire Bot Melee",
    "2": "Dire Bot Ranged",
    "4": "Dire Mid Melee",
    "8": "Dire Mid Ranged",
    "16": "Dire Top Melee",
    "32": "Dire Top Ranged",
    "64": "Radiant Bot Melee",
    "128": "Radiant Bot Ranged",
    "256": "Radiant Mid Melee",
    "512": "Radiant Mid Ranged",
    "1024": "Radiant Top Melee",
    "2048": "Radiant Top Ranged"
}