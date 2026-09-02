import json
from datetime import date
from unittest.mock import patch

from wordle_solver.nyt_check import fetch_todays_answer, maybe_check_nyt_word
from wordle_solver.solver import Solver


def _write_lists(data_dir, answers, guesses):
    (data_dir / "answers.txt").write_text("\n".join(answers) + "\n")
    (data_dir / "guesses.txt").write_text("\n".join(guesses) + "\n")


def _mock_response(body: dict):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(body).encode()

    return _Resp()


class TestFetchTodaysAnswer:
    def test_returns_solution_on_success(self):
        with patch("wordle_solver.nyt_check.urllib.request.urlopen",
                   return_value=_mock_response({"solution": "CRANE"})):
            assert fetch_todays_answer() == "crane"

    def test_returns_none_on_network_error(self):
        with patch("wordle_solver.nyt_check.urllib.request.urlopen", side_effect=OSError("boom")):
            assert fetch_todays_answer() is None

    def test_returns_none_on_malformed_body(self):
        with patch("wordle_solver.nyt_check.urllib.request.urlopen",
                   return_value=_mock_response({"solution": "notfive"})):
            assert fetch_todays_answer() is None


class TestMaybeCheckNytWord:
    def test_skip_flag_short_circuits(self, tmp_path):
        solver = Solver(["crane"], ["trace"])
        with patch("wordle_solver.nyt_check.fetch_todays_answer") as fetch:
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=tmp_path / "state.json",
                                           skip=True)
        assert result is None
        fetch.assert_not_called()

    def test_cache_hit_skips_fetch(self, tmp_path):
        _write_lists(tmp_path, ["crane"], ["trace"])
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps({"last_checked": date.today().isoformat()}))
        solver = Solver(["crane"], ["trace"])

        with patch("wordle_solver.nyt_check.fetch_todays_answer") as fetch:
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path)

        assert result is None
        fetch.assert_not_called()

    def test_adds_missing_word_and_updates_state(self, tmp_path):
        _write_lists(tmp_path, ["crane"], ["zesty"])
        state_path = tmp_path / "state.json"
        solver = Solver(["crane"], ["zesty"])

        with patch("wordle_solver.nyt_check.fetch_todays_answer", return_value="zesty"):
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path)

        assert result == "zesty"
        assert "zesty" in solver.answers
        assert "zesty" not in solver.extra_guesses
        assert "zesty" in solver.candidates
        assert (tmp_path / "answers.txt").read_text().splitlines() == ["crane", "zesty"]
        assert json.loads(state_path.read_text())["last_checked"]

    def test_already_known_word_is_noop_but_updates_state(self, tmp_path):
        _write_lists(tmp_path, ["crane"], [])
        state_path = tmp_path / "state.json"
        solver = Solver(["crane"], [])

        with patch("wordle_solver.nyt_check.fetch_todays_answer", return_value="crane"):
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path)

        assert result is None
        assert json.loads(state_path.read_text())["last_checked"]

    def test_network_failure_does_not_update_state(self, tmp_path):
        _write_lists(tmp_path, ["crane"], [])
        state_path = tmp_path / "state.json"
        solver = Solver(["crane"], [])

        with patch("wordle_solver.nyt_check.fetch_todays_answer", return_value=None):
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path)

        assert result is None
        assert not state_path.exists()

    def test_force_bypasses_cache(self, tmp_path):
        _write_lists(tmp_path, ["crane"], ["zesty"])
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps({"last_checked": date.today().isoformat()}))
        solver = Solver(["crane"], ["zesty"])

        with patch("wordle_solver.nyt_check.fetch_todays_answer", return_value="zesty") as fetch:
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path, force=True)

        fetch.assert_called_once()
        assert result == "zesty"

    def test_corrupt_state_file_treated_as_empty(self, tmp_path):
        _write_lists(tmp_path, ["crane"], [])
        state_path = tmp_path / "state.json"
        state_path.write_text("not json")
        solver = Solver(["crane"], [])

        with patch("wordle_solver.nyt_check.fetch_todays_answer", return_value=None):
            result = maybe_check_nyt_word(solver, data_dir=tmp_path, state_path=state_path)

        assert result is None
