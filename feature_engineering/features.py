from mappings import slot_hero, team_identifier, barracks_map
from mappings import game_mode_map, lobby_type_map
import pandas as pd

# Used for purchase_features
items_df = pd.read_csv('../additional_data/items.csv', index_col=0)
heroes_df = pd.read_csv('../additional_data/heroes.csv', index_col=0)
heroes_df.Role = heroes_df.Role.map(eval)
heroes_df.Rolelevels = heroes_df.Rolelevels.map(lambda x: list(map(int, eval(x))))

def chat_features(game):
    """
    game -> JSON object
    
    returns: dict of chat features:
    1) Total amount of messages
    2) # of messages per team
    3) # of messages per player
    """
    chat = game['chat']
    
    suffix = "_chat_msg"
    
    # Initialize with zeros

    if 'init_dict' not in dir(chat_features):
        team_features = {'r' + suffix: 0, 'd' + suffix: 0}
        hero_features = {(f'r{i+1}' if i < 5 else f'd{i-4}')+suffix:0 for i in range(10)}

        chat_features.init_dict = {'chat_len': 0, **team_features, **hero_features}

    features = chat_features.init_dict.copy()
    # Use slot_to_hero mapping to update coutns
    for msg in chat:
        player_slot = msg['player_slot']
        if player_slot is None:
            continue
        hero_id = slot_hero[msg['player_slot']]
        if hero_id.startswith('r'):
            features['r' + suffix] += 1
        else:
            features['d' + suffix] += 1

        features[hero_id + suffix] += 1
        features['chat_len'] += 1
    
    return features

def objectives_features(game):
    if 'init_features' not in dir(objectives_features):
        objectives_features.init_features = {'r_tower_killed': 0, 'd_tower_killed': 0,
                'r_barracks_killed': 0, 'd_barracks_killed': 0,
                'r_roshan_killed': 0, 'd_roshan_killed': 0,
                'r_first_blood': False, 'd_first_blood': False,
                'r_had_aegis': 0, 'd_had_aegis': 0,
                'r_tower_denied': 0, 'd_tower_denied': 0,
                'obj_len': 0, 'r_obj': 0, 'd_obj': 0}
    c = objectives_features.init_features.copy()
    for obj in game['objectives']:
        event = obj['type']
        if event == 'CHAT_MESSAGE_TOWER_KILL':
            team = team_identifier[obj['team']]
            key =  team + '_tower_killed'
            c[key] += 1
            c[team + '_obj'] += 1
        elif event == "CHAT_MESSAGE_TOWER_DENY":
            team = slot_hero[obj['player_slot']][0]
            key = team + '_tower_denied'
            c[key] += 1
            c[team + '_obj'] += 1
        elif event == "CHAT_MESSAGE_ROSHAN_KILL":
            team = team_identifier[obj['team']]
            key = team + '_roshan_killed'
            c[key] += 1
            c[team + '_obj'] += 1
        elif event == "CHAT_MESSAGE_BARRACKS_KILL":
            barrack = barracks_map[obj['key']]
            team = ('d' if barrack.startswith("Dire") else 'r')
            c[team + '_barracks_killed'] += 1
            c[team + '_obj'] += 1
        elif event == "CHAT_MESSAGE_FIRSTBLOOD":
            team = slot_hero[obj['player_slot']][0]
            c[team + '_obj'] += 1
            c[team + '_first_blood'] = True
        elif event == "CHAT_MESSAGE_AEGIS":
            team = slot_hero[obj['player_slot']][0]
            key = team + '_had_aegis'
            c[key] += 1
            c[team + '_obj'] += 1
        else:  # ignore other events, like aegis steal and deny
            continue
        c['obj_len'] += 1
    return c

def general_features(game):
    if 'init_dict' not in dir(general_features):
        general_features.init_dict = {'game_time': 0, 'game_mode': None,
                                      'lobby_type': None, 'game_phase': None}
    c = general_features.init_dict.copy()
    c['game_time'] = game['game_time']
    c['lobby_type'] = lobby_type_map[game['lobby_type']]
    gm = game_mode_map[game['game_mode']]
    if gm == "Captains Draft":
        gm = "Captains Mode"
    elif gm == "Least Played":
        gm = "Random Draft"
    elif gm == 'All Random':
        gm = "Random Draft"
    c['game_mode'] = gm
    
    game_mins = game['game_time'] / 60.0
    game_phase = 'early_game'
    if game_mins >= 26:
        game_phase = 'late_game'
    elif game_mins >= 13:
        game_phase = 'mid_game'
    c['game_phase'] = game_phase
    
    return c

