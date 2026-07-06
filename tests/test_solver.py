import pytest

from wordle_solver.game import Clue, score_guess
from wordle_solver.solver import Solver, rank_guesses

G = Clue.GREEN
Y = Clue.YELLOW
B = Clue.GREY

ALL_GREEN = (G, G, G, G, G)


def make_solver(*extra):
    """Solver with a small, controlled answer list."""
    answers = ["crane", "crave", "trace", "grace", "brace"]
    return Solver(answers, list(extra))


class TestSolverApply:
    def test_all_candidates_initially(self):
        s = make_solver()
        assert set(s.candidates) == {"crane", "crave", "trace", "grace", "brace"}

    def test_apply_narrows_candidates(self):
        s = make_solver()
        # scoring "crane" against "crane" → all green → only "crane" remains
        s.apply("crane", ALL_GREEN)
        assert s.candidates == ["crane"]

    def test_apply_chain(self):
        s = make_solver()
        # first clue: 'c' correct, 'r' present, rest absent/wrong
        pattern1 = score_guess("crane", "crave")
        s.apply("crane", pattern1)
        # 'crave' must still be a candidate; 'grace' and 'brace' may or may not be
        assert "crave" in s.candidates
        assert "crane" not in s.candidates

    def test_apply_empty_candidates_on_no_match(self):
        s = make_solver()
        # impossible pattern eliminates everything
        s.apply("zzzzz", ALL_GREEN)
        assert s.candidates == []

    def test_reset_restores_all_candidates(self):
        s = make_solver()
        s.apply("crane", ALL_GREEN)
        s.reset()
        assert set(s.candidates) == {"crane", "crave", "trace", "grace", "brace"}

    def test_reset_clears_history(self):
        s = make_solver()
        s.apply("crane", ALL_GREEN)
        s.reset()
        assert s.history == []

    def test_is_solved_after_all_green(self):
        s = make_solver()
        s.apply("crane", ALL_GREEN)
        assert s.is_solved()

    def test_is_solved_false_initially(self):
        assert not make_solver().is_solved()


class TestHardModeConstraints:
    def test_green_positions_extracted(self):
        s = make_solver()
        s.apply("crane", (G, B, B, B, B))   # 'c' locked at position 0
        green, _ = s.hard_mode_constraints()
        assert green == {0: "c"}

    def test_yellow_minimum_count(self):
        s = make_solver()
        s.apply("crane", (B, Y, B, B, B))   # 'r' must appear at least once
        _, min_count = s.hard_mode_constraints()
        assert min_count["r"] >= 1

    def test_multiple_greens_accumulated(self):
        s = make_solver()
        s.apply("crane", (G, G, B, B, B))
        s.apply("crave", (G, G, B, G, B))
        green, _ = s.hard_mode_constraints()
        assert green[0] == "c"
        assert green[1] == "r"
        assert green[3] == "v"

    def test_duplicate_yellow_counts_correctly(self):
        s = make_solver()
        # Two 'a's in a guess, both yellow → need at least 2 'a's
        s.apply("llama", (B, B, Y, B, Y))
        _, min_count = s.hard_mode_constraints()
        assert min_count["a"] >= 2


class TestHardModePool:
    def test_no_history_returns_all_words(self):
        s = make_solver("extra1", "extra2")
        pool = s.hard_mode_pool()
        assert set(pool) == set(s.all_words)

    def test_green_constraint_filters_pool(self):
        s = make_solver()
        s.apply("crane", (G, B, B, B, B))   # first letter must be 'c'
        pool = s.hard_mode_pool()
        assert all(w[0] == "c" for w in pool)

    def test_yellow_constraint_filters_pool(self):
        s = make_solver()
        s.apply("crane", (B, Y, B, B, B))   # 'r' must be present
        pool = s.hard_mode_pool()
        assert all("r" in w for w in pool)

    def test_word_violating_green_excluded(self):
        s = make_solver()
        s.apply("crane", (G, B, B, B, B))   # 'c' at position 0
        pool = s.hard_mode_pool()
        assert "trace" not in pool   # starts with 't'


class TestRankGuesses:
    def test_returns_at_most_top_n(self):
        answers = ["crane", "crave", "trace", "grace", "brace"]
        pool = answers[:]
        results = rank_guesses(pool, answers, top_n=3)
        assert len(results) <= 3

    def test_possible_answers_tagged(self):
        answers = ["crane", "crave"]
        pool = answers + ["zzzzz"]
        results = rank_guesses(pool, answers, top_n=10)
        by_word = {w: is_ans for w, _, is_ans in results}
        assert by_word["crane"] is True
        assert by_word["crave"] is True
        assert by_word["zzzzz"] is False

    def test_scores_descending(self):
        answers = ["crane", "crave", "trace", "grace", "brace"]
        results = rank_guesses(answers, answers, top_n=5)
        scores = [s for _, s, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_single_candidate_returned(self):
        answers = ["crane"]
        results = rank_guesses(answers, answers, top_n=5)
        assert len(results) == 1
        assert results[0][0] == "crane"
