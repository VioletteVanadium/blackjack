import numpy as np
from arcade import SpriteList, color, shape_list

from . import CARD_SCALE, CARD_SIZE, CARD_SPACING, SCREEN_SIZE, SEAT_PADDING
from .utilities import centered_text


class Seat(SpriteList):
    def __init__(self, window_width: int, window_height: int, **anchor):
        super().__init__()
        self.scale_xy = [window_width, window_height] / SCREEN_SIZE
        self.scale = min(self.scale_xy)
        self.card_anchors = [np.zeros(2) for _ in range(11)]
        self.anchor = np.zeros(2)  # the top-left corner of the seat
        self.placemat: shape_list.Shape
        self.highlight: shape_list.Shape

        if "left" in anchor:
            self.anchor[0] = anchor["left"]
        elif "center_x" in anchor:
            self.anchor[0] = anchor["center_x"] - self.width / 2
        elif "right" in anchor:
            self.anchor[0] = anchor["right"] - self.width
        else:
            raise ValueError(
                "anchor must contain one of {'left', 'right', 'center_x'}"
            )

        if "top" in anchor:
            self.anchor[1] = anchor["top"]
        elif "center_y" in anchor:
            self.anchor[1] = anchor["center_y"] + self.height / 2
        elif "bottom" in anchor:
            self.anchor[1] = anchor["bottom"] + self.height
        else:
            raise ValueError(
                "anchor must contain one of {'top', 'center_y', 'bottom'}"
            )

    @property
    def width(self):
        return self.scale * (
            CARD_SIZE[0] + 5 * CARD_SPACING[0] + 2 * SEAT_PADDING
        )

    @property
    def height(self):
        return self.scale * (CARD_SIZE[1] + CARD_SPACING[1] + 2 * SEAT_PADDING)

    @property
    def value_total(self):
        total = 0
        aces = 0
        for card in self:
            if card is None:
                continue
            if card.value == 1:
                aces += 1
            elif card.value >= 10:
                total += 10
            else:
                total += card.value
        if aces == 0:
            return total
        tmp = 11 + aces - 1
        if tmp + total <= 21:
            return tmp + total
        return aces + total

    def setup_rectangles(self):
        rect_kwargs = dict(
            center_x=self.anchor[0] + self.width / 2,
            center_y=self.anchor[1] - self.height / 2,
            width=self.width,
            height=self.height,
        )
        self.placemat = shape_list.create_rectangle_filled(
            color=(*color.BLACK[:3], 0x44), **rect_kwargs
        )
        self.highlight = shape_list.create_rectangle_outline(
            color=color.WHITE,
            border_width=2,
            **rect_kwargs,
        )

    def anchor_cards(self):
        for (left, top), card in zip(self.card_anchors, self):
            card.scale = self.scale * CARD_SCALE
            card.left = left
            card.top = top

    def on_resize(self, window_width, window_height):
        self.anchor /= self.scale_xy
        self.scale_xy = [window_width, window_height] / SCREEN_SIZE
        self.anchor *= self.scale_xy
        self.scale = min(self.scale_xy)

        for i, anchor in enumerate(self.card_anchors):
            if i < 6:
                self.card_anchors[i][0] = self.anchor[0] + self.scale * (
                    i * CARD_SPACING[0] + SEAT_PADDING
                )
                self.card_anchors[i][1] = self.anchor[1] - self.scale * (
                    SEAT_PADDING
                )
            else:
                self.card_anchors[i][0] = self.anchor[0] + self.scale * (
                    (i - 5.5) * CARD_SPACING[0] + SEAT_PADDING
                )
                self.card_anchors[i][1] = self.anchor[1] - self.scale * (
                    CARD_SPACING[1] + SEAT_PADDING
                )
        self.setup_rectangles()
        self.anchor_cards()

    def on_draw(self, highlight: bool = False):
        self.placemat.draw()
        if highlight:
            self.highlight.draw()
        self.draw()


class Dealer(Seat):
    def will_stay(self):
        if self.value_total < 17:
            return False
        return True

    def on_draw(self, highlight: bool = False):
        super().on_draw(highlight=highlight)
        center_y = self.anchor[1] - self.scale * SEAT_PADDING / 2
        centered_text(
            self.value_total,
            start_x=self.anchor[0] + self.width / 2,
            start_y=center_y,
            color=color.WHITE,
        ).draw()


class Player(Seat):
    def __init__(self, window_width, window_height, purse=1000, **anchor):
        super().__init__(window_width, window_height, **anchor)
        self.bet = 100
        self.purse = purse
        self.bet_resolved = None

    def resolve_bet(self, dealer_total=None):
        if self.bet_resolved:
            return

        value = self.value_total

        # Black Jack is an auto-win condition
        if value == 21 and len(self) == 2:
            self.purse += int(1.5 * self.bet)
            self.bet_resolved = "W"
            return
        # Bust is an auto lose condition
        if value > 21:
            self.purse -= self.bet
            self.bet_resolved = "L"
            return
        # any other condition requires knowledge of the dealer's score
        if dealer_total is None:
            return

        # we know the player hasn't busted, so...
        if dealer_total > 21:
            # the dealer busted, player wins
            self.purse += self.bet
            self.bet_resolved = "W"
        elif dealer_total > value:
            # the dealer has a higher score
            self.purse -= self.bet
            self.bet_resolved = "L"
        elif value > dealer_total:
            # the player has a higher score
            self.purse += self.bet
            self.bet_resolved = "W"
        else:
            # tie, aka "push"
            self.bet_resolved = "T"

    def on_draw(self, highlight):
        super().on_draw(highlight)
        purse_color = color.WHITE
        if self.bet_resolved == "W":
            purse_color = color.GREEN_YELLOW
        elif self.bet_resolved == "L":
            purse_color = color.RED_ORANGE

        center_y = self.anchor[1] - self.scale * SEAT_PADDING / 2
        centered_text(
            self.purse,
            start_x=self.anchor[0] + self.width / 4,
            start_y=center_y,
            color=purse_color,
        ).draw()
        centered_text(
            self.value_total,
            start_x=self.anchor[0] + 2 * self.width / 4,
            start_y=center_y,
            color=color.WHITE,
        ).draw()
        centered_text(
            self.bet,
            start_x=self.anchor[0] + 3 * self.width / 4,
            start_y=center_y,
            color=color.WHITE,
        ).draw()