def teamfights_features(game):
    if 'init_dict' not in dir(teamfights_features):
        teamfights_features.init_dict = {'n_fights': 0, 'mean_time': 0, 'mean_deaths': 0}
    c = teamfights_features.init_dict.copy()
    c['n_fights'] = len(game['teamfights'])
    for fight in game['teamfights']:
        c['mean_time'] += fight['end'] - fight['start']
        c['mean_deaths'] += fight['deaths']
    if c['n_fights']:
        c['mean_time'] /= c['n_fights']
        c['mean_deaths'] /= c['n_fights']
    return c

def log_features(player):
    if 'init_dict' not in dir(log_features):
        log_features.init_dict = {'len_obs_left': 0, 'len_sen_left': 0, 'len_purchase': 0,
                                  'n_buybacks': 0}
    c = log_features.init_dict.copy()
    c['len_obs_left'] = len(player['obs_left_log'])
    c['len_sen_left'] =  len(player['sen_left_log'])
    c['len_purchase'] = len(player['purchase_log'])
    c['n_buybacks'] = len(player['buyback_log'])
    return c

def dt_features(game, player, beta=.6, corrected=True):
    if 'init_dict' not in dir(dt_features):
        dt_features.init_dict = {'xp_sec': 0, 'gold_sec': 0}
    c = dt_features.init_dict.copy()
    
    
    times = player['times'].copy()
    gold_t = player['gold_t'].copy()
    xp_t = player['xp_t'].copy()
    
    if times and game['game_time'] > times[-1]:
        times.append(game['game_time'])
        gold_t.append(player['gold'])
        xp_t.append(player['xp'])
    n = len(times) - 1
    dt = [times[i + 1] - times[i] for i in range(n)]
    dgold = [gold_t[i + 1] - gold_t[i] for i in range(n)]
    dxp = [xp_t[i + 1] - xp_t[i] for i in range(n)]

    
    gold_sec = [gold / time for gold,time in zip(dgold, dt)]
    avg_gold = 0
    for gs in gold_sec:
        avg_gold = beta * avg_gold + (1 - beta) * gs
    
    xp_sec = [xp / time for xp, time in zip(dxp, dt)]
    avg_xp = 0
    for xs in xp_sec:
        avg_xp = beta * avg_xp + (1 - beta) * xs
    
    if corrected and n > 0:
        avg_gold = avg_gold / (1 - beta ** (n + 1))
        avg_xp = avg_xp / (1 - beta ** (n + 1))
    
    c['xp_sec'] = avg_xp
    c['gold_sec'] = avg_gold
    return c

def normalize_coords(x, y, xmin=66.0, xmax=200.0, ymin=66.0, ymax=200.0):
    return (x - xmin) / (xmax - xmin) , (y - ymin) / (ymax - ymin)

def pos_features(player):
    if 'init' not in dir(pos_features):
        pos_features.init = {'x': None, 'y': None, 'lane': None,
                             'my_base_d': 0, 'enemy_base_d': 0}
        
        pos_features.radiant_base = (0.1, 0.1)
        pos_features.dire_base = (.9, .9)
        pos_features.dist = lambda x, y, b: ((x - b[0]) ** 2 + (y - b[1]) ** 2) ** .5
        
        pos_features.is_top_lane = lambda x, y: x < .175 or y < .175
        pos_features.is_mid_lane = lambda x, y: abs(x - y) < .15
        pos_features.is_bot_lane = lambda x, y: x > .85 or y > .85
        
    c = pos_features.init.copy()
    x, y = player['x'], player['y']
    x, y = normalize_coords(x, y)
    if pos_features.is_top_lane(x, y):
        c['lane'] = 'top'
    elif pos_features.is_mid_lane(x, y):
        c['lane'] = 'mid'
    elif pos_features.is_bot_lane(x, y):
        c['lane'] = 'bot'
    else:
        c['lane'] = 'jungle'
    
    hero_identifier = slot_hero[player['player_slot']]
    team = hero_identifier[0]
    if team == 'r':
        c['my_base_d'] = pos_features.dist(x, y, pos_features.radiant_base)
        c['enemy_base_d'] = pos_features.dist(x, y, pos_features.dire_base)
    else:
        c['my_base_d'] = pos_features.dist(x, y, pos_features.dire_base)
        c['enemy_base_d'] = pos_features.dist(x, y, pos_features.radiant_base)
    
    c['x'] = x
    c['y'] = y
    return c

