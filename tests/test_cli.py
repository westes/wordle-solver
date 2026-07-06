import pytest

from wordle_solver.game import Clue
from wordle_solver.cli import parse_line, hard_mode_violation

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
