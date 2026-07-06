"""Feedback simulation matching Wordle's own coloring algorithm."""

from enum import IntEnum


class Clue(IntEnum):
    GREY = 0
    YELLOW = 1
    GREEN = 2


CLUE_CHARS = {Clue.GREEN: "G", Clue.YELLOW: "Y", Clue.GREY: "B"}

# Accept a few common shorthand alphabets when parsing user input.
_CHAR_TO_CLUE = {
    "G": Clue.GREEN, "2": Clue.GREEN,
    "Y": Clue.YELLOW, "1": Clue.YELLOW,
    "B": Clue.GREY, "0": Clue.GREY, ".": Clue.GREY, "-": Clue.GREY,
}


def score_guess(guess: str, answer: str) -> tuple:
    """Return the clue Wordle would show for `guess` against the true `answer`.

    Two-pass algorithm: greens first, then yellows against leftover letters,
    so duplicate letters are handled the same way the real game does.
    """
    n = len(guess)
    result = [Clue.GREY] * n
    remaining = list(answer)

    for i in range(n):
        if guess[i] == remaining[i]:
            result[i] = Clue.GREEN
            remaining[i] = None

    for i in range(n):
        if result[i] == Clue.GREEN:
            continue
        letter = guess[i]
        if letter in remaining:
            result[i] = Clue.YELLOW
            remaining[remaining.index(letter)] = None

    return tuple(result)


def pattern_to_str(pattern) -> str:
    return "".join(CLUE_CHARS[c] for c in pattern)


def pattern_to_digits(pattern) -> str:
    return "".join(str(int(c)) for c in pattern)


def str_to_pattern(s: str) -> tuple:
    s = s.strip()
    try:
        return tuple(_CHAR_TO_CLUE[ch.upper()] for ch in s)
    except KeyError as e:
        raise ValueError(f"Unrecognized clue character: {e.args[0]!r}") from None
