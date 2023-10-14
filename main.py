import arcade
import numpy as np

from blackjack import SCREEN_SIZE, SCREEN_TITLE
from blackjack.deck import Card, Deck
from blackjack.seat import Dealer, Player
from blackjack.textures import TABLE


class BlackJack(arcade.Window):
    def __init__(self, num_players: int):
        super().__init__(
            width=SCREEN_SIZE[0],
            height=SCREEN_SIZE[1],
            title=SCREEN_TITLE,
            fullscreen=False,
            resizable=True,
        )
        self.background_color = arcade.color.RICH_BLACK
        self.background_texture = TABLE
        self.background_scale: float

        self.num_players = num_players

        self.deck: Deck
        self.dealer: Dealer
        self.players: list[Player] = []

        self.player_idx: int = 0
        self.round_over = False

    def setup(self, new_deck: bool = False):
        width, height = self.get_size()
        if new_deck:
            self.deck = Deck(width, height, "red")
        self.dealer = Dealer(width, height, center_x=width / 2, top=height)
        players = []
        for i in range(self.num_players):
            if self.players:
                kwargs = {"purse": self.players[i].purse}
            else:
                kwargs = {}
            players.append(
                Player(
                    width,
                    height,
                    center_x=width * (i + 0.5) / self.num_players,
                    bottom=0,
                    **kwargs,
                )
            )
        self.players = players
        self.player_idx = 0
        self.round_over = False
        self.on_resize(width, height)

        for seat in self.players + [self.dealer] + self.players:
            self.deck.deal_card(seat)
        self.deck.deal_card(self.dealer, flip=False)

    def on_resize(self, width, height):
        super().on_resize(width, height)

        self.background_scale = max(
            np.array([width, height]) / self.background_texture.size
        )
        self.deck.on_resize(width, height)
        self.dealer.on_resize(width, height)
        for p in self.players:
            p.on_resize(width, height)

    def on_update(self, delta_time: float = 1 / 60):
        if not self.deck.easing_data.on_update(delta_time):
            return

        # go through players in order
        while self.players and self.player_idx < self.num_players:
            player = self.players[self.player_idx]
            if player.purse <= 0:
                self.player_idx += 1
                continue
            player.resolve_bet()
            if not player.bet_resolved and player.value_total < 21:
                break
            self.player_idx += 1

        # once we are done with the players, it is the dealer's turn, and then
        # we can resolve any remaining bets
        if self.player_idx >= self.num_players:
            hole_card: Card = self.dealer[1]
            if (
                hole_card.texture == hole_card.back_texture
                and hole_card not in self.deck.easing_data.objects
            ):
                hole_card.easing_swap_texture(self.deck.easing_data)
            if self.dealer.will_stay():
                dealer_total = self.dealer.value_total
                for player in self.players:
                    player.resolve_bet(dealer_total)
                self.round_over = True
            else:
                self.deck.deal_card(self.dealer)

    def on_draw(self):
        width, height = self.get_size()
        self.background_texture.draw_scaled(
            width / 2, height / 2, self.background_scale
        )
        self.deck.on_draw()
        for i, seat in enumerate(self.players + [self.dealer]):
            if i == self.player_idx:
                seat.on_draw(highlight=True)
            else:
                seat.on_draw(highlight=False)

    def on_key_press(self, symbol, modifier):
        if symbol == arcade.key.Q:
            exit(0)

        # any key will start a new round
        if self.round_over:
            self.setup()
            return

        # handle the players turn
        player = self.players[self.player_idx]
        if symbol == arcade.key.SPACE:
            self.deck.deal_card(player)
        elif symbol == arcade.key.ENTER:
            self.player_idx += 1


if __name__ == "__main__":
    window = BlackJack(num_players=1)
    window.setup(new_deck=True)
    arcade.run()
