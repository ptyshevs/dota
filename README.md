# Dota: Radiant victory prediction

[Link](https://www.kaggle.com/c/mlcourse-dota2-win-prediction) to competition.
[Link](https://www.taskade.com/e/izLoMiUnQoAHWuSE) to TO-DO.

## Problem descriptoin

Dota is a competitive game, where two teams of five players fight each-other. Before the game starts, each player chooses a hero and spawns on
his base. Before the creeps appear, there is time to buy items from the shop using initial gold. Then, each player goes to his position on the
map.

## Data description

Dataset is in JSONL format - each line is a JSON object that describes one game.
Available keys: `['game_time', 'match_id_hash', 'teamfights', 'objectives', 'chat', 'game_mode', 'lobby_type', 'players']`. Furthermore, `train_matches.jsonl` contains additional key `targets`, which contains the following fields: `['game_time', 'duration', 'time_remaining', 'radiant_win', 'next_roshan_team']`. `radiant_win` is our target.

Score is calculated using ROC AUC.

### Game object

Game object consists of 8 (+1 for training matches) keys:
* `game_time` - time at the moment of data collection
* `match_id_hash` - game unique identifier
* `teamfights` - list of fighting encounters between teams
* `objectives` - ?
* `chat` - list of encrypted chat messages in format (`player_slot`, `time`, `message`)
* `game_mode` - type of game played (Majority of 22 - "All Draft")
* `lobby_type` - type of game lobby created. (0 - Public matchmaking, 7 - Ranked)

## Pre-processed features

There are 245 features in the dataset. First 5 of them are related to the game configuration. The remaining 240 describe the state of all 10 heros,
each having 24 features, such as (x, y) location, hp, gold, etc.

## Features engineered

### General features

* `game_time`
* game phase based on time (early\mid\late)
* `game_mode`
* `lobby_type`

### Chat

Chat is collected only before the current `game_time`.
* Chat length
* Number of messages per team
* Number of messages per player

### Teamfights

Since almost all information about teamfights is aggregated in players, we don't focus on feature extraction here.
* Number of fights
* Mean fight time (in sec.)
* Mean number of deaths

### Objectives

* Num of objectives
* Num of objectives per team
* Num of Aegis per team
* Num of Barracks killed per team
* Firstblood indicator per team
* Roshan kills per team
* Tower denies per team
* Tower kills per team

### Player features

### Features not used
* `player['obs']` - aggregates x, y coordinates of observations, obs_placed instead
* `player['sen']` - same reason, sen_placed instead
* len of `player['runes_log']` - `player['rune_pickups']`
* len of kills_log - no need, there is counter for kills
* len of obs_log
* len of sen_log
* `player['observers_placed']`
* `account_id_hash`
* runes
* `player[dn_t]` - use the number of denies only
* pred_vict - categorical, low variance
* randomed - categorical, low variance
* `player[ability_upgrades]`

#### Main features

* `level` - categorical
* `kills`
* `deaths`
* `assists`
* `denies`
* `nearby_creep_death_count`
* `obs_placed`
* `sen_placed`
* `creeps_stacked`
* `camps_stacked`
* `rune_pickups`
* `teamfight_participation`
* `max_health`
* `health_frac = health / max_health`
* pings


#### Life_state

* dead_sec
* dead_frac
* magic_sec
* magic_frac

#### Reasons

* net_gold
* gold_reasons
* gold_reasons_frac
* net_xp
* xp_reasons
* xp_reasons_frac

#### Team-aggregated

* Level difference

#### Items

* len of hero_stash
* add items from hero_stash
* net worth

#### Logs

* len of obs_left_log
* len of sen_left_log
* len of purchase_log
* len of buyback_log 

#### delta-time

using times, collect features from delta-time features `gold_t`, `xp_t`
* exponential corrected gold/sec
* exponential corrected xp/sec

### Actions

* binary-encoded actions

### Location features

All this features are hard to infer because of the unknown scales for coordinates.
My experiments with position visualization don't look very realistic, with players
stuck off-map sometimes.
* x
* y
* lane
* proximity to player's base
* proximity to enemy's base
------------------
* team centroid proximity to self base (not done)
* team centroid proximity to enemy base (not done)

### FAQ

Q: There is negative value in time!

A: This means that action has happenned in the beginning phase of the game, before the creeps were spawned.

Q: How does player_slot correspond to team?

A: Slot < 128 -> Radiant team, otherwise Dire

Q: What was the version of game when the data was collected?

A: Assuming data was collected on the single game version, it is between 7.07 and 7.19.
This was found by analyzing hero picks in train and test games, and then comparing them to [heroes release dates](https://dota2.gamepedia.com/Heroes_by_release). `dota_map.png` is for 7.07.

Q: What is player slot?

A: This field denotes player team (which is relevant) and position in a team (which is not). There are 10 unique values - `[0, 1, 2, 3, 4, 128, 129, 130, 131, 132]`. First five are for team Radiant, next five are for Dire.

Q: What is better: Bag-of-Roles or Bag-of-Roles-Levels?

A: ?

