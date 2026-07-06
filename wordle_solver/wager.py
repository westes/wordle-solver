"""Tracks a $-per-letter wager score alongside the solver.

Default rule: $1 per correct-spot letter, $2 per present-but-wrong-spot
letter, $3 per absent letter — tune with the `/price` command if your
wager uses different numbers.
"""

from dataclasses import dataclass, field

from .game import Clue

DEFAULT_PRICES = {Clue.GREEN: 1, Clue.YELLOW: 2, Clue.GREY: 3}


@dataclass
class Wager:
    prices: dict = field(default_factory=lambda: dict(DEFAULT_PRICES))
    round_total: int = 0
    session_total: int = 0

    def cost_of(self, pattern) -> int:
        return sum(self.prices[clue] for clue in pattern)

    def add(self, pattern) -> int:
        cost = self.cost_of(pattern)
        self.round_total += cost
        self.session_total += cost
        return cost

    def new_round(self) -> None:
        self.round_total = 0

    def set_prices(self, green: int, yellow: int, grey: int) -> None:
        self.prices = {Clue.GREEN: green, Clue.YELLOW: yellow, Clue.GREY: grey}

    def prices_str(self) -> str:
        return (f"correct=${self.prices[Clue.GREEN]}  "
                f"present=${self.prices[Clue.YELLOW]}  "
                f"absent=${self.prices[Clue.GREY]}")
