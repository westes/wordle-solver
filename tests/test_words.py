from wordle_solver.words import add_answer_word


def _write_lists(tmp_path, answers, guesses):
    (tmp_path / "answers.txt").write_text("\n".join(answers) + "\n")
    (tmp_path / "guesses.txt").write_text("\n".join(guesses) + "\n")


class TestAddAnswerWord:
    def test_adds_new_word_to_answers(self, tmp_path):
        _write_lists(tmp_path, ["crane", "trace"], ["about"])

        result = add_answer_word("zesty", data_dir=tmp_path)

        assert result == {"added": True, "removed_from_guesses": False}
        assert (tmp_path / "answers.txt").read_text().splitlines() == ["crane", "trace", "zesty"]
        assert (tmp_path / "guesses.txt").read_text().splitlines() == ["about"]

    def test_word_already_in_answers_is_a_noop(self, tmp_path):
        _write_lists(tmp_path, ["crane", "trace"], ["about"])

        result = add_answer_word("crane", data_dir=tmp_path)

        assert result == {"added": False, "removed_from_guesses": False}
        assert (tmp_path / "answers.txt").read_text().splitlines() == ["crane", "trace"]

    def test_word_present_in_guesses_is_removed(self, tmp_path):
        _write_lists(tmp_path, ["crane", "trace"], ["about", "zesty"])

        result = add_answer_word("zesty", data_dir=tmp_path)

        assert result == {"added": True, "removed_from_guesses": True}
        assert (tmp_path / "answers.txt").read_text().splitlines() == ["crane", "trace", "zesty"]
        assert (tmp_path / "guesses.txt").read_text().splitlines() == ["about"]

    def test_answers_written_sorted(self, tmp_path):
        _write_lists(tmp_path, ["trace", "zesty"], [])

        add_answer_word("crane", data_dir=tmp_path)

        assert (tmp_path / "answers.txt").read_text().splitlines() == ["crane", "trace", "zesty"]
