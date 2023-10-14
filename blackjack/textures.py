import itertools as it
import os

import arcade

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

CARD_BACKS: dict[str, arcade.texture.Texture] = {
    name: arcade.load_texture(
        os.path.join(ASSETS, f"cards/backs/{name}.png"),
        hit_box_algorithm=None,
    )
    for name in ["red", "blue"]
}
CARD_FACES: dict[tuple[str, int], arcade.texture.Texture] = {
    (suit, value): arcade.load_texture(
        os.path.join(ASSETS, f"cards/faces/{value}{suit}.png"),
        hit_box_algorithm=None,
    )
    for (suit, value) in it.product(
        ["S", "H", "C", "D"], range(1, 14)
    )
}
TABLE = arcade.load_texture(
    os.path.join(ASSETS, "felt_green.jpg"), hit_box_algorithm=None
)
