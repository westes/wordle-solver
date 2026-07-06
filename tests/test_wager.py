from wordle_solver.game import Clue
from wordle_solver.wager import Wager

G = Clue.GREEN
Y = Clue.YELLOW
B = Clue.GREY


class TestWagerCost:
    def test_all_correct_costs_one_each(self):
        w = Wager()
        assert w.cost_of((G, G, G, G, G)) == 5

    def test_all_present_costs_two_each(self):
        w = Wager()
        assert w.cost_of((Y, Y, Y, Y, Y)) == 10

    def test_all_absent_costs_three_each(self):
        w = Wager()
        assert w.cost_of((B, B, B, B, B)) == 15

    def test_mixed_cost(self):
        w = Wager()
        assert w.cost_of((G, Y, B, G, B)) == 1 + 2 + 3 + 1 + 3


class TestWagerAccumulation:
    def test_add_accumulates_round_and_session(self):
        w = Wager()
        w.add((G, G, G, G, G))   # cost 5
        w.add((B, B, B, B, B))   # cost 15
        assert w.round_total == 20
        assert w.session_total == 20

    def test_new_round_resets_round_total_only(self):
        w = Wager()
        w.add((G, G, G, G, G))   # cost 5
        w.new_round()
        w.add((B, B, B, B, B))   # cost 15 in new round
        assert w.round_total == 15
        assert w.session_total == 20   # unchanged across rounds

    def test_add_returns_cost_of_that_guess(self):
        w = Wager()
        cost = w.add((G, Y, B, G, B))
        assert cost == 1 + 2 + 3 + 1 + 3

    def test_fresh_wager_starts_at_zero(self):
        w = Wager()
        assert w.round_total == 0
        assert w.session_total == 0


class TestWagerPrices:
    def test_set_prices_changes_cost(self):
        w = Wager()
        w.set_prices(10, 20, 30)
        assert w.cost_of((G, Y, B)) == 60

    def test_reset_via_set_prices_default(self):
        w = Wager()
        w.set_prices(10, 20, 30)
        w.set_prices(1, 2, 3)
        assert w.cost_of((G, Y, B)) == 6

    def test_prices_str_contains_values(self):
        w = Wager()
        s = w.prices_str()
        assert "$1" in s
        assert "$2" in s
        assert "$3" in s

    def test_prices_str_after_custom_prices(self):
        w = Wager()
        w.set_prices(5, 10, 15)
        s = w.prices_str()
        assert "$5" in s
        assert "$10" in s
        assert "$15" in s
