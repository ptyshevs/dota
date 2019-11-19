import pandas as pd
import gc
import re

def permute_players(X, Y, permute_more=False):
    general_features = []
    hero_features = []
    for c in X.columns:
        if re.search(r'^[rd][0-9]_.*', c):
            hero_features.append(c)
        else:
            general_features.append(c)
    
    general_features = X[general_features]
    permutations = [(2, 1, 4, 5, 3), (3, 4, 5, 1, 2), (4, 5, 2, 3, 1), (5, 3, 1, 2, 4)]
    if permute_more:
        permutations = permutations + [(1, 2, 5, 4, 3), (2, 3, 1, 5, 4), (3, 5, 4, 1, 2), (4, 1, 2, 3, 5), (5, 4, 3, 2, 1)]
    enh_train = []

    for perm_rad, perm_dire in zip(permutations, permutations[1:] + [permutations[0]]):
        new_r_team = []
        new_d_team = []
        for i, prad, pdire in zip(range(1, 6), perm_rad, perm_dire):
            p = X[[c for c in hero_features if c.startswith('r'+str(prad))]]
            p.columns = [c[0] + str(i) + c[2:] for c in p.columns]
            new_r_team.append(p)

            p = X[[c for c in hero_features if c.startswith('d'+str(pdire))]]
            p.columns = [c[0] + str(i) + c[2:] for c in p.columns]
            new_d_team.append(p)
        combined_df = pd.concat([general_features] + new_r_team + new_d_team, axis=1)
        enh_train.append(combined_df)
        gc.collect()
    X_enh = pd.concat([X] + enh_train)
    y_enh = pd.DataFrame(pd.concat([Y.radiant_win] * (1 + len(enh_train))), columns=['radiant_win'])
    return X_enh, y_enh

def permute_teams(X, Y):
    hero_features = [c for c in X.columns if re.search(r'^[rd][0-9]_.*', c)]
    team_features = [c for c in X.columns if re.search(r'^[rd]_.*', c)]
    
    rad_cols = []
    dire_cols = []
    neutral_cols = [c for c in X.columns if c not in hero_features and c not in team_features]
    for c in (hero_features + team_features):
        if c.startswith('r'):
            rad_cols.append(c)
        elif c.startswith('d'):
            dire_cols.append(c)
    neutral_data = X[neutral_cols]
    
    radiant_team = X[rad_cols]
    radiant_team.columns = ['d' + c[1:] for c in radiant_team.columns]
    
    dire_team = X[dire_cols]
    dire_team.columns = ['r' + c[1:] for c in dire_team.columns]
    
    target = Y.radiant_win
    inv_target = ~ target
    inv_target.index = inv_target.index.map(lambda x: 'inv_' + str(x))
    target_comb = pd.concat([target, inv_target])
    
    y_inv = pd.DataFrame(target_comb, columns=['radiant_win'])
    del target, inv_target, target_comb
    gc.collect()    
    X_inv = pd.concat([neutral_data, dire_team, radiant_team], axis=1)
    X_inv.index = X_inv.index.map(lambda x: 'inv_' + str(x))
    X_comb = pd.concat([X, X_inv])
    gc.collect()
    return X_comb, y_inv