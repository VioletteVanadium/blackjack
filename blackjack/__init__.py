import numpy as np
from .textures import CARD_BACKS

SCREEN_TITLE = "Black Jack"
SCREEN_SIZE = np.array([1920, 1080])
SEAT_PADDING = 20
CARD_SPACING = np.array([26, 76])
CARD_SCALE = 0.4
CARD_SIZE = CARD_SCALE * np.array(CARD_BACKS["red"].size)
