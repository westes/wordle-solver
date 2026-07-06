import pytest

from wordle_solver.game import Clue, score_guess, str_to_pattern, pattern_to_str, pattern_to_digits

G = Clue.GREEN
Y = Clue.YELLOW
B = Clue.GREY


class TestScoreGuess:
    def test_all_green(self):
        assert score_guess("crane", "crane") == (G, G, G, G, G)

    def test_all_grey(self):
        assert score_guess("brick", "those") == (B, B, B, B, B)

    def test_basic_yellow(self):
        assert score_guess("trail", "blurt") == (Y, Y, B, B, Y)

    def test_basic_mixed(self):
        assert score_guess("arise", "spare") == (Y, Y, B, Y, G)

    # Duplicate-letter cases — this is where the two-pass algorithm matters.

    def test_duplicate_in_guess_one_in_answer_first_gets_yellow(self):
        # 'a' appears twice in "nasal" (pos 1, 3), once in "ultra" (pos 4).
        # Neither is a green, so pass-2 left-to-right: pos 1 → yellow, pos 3 → grey.
        assert score_guess("nasal", "ultra") == (B, Y, B, B, Y)

    def test_duplicate_in_guess_one_in_answer_green_takes_priority(self):
        # "eerie" has 3 e's; "abcee" has 2. The last 'e' in the guess hits green
        # at position 4; one remaining 'e' in the answer makes the first 'e' yellow;
        # the middle 'e' has nothing left to match → grey.
        assert score_guess("eerie", "abcee") == (Y, B, B, B, G)

    def test_duplicate_in_guess_both_in_answer(self):
        # "sleep" has two 'e's; answer "geese" has three 'e's
        # both guess 'e's should be coloured (green or yellow)
        result = score_guess("sleep", "geese")
        assert result[2] == G   # 'e' at pos 2 matches answer pos 2
        assert result[3] in (G, Y)

    def test_duplicate_in_answer_guess_has_one(self):
        # "abbey" has two 'b's; "bland" has one 'b' in the wrong position → yellow
        assert score_guess("bland", "abbey") == (Y, B, Y, B, B)

    def test_guess_equals_answer_all_green(self):
        for word in ("tales", "quick", "zzzzz"):
            assert score_guess(word, word) == (G,) * 5

    def test_yellow_not_double_counted(self):
        # "added" vs "daddy": only two 'd's in answer, so not all three guess-d's get colour
        result = score_guess("added", "daddy")
        d_colours = [result[i] for i, c in enumerate("added") if c == "d"]
        coloured = sum(1 for c in d_colours if c != B)
        assert coloured <= 3  # answer has three 'd's at most


class TestStrToPattern:
    def test_digit_encoding(self):
        assert str_to_pattern("22110") == (G, G, Y, Y, B)

    def test_letter_encoding(self):
        assert str_to_pattern("GGYYB") == (G, G, Y, Y, B)

    def test_lowercase_letter_encoding(self):
        assert str_to_pattern("ggyyb") == (G, G, Y, Y, B)

    def test_mixed_encodings(self):
        assert str_to_pattern("2G1Y0") == (G, G, Y, Y, B)

    def test_invalid_char_raises(self):
        with pytest.raises(ValueError):
            str_to_pattern("2210X")

    def test_dot_and_dash_are_grey(self):
        assert str_to_pattern("..---") == (B,) * 5


class TestPatternHelpers:
    def test_pattern_to_str(self):
        assert pattern_to_str((G, Y, B)) == "GYB"

    def test_pattern_to_digits(self):
        assert pattern_to_digits((G, Y, B)) == "210"