def action_features(player):
    if 'init' not in dir(action_features):
        action_features.actions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                                   17, 18, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31,
                                   32, 33, 36]
        action_features.init = {f'action_{a}': 0 for a in action_features.actions}
    c = action_features.init.copy()
    for a, v in player['actions'].items():
        c[f'action_{a}'] = v
    return c

def life_state_features(game, player):
    if 'init' not in dir(life_state_features):
        life_state_features.init = {'sec_dead': 0, 'sec_magic': 0,
                                    'frac_dead': 0, 'frac_magic': 0}
    c = life_state_features.init.copy()
    
    time = game['game_time']
    
    keys = player['life_state'].keys()
    if '1' in keys:
        c['sec_dead'] = player['life_state']['1'] / 2.0
        if time:
            c['frac_dead'] = c['sec_dead'] / time
    if '2' in keys:
        c['sec_magic'] = player['life_state']['2'] / 2.0
        if time:
            c['frac_magic'] = c['sec_magic'] / time
    return c

def gold_features(player):
    if 'init' not in dir(gold_features):
        gold_features.gold_reasons = [0, 1, 2, 5, 6, 11, 12, 13, 14, 15]
        gold_features.init = {'net_gold': 0}
        gold_features.init.update({f'gold_reason_{i}': 0 for i in gold_features.gold_reasons})
        gold_features.init.update({f'gold_reason_{i}_frac': 0 for i in gold_features.gold_reasons})

    c = gold_features.init.copy()
    for reason, value in player['gold_reasons'].items():
        if reason == '0':
            value -= 600  # base value
        c['net_gold'] += value
        c['gold_reason_' + reason] = value
    for reason, value in player['gold_reasons'].items():
        if c['net_gold']:
            c['gold_reason_' + reason + '_frac'] = c['gold_reason_' + reason] / c['net_gold']
    return c

def xp_features(player):
    if 'init' not in dir(xp_features):
        xp_features.xp_reasons = [0, 1, 2, 3]
        xp_features.init = {'net_xp': 0}
        xp_features.init.update({f'xp_reason_{i}': 0 for i in xp_features.xp_reasons})
        xp_features.init.update({f'xp_reason_{i}_frac': 0 for i in xp_features.xp_reasons})

    c = xp_features.init.copy()
    c['net_xp'] = player['xp']
    for reason, value in player['xp_reasons'].items():
        c['xp_reason_' + reason] = value
        if player['xp']:
            c['xp_reason_' + reason + '_frac'] = value / player['xp']
    return c

def purchase_features(player):
    if 'init' not in dir(purchase_features):
        purchase_features.categories = ['Consumables', 'Attributes', 'Armaments', 'Arcane', 'Common', 'Support',
                      'Caster', 'Weapons', 'Armor', 'Artifacts', 'Secret shop']
        purchase_features.init = {'pch_total_cost': 0}
        purchase_features.init.update({f'pch_{cat}': 0 for cat in purchase_features.categories})

    c = purchase_features.init.copy()
    for p, amount in player['purchase'].items():
        if p not in items_df.index:
            continue
        item = items_df.loc[p]
        c['pch_total_cost'] += item.cost
        c[f'pch_{item.category}'] += 1
    return c

def hero_features(player):
    if 'init' not in dir(hero_features):
        hero_features.roles = ['Initiator', 'Disabler', 'Durable', 'Nuker',
                               'Carry', 'Pusher', 'Escape', 'Jungler', 'Support']
        hero_features.rolelevels = [1, 2, 3]
        hero_features.init = {f'role_{a}_lvl': 0 for a in hero_features.roles}
        hero_features.init.update({'complexity': 0, 'attack_type': None, 'attribute': None,
                                 'hero_tag': 0})
        
    c = hero_features.init.copy()
    
    hero = heroes_df.loc[player['hero_id']]
    c['hero_tag'] = hero.tag
    c['attribute'] = hero.AttributePrimary
    c['attack_type'] = hero.AttackCapabilities
    c['complexity'] = hero.Complexity
    for role, level in zip(hero.Role, hero.Rolelevels):
        c[f'role_{role}_lvl'] = level
    return c

