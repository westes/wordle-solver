"""Loading of the bundled word lists.

Both files come from the original NYT Wordle source: `answers.txt` is the
2,315-word possible-answer list, `guesses.txt` is the additional ~10,657
words accepted as valid guesses but never used as answers.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str, data_dir: Path = DATA_DIR) -> list:
    path = data_dir / filename
    return [w.strip().lower() for w in path.read_text().splitlines() if w.strip()]


def load_answers() -> list:
    return _load("answers.txt")


def load_extra_guesses() -> list:
    return _load("guesses.txt")


def load_all_valid_words() -> list:
    return load_answers() + load_extra_guesses()


def add_answer_word(word: str, data_dir: Path = DATA_DIR) -> dict:
    """Add `word` to the bundled answers list, removing it from the extra
    guesses list if it's there (the two lists are meant to be disjoint)."""
    word = word.strip().lower()
    answers = _load("answers.txt", data_dir)
    guesses = _load("guesses.txt", data_dir)

    result = {"added": False, "removed_from_guesses": False}

    if word not in answers:
        answers.append(word)
        answers.sort()
        (data_dir / "answers.txt").write_text("\n".join(answers) + "\n")
        result["added"] = True

    if word in guesses:
        guesses = [w for w in guesses if w != word]
        (data_dir / "guesses.txt").write_text("\n".join(guesses) + "\n")
        result["removed_from_guesses"] = True

    return result
