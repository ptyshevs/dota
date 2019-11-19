import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def draw_players(players, scale=5.12, offset=5, path_to_map='dota_map.jpg'):
    if 'init_map' not in dir(draw_players):
        draw_players.init_map = np.array(Image.open(path_to_map))
    map = draw_players.init_map.copy()
    for p in players:
        x = int(p['x'] * scale)
        y = int(p['y'] * scale)
        color = (255, 0, 0) if p['player_slot'] < 127 else (0, 255, 0)
        map[x-offset:x+offset,y-offset:y+offset] = color
    plt.figure(figsize=(12, 12))
    plt.axis('off')
    plt.imshow(map)
    plt.show()