item_index = ['tango', 'wraith_band', 'enchanted_mango', 'clarity', 'tpscroll', 'magic_stick', 'wind_lace', 'magic_wand', 'stout_shield', 'quelling_blade', 'branches', 'faerie_fire', 'flask', 'orb_of_venom', 'boots', 'null_talisman', 'phase_boots', 'blade_of_alacrity', 'ancient_janggo', 'dust', 'soul_ring', 'tranquil_boots', 'chainmail', 'pers', 'blight_stone', 'ring_of_aquila', 'power_treads', 'smoke_of_deceit', 'ward_sentry', 'ring_of_health', 'ring_of_basilius', 'ring_of_regen', 'gauntlets', 'circlet', 'ward_observer', 'bottle', 'helm_of_iron_will', 'void_stone', 'bracer', 'ring_of_protection', 'gloves', 'arcane_boots', 'blades_of_attack', 'lifesteal', 'slippers', 'robe', 'urn_of_shadows', 'bfury', 'mekansm', 'broadsword', 'ogre_axe', 'blink', 'mithril_hammer', 'infused_raindrop', 'belt_of_strength', 'tome_of_knowledge', 'vanguard', 'boots_of_elves', 'staff_of_wizardry', 'invis_sword', 'energy_booster', 'hand_of_midas', 'shadow_amulet', 'blade_mail', 'medallion_of_courage', 'cloak', 'helm_of_the_dominator', 'kaya', 'dragon_lance', 'black_king_bar', 'desolator', 'heavens_halberd', 'armlet', 'travel_boots', 'ultimate_scepter', 'sange_and_yasha', 'radiance', 'reaver', 'lesser_crit', 'monkey_king_bar', 'quarterstaff', 'maelstrom', 'mask_of_madness', 'echo_sabre', 'javelin', 'glimmer_cape', 'solar_crest', 'vladmir', 'diffusal_blade', 'cyclone', 'mantle', 'sphere', 'oblivion_staff', 'ultimate_orb', 'shivas_guard', 'spirit_vessel', 'silver_edge', 'butterfly', 'yasha', 'abyssal_blade', 'platemail', 'manta', 'greater_crit', 'force_staff', 'aether_lens', 'point_booster', 'buckler', 'headdress', 'ghost', 'nullifier', 'meteor_hammer', 'veil_of_discord', 'hurricane_pike', 'crimson_guard', 'heart', 'basher', 'gem', 'mystic_staff', 'hyperstone', 'ethereal_blade', 'claymore', 'sobi_mask', 'guardian_greaves', 'sheepstick', 'orchid', 'aeon_disk', 'bloodstone', 'lotus_orb', 'hood_of_defiance', 'vitality_booster', 'demon_edge', 'pipe', 'refresher', 'skadi', 'mjollnir', 'rod_of_atos', 'aegis', 'relic', 'assault', 'talisman_of_evasion', 'soul_booster', 'eagle', 'sange', 'satanic', 'bloodthorn', 'necronomicon', 'octarine_core', 'rapier', 'courier', 'moon_shard', 'dagon']

def strange_items_mapper(item):
    if item == 'ward_dispenser':
        return 'ward_observer'
    elif 'tango' in item:
        return 'tango'
    elif 'dagon' in item:
        return 'dagon'
    elif 'necronomicon' in item:
        return 'necronomicon'
    elif 'travel_boots' in item:
        return 'travel_boots'
    else:
        return item

def team_items_features(game):
    if 'init' not in dir(team_items_features):
        radiant = {f'r_{item}': 0 for item in item_index}
        dire = {f'd_{item}': 0 for item in item_index}
        team_items_features.init = {**radiant, **dire}
    
    c = team_items_features.init.copy()
    for i, p in enumerate(game['players']):
        team = 'r' if i < 5 else 'd'
        for source in ['hero_inventory', 'hero_stash']:
            for thing in p[source]:
                name = thing['id'][5:]
                if name in item_index:
                    c[f'{team}_{name}'] += 1
                else:
                    name2 = strange_items_mapper(name)
                    if name2 != name:
                        c[f'{team}_{name2}'] += 1
    return c

