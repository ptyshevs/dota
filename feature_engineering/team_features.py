import pandas as pd
import numpy as np
import re
import tqdm

def team_features(df, agg=None, remove_hero_features=False, calcuate_differences=True, remove_team_features=False):
    hero_features = [c for c in df.columns if re.search(r'^[rd][0-9]_.*', c)]
    team_features = [c for c in df.columns if re.search(r'^[rd]_.*', c)]

    single_player_features = [c for c in train_df.columns.tolist() if c.startswith('r1')]
    
    df_cpy = df.copy()
    if agg is None:
        agg = [np.sum]
    else:
        agg = [np.sum] + agg
    for feature in tqdm.tqdm(single_player_features):
        if feature.endswith('chat_msg') or feature.endswith('hero_tag') or feature.endswith('lane') or \
            feature.endswith('attack_type') or feature.endswith('attribute'):
            continue
        name = feature[3:]
        subdf = df_cpy[[c for c in df_cpy.columns if c.endswith(name)]]
        rad = subdf[[c for c in subdf.columns if c.startswith('r')]]
        dire = subdf[[c for c in subdf.columns if c.startswith('d')]]
        for f in agg:
            fname = str(f).split(' ')[1]
            for team in ['r', 'd']:
                team_df = subdf[[c for c in subdf.columns if c.startswith(team)]]
                
                df_cpy[f'{team}_{name}_{fname}'] = f(team_df, axis=1)

    if remove_hero_features:
        df_cpy.drop(hero_features, axis=1, inplace=True)
        if calcuate_differences:
            for feature in team_features:
                if feature.startswith('d'):
                    continue
                name = feature[2:]
                df_cpy[f'{name}_diff'] = df_cpy[feature].astype(np.float32) - df_cpy[f'd_{name}'].astype(np.float32)
            for feature in single_player_features:
                if feature.endswith('chat_msg') or feature.endswith('hero_tag') or feature.endswith('lane') or feature.endswith('attack_type') or feature.endswith('attribute'):
                    continue
                feature = feature[0] + feature[2:] + '_sum'
                name = feature[2:]
                df_cpy[f'{name}_diff'] = df_cpy[feature].astype(np.float32) - df_cpy[f'd_{name}'].astype(np.float32)
            if remove_team_features:
                df_cpy.drop(team_features, axis=1, inplace=True)
    return df_cpy