"""Loading of the bundled word lists.

Both files come from the original NYT Wordle source: `answers.txt` is the
2,315-word possible-answer list, `guesses.txt` is the additional ~10,657
words accepted as valid guesses but never used as answers.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> list:
    path = DATA_DIR / filename
    return [w.strip().lower() for w in path.read_text().splitlines() if w.strip()]


def load_answers() -> list:
    return _load("answers.txt")


def load_extra_guesses() -> list:
    return _load("guesses.txt")


def load_all_valid_words() -> list:
    return load_answers() + load_extra_guesses()