def player_kill_streaks(player):
    
    ks_cum = {'3-4': 0, '5-6': 0, '>6': 0}

    ks = {int(k):v for k, v in player['kill_streaks'].items()}
    sorted_ks = sorted(ks.keys(), reverse=True)

    for i, k in enumerate(sorted_ks):
        if ks[k] == 0:
            continue
        if k < 5:
            ks_cum['3-4'] += ks[k]
        elif k < 7:
            ks_cum['5-6'] += ks[k]
        else:
            ks_cum['>6'] += ks[k]
        v = ks[k]
        for ki in sorted_ks[i:]:
            ks[ki] -= v
    return ks_cum

def player_multi_kills(player):
    
    mk_cum = {'2': 0, '>2': 0}

    mk = {int(k):v for k, v in player['multi_kills'].items()}
    sorted_mk = sorted(mk.keys(), reverse=True)

    for i, k in enumerate(sorted_mk):
        if mk[k] == 0:
            continue
        if k == 2:
            mk_cum['2'] += mk[k]
        else:
            mk_cum['>2'] += mk[k]
        v = mk[k]
        for ki in sorted_mk[i:]:
            mk[ki] -= v
    return mk_cum

def team_kill_streaks_features(game):
    if 'init' not in dir(team_kill_streaks_features):
        multi_kills = ['2', '>2']
        kill_streaks = ['3-4', '5-6', '>6']
        team_kill_streaks_features.init = {'r_kill_streaks': 0, 'r_multi_kills': 0,
                                           'd_kill_streaks': 0, 'd_multi_kills': 0}
        team_kill_streaks_features.init.update({f'r{i}_multi_kills_{mk}': 0 for mk in multi_kills for i in range(1, 6)})
        team_kill_streaks_features.init.update({f'd{i}_multi_kills_{mk}': 0 for mk in multi_kills for i in range(1, 6)})
    
        team_kill_streaks_features.init.update({f'r{i}_kill_streaks_{mk}': 0 for mk in kill_streaks for i in range(1, 6)})
        team_kill_streaks_features.init.update({f'd{i}_kill_streaks_{mk}': 0 for mk in kill_streaks for i in range(1, 6)})

    
    c = team_kill_streaks_features.init.copy()
    
    for i, player in enumerate(game['players']):
        team = 'r' if i < 5 else 'd'
        idx = i % 5 + 1
        
        mk_cum = player_multi_kills(player)
        for k, v in mk_cum.items():
            c[f'{team}{idx}_multi_kills_{k}'] = v
        c[f'{team}_multi_kills'] += sum(mk_cum.values())

        ks_cum = player_kill_streaks(player)
        for k, v in ks_cum.items():
            c[f'{team}{idx}_kill_streaks_{k}'] = v
        c[f'{team}_kill_streaks'] += sum(ks_cum.values())
    return c

def main_player_features(player):
    if 'init' not in dir(main_player_features):
        main_player_features.init = {'obs_placed': 0, 'sen_placed': 0, 'creeps_stacked': 0,
                                    'camps_stacked': 0, 'rune_pickups': 0,
                                     'teamfight_participation': 0, 'towers_killed': 0,
                                     'pings': 0, 'gold': 0, 'lh': 0, 'health': 0,
                                    'max_health': 0, 'level': 0, 'kills': 0, 'deaths': 0,
                                    'assists': 0, 'denies': 0, 'nearby_creep_death_count': 0}
    
    c = main_player_features.init.copy()
    for k in c.keys():
        if k == 'pings':
            if player[k]:
                c[k] = player[k]['0']
        else:
            c[k] = player[k]
    c['health_frac'] = c['health'] / c['max_health']
    return c


