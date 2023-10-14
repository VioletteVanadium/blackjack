import random
from typing import Iterable, Optional

import numpy as np
from arcade import BasicSprite, SpriteList, easing

from . import CARD_SCALE, SCREEN_SIZE, SEAT_PADDING
from .seat import Seat
from .textures import CARD_BACKS, CARD_FACES
from .utilities import SequenceEasing


class Card(BasicSprite):
    def __init__(self, suit: str, value: int, back: str, scale: float):
        self.suit = suit
        self.value = value
        self.face_texture = CARD_FACES[suit, value]
        self.back_texture = CARD_BACKS[back]
        super().__init__(self.back_texture, scale=scale)
        self.texture = self.back_texture
        self.dealt = False

    def swap_texture(self):
        if self.texture == self.back_texture:
            self.texture = self.face_texture
        else:
            self.texture = self.back_texture

    def easing_swap_texture(self, easing_data: SequenceEasing, duration=0.3):
        mid_time = duration / 2

        easing_data.series().add_easing_data(
            self, "width", easing.ease_value(self.width, 0, time=mid_time)
        )
        easing_data.series().add_function_data(
            self, "swap_texture", (), {}
        )
        easing_data.series().add_easing_data(
            self, "width", easing.ease_value(0, self.width, time=mid_time)
        )


class Deck(SpriteList):
    def __init__(self, window_width: int, window_height: int, card_back: str):
        super().__init__()
        self.scale = 0.0
        self.anchor = np.zeros(2)
        self.offset = 0.0
        self.card_back = card_back
        self.easing_data = SequenceEasing()

    @property
    def card_scale(self):
        return self.scale * CARD_SCALE

    def add_deck(self):
        new_cards = list(CARD_FACES.keys())
        random.shuffle(new_cards)

        card_scale = self.card_scale
        for i, (suit, value) in enumerate(new_cards):
            self.insert(0, Card(suit, value, self.card_back, card_scale))

        offset = self.offset
        anchor = self.anchor
        for i, card in enumerate(self):
            card.left = anchor[0] + int(offset * i)
            card.top = anchor[1] - int(offset * i)

    def deal_card(
        self,
        seat: Seat,
        flip: bool = True,
        start_time: float = 0.0,
        duration: float = 0.5,
    ):
        # determine which card we are sending to the seat
        if len(self) == 0:
            self.add_deck()
        card = None
        for card in reversed(self):
            if not card.dealt:
                break
        card.dealt = True

        # determine where on the screen we are sending the card
        new_left, new_top = seat.card_anchors[len(seat)]

        # midpoint is important for texture swapping and parent hand-over
        mid_time = duration / 2
        mid_left = card.left + (new_left - card.left) / 2
        mid_top = card.top + (new_top - card.top) / 2

        # translate to midpoint
        self.easing_data.series().add_easing_data(
            card, "left", easing.ease_value(card.left, mid_left, time=mid_time)
        )
        self.easing_data.parallel().add_easing_data(
            card, "top", easing.ease_value(card.top, mid_top, time=mid_time)
        )

        if flip:
            # and half-flip
            self.easing_data.parallel().add_easing_data(
                card,
                "width",
                easing.ease_value(card.width, 0, time=mid_time),
            )
            self.easing_data.parallel().add_function_data(
                card, "swap_texture", (), {}, delay=mid_time
            )

        # exchange card parent
        self.easing_data.series().add_function_data(
            self, "remove", (card,), {}, delay=0.1
        )
        self.easing_data.parallel().add_function_data(
            seat, "append", (card,), {}, delay=0.1
        )

        # translate to final location
        self.easing_data.parallel().add_easing_data(
            card, "left", easing.ease_value(mid_left, new_left, time=mid_time)
        )
        self.easing_data.parallel().add_easing_data(
            card, "top", easing.ease_value(mid_top, new_top, time=mid_time)
        )
        if flip:
            # and finish the second half of the flip
            self.easing_data.parallel().add_easing_data(
                card,
                "width",
                easing.ease_value(0, card.width, time=mid_time),
            )

        # if the screen has been resized during the animation, the final
        # location may be slightly off, so we will re-anchor all of the cards
        # in the new_parent's hand
        self.easing_data.series().add_function_data(
            seat, "anchor_cards", (), {}
        )

    def on_resize(self, window_width, window_height):
        self.scale = min([window_width, window_height] / SCREEN_SIZE)
        self.anchor = [0, window_height] + self.scale * np.array(
            [SEAT_PADDING, -SEAT_PADDING]
        )
        self.offset = self.scale * CARD_SCALE / 2
        for i, card in enumerate(self):
            card.scale = self.scale * CARD_SCALE
            card.left = self.anchor[0] + int(self.offset * i)
            card.top = self.anchor[1] - int(self.offset * i)

    def on_update(
        self, delta_time: float = 1 / 60, names: Optional[Iterable[str]] = None
    ):
        self.easing_data.on_update(delta_time)

    def on_draw(self):
        self.draw()
