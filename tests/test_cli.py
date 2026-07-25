import argparse

import pytest

from wordle_solver import cli
from wordle_solver.game import Clue, score_guess
from wordle_solver.cli import handle_slash_command, parse_line, hard_mode_violation, print_suggestions
from wordle_solver.solver import Solver, rank_guesses
from wordle_solver.wager import Wager

G = Clue.GREEN
Y = Clue.YELLOW
B = Clue.GREY


class TestParseLine:
    def test_digit_encoding(self):
        guess, pattern = parse_line("c2r1a0n0e0")
        assert guess == "crane"
        assert pattern == (G, Y, B, B, B)

    def test_letter_encoding(self):
        guess, pattern = parse_line("cGrYaBnBeB")
        assert guess == "crane"
        assert pattern == (G, Y, B, B, B)

    def test_spaces_stripped(self):
        guess, pattern = parse_line("c 2 r 1 a 0 n 0 e 0")
        assert guess == "crane"
        assert pattern == (G, Y, B, B, B)

    def test_uppercase_letters_lowercased(self):
        guess, _ = parse_line("C2R1A0N0E0")
        assert guess == "crane"

    def test_all_green(self):
        _, pattern = parse_line("c2r2a2n2e2")
        assert pattern == (G, G, G, G, G)

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError):
            parse_line("c2r1a0")   # only 3 pairs

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            parse_line("c2r1a0n0e0x0")   # 6 pairs

    def test_digit_in_letter_position_raises(self):
        with pytest.raises(ValueError):
            parse_line("12r1a0n0e0")   # position 0 is '1', not a letter


class TestHardModeViolation:
    def test_valid_guess_returns_none(self):
        green = {0: "c", 1: "r"}
        from collections import Counter
        min_count = Counter({"a": 1})
        assert hard_mode_violation("crane", green, min_count) is None

    def test_wrong_green_position_detected(self):
        green = {0: "c"}
        from collections import Counter
        result = hard_mode_violation("trace", green, Counter())
        assert result is not None
        assert "1" in result   # position 1 (1-indexed)

    def test_missing_required_letter_detected(self):
        from collections import Counter
        min_count = Counter({"r": 1})
        result = hard_mode_violation("piano", {}, min_count)
        assert result is not None
        assert "R" in result

    def test_missing_duplicate_letter_detected(self):
        # Word needs two 'e's
        from collections import Counter
        min_count = Counter({"e": 2})
        result = hard_mode_violation("crane", {}, min_count)
        assert result is not None   # "crane" has only one 'e'

    def test_satisfies_duplicate_requirement(self):
        from collections import Counter
        min_count = Counter({"e": 2})
        result = hard_mode_violation("geese", {}, min_count)
        assert result is None   # "geese" has three 'e's — satisfies ≥2

    def test_empty_constraints_always_none(self):
        from collections import Counter
        assert hard_mode_violation("crane", {}, Counter()) is None


class TestAddWordCommand:
    def _solver(self):
        return Solver(answers=["crane", "trace"], extra_guesses=["about", "zesty"])

    def _opts(self):
        return argparse.Namespace(top=10, position_weight=1.0, presence_weight=1.0)

    def test_rejects_wrong_arg_count(self, capsys):
        solver = self._solver()
        handle_slash_command("/addword", solver, Wager(), {}, solver.answers, self._opts())
        assert "Usage" in capsys.readouterr().out
        assert solver.answers == ["crane", "trace"]

    def test_rejects_non_alpha_or_wrong_length(self, capsys):
        solver = self._solver()
        handle_slash_command("/addword abc12", solver, Wager(), {}, solver.answers, self._opts())
        assert "5 letters" in capsys.readouterr().out
        assert solver.answers == ["crane", "trace"]

    def test_already_in_answers_short_circuits(self, capsys, monkeypatch):
        solver = self._solver()
        called = False

        def fake_add(word):
            nonlocal called
            called = True
            return {"added": False, "removed_from_guesses": False}

        monkeypatch.setattr(cli, "add_answer_word", fake_add)
        handle_slash_command("/addword crane", solver, Wager(), {}, solver.answers, self._opts())

        assert "already" in capsys.readouterr().out
        assert not called
        assert solver.answers == ["crane", "trace"]

    def test_adds_word_and_removes_from_guesses(self, capsys, monkeypatch):
        solver = self._solver()
        monkeypatch.setattr(
            cli, "add_answer_word",
            lambda word: {"added": True, "removed_from_guesses": True},
        )

        handle_slash_command("/addword zesty", solver, Wager(), {}, solver.answers, self._opts())

        out = capsys.readouterr().out
        assert "Added ZESTY" in out
        assert "removed it from guesses.txt" in out
        assert solver.answers == ["crane", "trace", "zesty"]
        assert "zesty" not in solver.extra_guesses

    def test_new_candidate_consistent_with_history_is_added(self, capsys, monkeypatch):
        solver = self._solver()
        # Derive the pattern "trace" would actually produce against "chase",
        # so the new word is consistent with history by construction.
        pattern = score_guess("trace", "chase")
        solver.apply("trace", pattern)
        monkeypatch.setattr(
            cli, "add_answer_word",
            lambda word: {"added": True, "removed_from_guesses": False},
        )

        handle_slash_command("/addword chase", solver, Wager(), {}, solver.answers, self._opts())

        assert "chase" in solver.candidates


class TestPrintSuggestionsOrder:
    def test_possible_answers_printed_in_heuristic_order_not_alphabetical(self, capsys):
        # Deliberately not alphabetical so a bug that re-sorts alphabetically
        # would be caught: alphabetical order here is amigo, aroma, mango.
        answers = ["mango", "amigo", "aroma"]
        solver = Solver(answers=answers, extra_guesses=[])

        print_suggestions(solver, top_n=10, position_weight=1.0, presence_weight=1.0)

        expected_order = [
            word for word, _, _ in
            rank_guesses(answers, answers, top_n=len(answers), position_weight=1.0, presence_weight=1.0)
        ]
        assert expected_order != sorted(answers)  # sanity check the fixture is non-alphabetical

        printed_line = capsys.readouterr().out.splitlines()[2]
        assert printed_line.strip() == ", ".join(expected_order)