heroes_tags = ['nevermore', 'brewmaster', 'pudge', 'huskar', 'lycan', 'phantom_lancer', 'windrunner', 'night_stalker', 'ogre_magi',
          'tinker', 'razor', 'centaur', 'shadow_shaman', 'weaver', 'naga_siren', 'enchantress', 'antimage', 'clinkz', 'visage',
          'skywrath_mage', 'rattletrap', 'phantom_assassin', 'dragon_knight', 'furion', 'sven', 'spectre', 'viper', 'venomancer',
          'storm_spirit', 'bristleback', 'lion', 'faceless_void', 'shredder', 'juggernaut', 'doom_bringer', 'rubick', 'skeleton_king',
          'legion_commander', 'batrider', 'kunkka', 'zuus', 'sniper', 'gyrocopter', 'omniknight', 'morphling', 'chaos_knight', 'dark_willow',
          'luna', 'ancient_apparition', 'abaddon', 'spirit_breaker', 'abyssal_underlord', 'keeper_of_the_light', 'wisp', 'monkey_king', 'dazzle',
          'invoker', 'slark', 'silencer', 'obsidian_destroyer', 'bane', 'bounty_hunter', 'witch_doctor', 'lone_druid', 'bloodseeker', 'drow_ranger',
          'slardar', 'troll_warlord', 'broodmother', 'axe', 'elder_titan', 'medusa', 'disruptor', 'phoenix', 'tidehunter', 'lina', 'techies', 'mirana',
          'life_stealer', 'riki', 'oracle', 'pangolier', 'ursa', 'tiny', 'queenofpain', 'alchemist', 'winter_wyvern', 'treant', 'puck', 'shadow_demon',
          'lich', 'necrolyte', 'crystal_maiden', 'tusk', 'jakiro', 'ember_spirit', 'sand_king', 'nyx_assassin', 'terrorblade', 'earthshaker', 'vengefulspirit',
          'magnataur', 'warlock', 'pugna', 'earth_spirit', 'arc_warden', 'meepo', 'death_prophet', 'templar_assassin', 'enigma',
          'undying', 'leshrac', 'dark_seer', 'beastmaster', 'chen']
    
def team_lineups(game):
    if 'init' not in dir(team_lineups):
        dire = {f'r_{hero}': 0 for hero in heroes_tags}
        radiant = {f'd_{hero}': 0 for hero in heroes_tags}
        team_lineups.init = {**dire, **radiant}
    
    c = team_lineups.init.copy()
    
    for i, p in enumerate(game['players']):
        team = 'r' if i <  5 else 'd'
        name = '_'.join(p['hero_name'].split('_')[3:])
        c[f'{team}_{name}'] = 1
    return c


def player_features(game, player):
    prefix = slot_hero[player['player_slot']]
    features = {**log_features(player), **dt_features(game, player),
            **pos_features(player), **action_features(player),
            **life_state_features(game, player), **gold_features(player),
           **xp_features(player), **purchase_features(player),
           **hero_features(player),  **main_player_features(player)}
    
    return {f'{prefix}_{key}': value for key, value in features.items()}

def game_features(game):
    features = {**chat_features(game), **objectives_features(game),
                **general_features(game), **teamfights_features(game),
                **team_items_features(game), **team_kill_streaks_features(game),
               **team_lineups(game)}
    for p in game['players']:
        features.update(player_features(game, p))
    return features


