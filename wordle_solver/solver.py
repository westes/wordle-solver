"""Candidate tracking and a frequency/positional heuristic for ranking guesses."""

from collections import Counter
from dataclasses import dataclass, field

from .game import Clue, score_guess

WORD_LEN = 5
MAX_GUESSES = 6


@dataclass
class GuessRecord:
    guess: str
    pattern: tuple


@dataclass
class Solver:
    answers: list
    extra_guesses: list
    history: list = field(default_factory=list)
    candidates: list = field(init=False)

    def __post_init__(self):
        self.candidates = list(self.answers)

    @property
    def all_words(self) -> list:
        return self.answers + self.extra_guesses

    def apply(self, guess: str, pattern: tuple) -> None:
        """Record a guess/result and narrow the remaining candidates to those
        consistent with it (by literally re-simulating Wordle's own coloring)."""
        guess = guess.lower()
        self.history.append(GuessRecord(guess, pattern))
        self.candidates = [w for w in self.candidates if score_guess(guess, w) == pattern]

    def reset(self) -> None:
        self.history.clear()
        self.candidates = list(self.answers)

    def is_solved(self) -> bool:
        return bool(self.history) and self.history[-1].pattern == (Clue.GREEN,) * WORD_LEN

    def hard_mode_constraints(self):
        """Derive the two hard-mode requirements from history so far:
        fixed green letters by position, and minimum required count per
        letter from any green/yellow marks seen."""
        green = {}
        min_count = Counter()
        for rec in self.history:
            marks_this_guess = Counter()
            for i, (ch, clue) in enumerate(zip(rec.guess, rec.pattern)):
                if clue == Clue.GREEN:
                    green[i] = ch
                    marks_this_guess[ch] += 1
                elif clue == Clue.YELLOW:
                    marks_this_guess[ch] += 1
            for ch, count in marks_this_guess.items():
                if count > min_count[ch]:
                    min_count[ch] = count
        return green, min_count

    def hard_mode_pool(self) -> list:
        """Every known word that is a *legal* next guess under hard-mode rules:
        green letters stay in place, and every yellow/green letter seen so far
        appears at least as many times as it has been confirmed."""
        if not self.history:
            return list(self.all_words)

        green, min_count = self.hard_mode_constraints()
        pool = []
        for w in self.all_words:
            if any(w[i] != ch for i, ch in green.items()):
                continue
            counts = Counter(w)
            if any(counts[ch] < need for ch, need in min_count.items()):
                continue
            pool.append(w)
        return pool


def letter_stats(words: list):
    """Per-position and overall-presence letter frequencies across `words`."""
    n = len(words)
    position_freq = [Counter() for _ in range(WORD_LEN)]
    presence_freq = Counter()
    for w in words:
        for i, ch in enumerate(w):
            position_freq[i][ch] += 1
        for ch in set(w):
            presence_freq[ch] += 1
    position_freq = [{ch: c / n for ch, c in pf.items()} for pf in position_freq]
    presence_freq = {ch: c / n for ch, c in presence_freq.items()}
    return position_freq, presence_freq


def score_word(word, position_freq, presence_freq, position_weight=1.0, presence_weight=1.0, repeat_penalty=0.85):
    """Higher score = letters that are both common overall and likely in this
    position, favoring new letters over repeats since repeats teach us less."""
    score = 0.0
    seen = set()
    for i, ch in enumerate(word):
        score += position_weight * position_freq[i].get(ch, 0.0)
        gain = presence_weight * presence_freq.get(ch, 0.0)
        score += gain if ch not in seen else -repeat_penalty * gain
        seen.add(ch)
    return score


def rank_guesses(pool, candidates, top_n=10, position_weight=1.0, presence_weight=1.0):
    """Rank `pool` words by the heuristic, computed from letter stats over the
    still-possible `candidates`. Returns (word, score, is_possible_answer)."""
    position_freq, presence_freq = letter_stats(candidates)
    candidate_set = set(candidates)
    scored = [
        (score_word(w, position_freq, presence_freq, position_weight, presence_weight), w)
        for w in pool
    ]
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [(w, s, w in candidate_set) for s, w in scored[:top_n]]