categorical_columns = ['r_first_blood', 'd_first_blood', 'game_mode', 'lobby_type', 'game_phase', 'r_nevermore', 'r_brewmaster', 'r_pudge', 'r_huskar', 'r_lycan', 'r_phantom_lancer', 'r_windrunner', 'r_night_stalker', 'r_ogre_magi', 'r_tinker', 'r_razor', 'r_centaur', 'r_shadow_shaman', 'r_weaver', 'r_naga_siren', 'r_enchantress', 'r_antimage', 'r_clinkz', 'r_visage', 'r_skywrath_mage', 'r_rattletrap', 'r_phantom_assassin', 'r_dragon_knight', 'r_furion', 'r_sven', 'r_spectre', 'r_viper', 'r_venomancer', 'r_storm_spirit', 'r_bristleback', 'r_lion', 'r_faceless_void', 'r_shredder', 'r_juggernaut', 'r_doom_bringer', 'r_rubick', 'r_skeleton_king', 'r_legion_commander', 'r_batrider', 'r_kunkka', 'r_zuus', 'r_sniper', 'r_gyrocopter', 'r_omniknight', 'r_morphling', 'r_chaos_knight', 'r_dark_willow', 'r_luna', 'r_ancient_apparition', 'r_abaddon', 'r_spirit_breaker', 'r_abyssal_underlord', 'r_keeper_of_the_light', 'r_wisp', 'r_monkey_king', 'r_dazzle', 'r_invoker', 'r_slark', 'r_silencer', 'r_obsidian_destroyer', 'r_bane', 'r_bounty_hunter', 'r_witch_doctor', 'r_lone_druid', 'r_bloodseeker', 'r_drow_ranger', 'r_slardar', 'r_troll_warlord', 'r_broodmother', 'r_axe', 'r_elder_titan', 'r_medusa', 'r_disruptor', 'r_phoenix', 'r_tidehunter', 'r_lina', 'r_techies', 'r_mirana', 'r_life_stealer', 'r_riki', 'r_oracle', 'r_pangolier', 'r_ursa', 'r_tiny', 'r_queenofpain', 'r_alchemist', 'r_winter_wyvern', 'r_treant', 'r_puck', 'r_shadow_demon', 'r_lich', 'r_necrolyte', 'r_crystal_maiden', 'r_tusk', 'r_jakiro', 'r_ember_spirit', 'r_sand_king', 'r_nyx_assassin', 'r_terrorblade', 'r_earthshaker', 'r_vengefulspirit', 'r_magnataur', 'r_warlock', 'r_pugna', 'r_earth_spirit', 'r_arc_warden', 'r_meepo', 'r_death_prophet', 'r_templar_assassin', 'r_enigma', 'r_undying', 'r_leshrac', 'r_dark_seer', 'r_beastmaster', 'r_chen', 'd_nevermore', 'd_brewmaster', 'd_pudge', 'd_huskar', 'd_lycan', 'd_phantom_lancer', 'd_windrunner', 'd_night_stalker', 'd_ogre_magi', 'd_tinker', 'd_razor', 'd_centaur', 'd_shadow_shaman', 'd_weaver', 'd_naga_siren', 'd_enchantress', 'd_antimage', 'd_clinkz', 'd_visage', 'd_skywrath_mage', 'd_rattletrap', 'd_phantom_assassin', 'd_dragon_knight', 'd_furion', 'd_sven', 'd_spectre', 'd_viper', 'd_venomancer', 'd_storm_spirit', 'd_bristleback', 'd_lion', 'd_faceless_void', 'd_shredder', 'd_juggernaut', 'd_doom_bringer', 'd_rubick', 'd_skeleton_king', 'd_legion_commander', 'd_batrider', 'd_kunkka', 'd_zuus', 'd_sniper', 'd_gyrocopter', 'd_omniknight', 'd_morphling', 'd_chaos_knight', 'd_dark_willow', 'd_luna', 'd_ancient_apparition', 'd_abaddon', 'd_spirit_breaker', 'd_abyssal_underlord', 'd_keeper_of_the_light', 'd_wisp', 'd_monkey_king', 'd_dazzle', 'd_invoker', 'd_slark', 'd_silencer', 'd_obsidian_destroyer', 'd_bane', 'd_bounty_hunter', 'd_witch_doctor', 'd_lone_druid', 'd_bloodseeker', 'd_drow_ranger', 'd_slardar', 'd_troll_warlord', 'd_broodmother', 'd_axe', 'd_elder_titan', 'd_medusa', 'd_disruptor', 'd_phoenix', 'd_tidehunter', 'd_lina', 'd_techies', 'd_mirana', 'd_life_stealer', 'd_riki', 'd_oracle', 'd_pangolier', 'd_ursa', 'd_tiny', 'd_queenofpain', 'd_alchemist', 'd_winter_wyvern', 'd_treant', 'd_puck', 'd_shadow_demon', 'd_lich', 'd_necrolyte', 'd_crystal_maiden', 'd_tusk', 'd_jakiro', 'd_ember_spirit', 'd_sand_king', 'd_nyx_assassin', 'd_terrorblade', 'd_earthshaker', 'd_vengefulspirit', 'd_magnataur', 'd_warlock', 'd_pugna', 'd_earth_spirit', 'd_arc_warden', 'd_meepo', 'd_death_prophet', 'd_templar_assassin', 'd_enigma', 'd_undying', 'd_leshrac', 'd_dark_seer', 'd_beastmaster', 'd_chen', 'r1_lane', 'r1_role_Initiator_lvl', 'r1_role_Disabler_lvl', 'r1_role_Durable_lvl', 'r1_role_Nuker_lvl', 'r1_role_Carry_lvl', 'r1_role_Pusher_lvl', 'r1_role_Escape_lvl', 'r1_role_Jungler_lvl', 'r1_role_Support_lvl', 'r1_complexity', 'r1_attack_type', 'r1_attribute', 'r1_hero_tag', 'r2_lane', 'r2_role_Initiator_lvl', 'r2_role_Disabler_lvl', 'r2_role_Durable_lvl', 'r2_role_Nuker_lvl', 'r2_role_Carry_lvl', 'r2_role_Pusher_lvl', 'r2_role_Escape_lvl', 'r2_role_Jungler_lvl', 'r2_role_Support_lvl', 'r2_complexity', 'r2_attack_type', 'r2_attribute', 'r2_hero_tag', 'r3_lane', 'r3_role_Initiator_lvl', 'r3_role_Disabler_lvl', 'r3_role_Durable_lvl', 'r3_role_Nuker_lvl', 'r3_role_Carry_lvl', 'r3_role_Pusher_lvl', 'r3_role_Escape_lvl', 'r3_role_Jungler_lvl', 'r3_role_Support_lvl', 'r3_complexity', 'r3_attack_type', 'r3_attribute', 'r3_hero_tag', 'r4_lane', 'r4_role_Initiator_lvl', 'r4_role_Disabler_lvl', 'r4_role_Durable_lvl', 'r4_role_Nuker_lvl', 'r4_role_Carry_lvl', 'r4_role_Pusher_lvl', 'r4_role_Escape_lvl', 'r4_role_Jungler_lvl', 'r4_role_Support_lvl', 'r4_complexity', 'r4_attack_type', 'r4_attribute', 'r4_hero_tag', 'r5_lane', 'r5_role_Initiator_lvl', 'r5_role_Disabler_lvl', 'r5_role_Durable_lvl', 'r5_role_Nuker_lvl', 'r5_role_Carry_lvl', 'r5_role_Pusher_lvl', 'r5_role_Escape_lvl', 'r5_role_Jungler_lvl', 'r5_role_Support_lvl', 'r5_complexity', 'r5_attack_type', 'r5_attribute', 'r5_hero_tag', 'd1_lane', 'd1_role_Initiator_lvl', 'd1_role_Disabler_lvl', 'd1_role_Durable_lvl', 'd1_role_Nuker_lvl', 'd1_role_Carry_lvl', 'd1_role_Pusher_lvl', 'd1_role_Escape_lvl', 'd1_role_Jungler_lvl', 'd1_role_Support_lvl', 'd1_complexity', 'd1_attack_type', 'd1_attribute', 'd1_hero_tag', 'd2_lane', 'd2_role_Initiator_lvl', 'd2_role_Disabler_lvl', 'd2_role_Durable_lvl', 'd2_role_Nuker_lvl', 'd2_role_Carry_lvl', 'd2_role_Pusher_lvl', 'd2_role_Escape_lvl', 'd2_role_Jungler_lvl', 'd2_role_Support_lvl', 'd2_complexity', 'd2_attack_type', 'd2_attribute', 'd2_hero_tag', 'd3_lane', 'd3_role_Initiator_lvl', 'd3_role_Disabler_lvl', 'd3_role_Durable_lvl', 'd3_role_Nuker_lvl', 'd3_role_Carry_lvl', 'd3_role_Pusher_lvl', 'd3_role_Escape_lvl', 'd3_role_Jungler_lvl', 'd3_role_Support_lvl', 'd3_complexity', 'd3_attack_type', 'd3_attribute', 'd3_hero_tag', 'd4_lane', 'd4_role_Initiator_lvl', 'd4_role_Disabler_lvl', 'd4_role_Durable_lvl', 'd4_role_Nuker_lvl', 'd4_role_Carry_lvl', 'd4_role_Pusher_lvl', 'd4_role_Escape_lvl', 'd4_role_Jungler_lvl', 'd4_role_Support_lvl', 'd4_complexity', 'd4_attack_type', 'd4_attribute', 'd4_hero_tag', 'd5_lane', 'd5_role_Initiator_lvl', 'd5_role_Disabler_lvl', 'd5_role_Durable_lvl', 'd5_role_Nuker_lvl', 'd5_role_Carry_lvl', 'd5_role_Pusher_lvl', 'd5_role_Escape_lvl', 'd5_role_Jungler_lvl', 'd5_role_Support_lvl', 'd5_complexity', 'd5_attack_type', 'd5_attribute', 'd5_hero_tag']