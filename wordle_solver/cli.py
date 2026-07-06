"""Interactive REPL: enter each guess and its result, get ranked suggestions back."""

import argparse
import random
from collections import Counter

from .game import Clue, score_guess, str_to_pattern
from .solver import MAX_GUESSES, WORD_LEN, Solver, rank_guesses
from .wager import Wager
from .words import load_answers, load_extra_guesses

HELP_TEXT = """\
Enter each letter followed by its result digit, e.g.:
    c2r1a0n0e0
Digits mean correct/present/absent, not literal color:
    2 = right letter, right spot   (orange in colorblind mode)
    1 = right letter, wrong spot   (blue in colorblind mode)
    0 = letter not in word         (black in colorblind mode)

In `/practice` mode, just type the guessed word — no digits needed,
the tool knows the secret and scores it for you.

Commands:
    help                     show this text
    reset                    clear the solver (new puzzle, keeps wager totals)
    quit                     exit
    /practice                pick a secret word and let you guess it (hard-mode enforced)
    /round                   start a new wager round: clears solver + round total, exits practice
    /price                   reset per-letter $ values to the default $1/$2/$3
    /price <g> <y> <b>       set per-letter $ values, e.g. `/price 1 2 3`
"""


def parse_line(line: str):
    line = line.replace(" ", "")
    if len(line) != 2 * WORD_LEN:
        raise ValueError(f"expected {WORD_LEN} letter+digit pairs, e.g. `c2r1a0n0e0`")
    guess = line[0::2].lower()
    result = line[1::2]
    if not guess.isalpha():
        raise ValueError(f"expected {WORD_LEN} letter+digit pairs, e.g. `c2r1a0n0e0`")
    return guess, str_to_pattern(result)


def hard_mode_violation(guess: str, green: dict, min_count: Counter):
    """Return a human-readable reason `guess` breaks hard mode, or None if it's legal."""
    for i, ch in green.items():
        if guess[i] != ch:
            return f"position {i + 1} must be '{ch.upper()}'"
    counts = Counter(guess)
    for ch, need in min_count.items():
        if counts[ch] < need:
            return f"must include letter '{ch.upper()}' (need at least {need})"
    return None


def format_result(guess: str, pattern) -> str:
    labels = {Clue.GREEN: "correct", Clue.YELLOW: "present", Clue.GREY: "absent"}
    return "  ".join(f"{ch.upper()}:{labels[clue]}" for ch, clue in zip(guess, pattern))


def handle_slash_command(line: str, solver: Solver, wager: Wager, state: dict, answers: list, opts) -> None:
    parts = line.split()
    cmd = parts[0].lower()

    if cmd == "/practice":
        solver.reset()
        wager.new_round()
        state["secret"] = random.choice(answers)
        state["guesses_made"] = 0
        print(f"Practice round started — I picked a secret word. You have {MAX_GUESSES} guesses.")
        print(f"Just type the {WORD_LEN}-letter word you're guessing (hard mode enforced).")
        print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)
        return

    if cmd == "/round":
        solver.reset()
        wager.new_round()
        state["secret"] = None
        state["guesses_made"] = 0
        print(f"New round. Prices: {wager.prices_str()}  |  session total: ${wager.session_total}")
        print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)
        return

    if cmd == "/price":
        args = parts[1:]
        if not args:
            wager.set_prices(1, 2, 3)
            print(f"Prices reset to default. {wager.prices_str()}")
        elif len(args) == 3 and all(a.lstrip("-").isdigit() for a in args):
            wager.set_prices(*(int(a) for a in args))
            print(f"Prices updated. {wager.prices_str()}")
        else:
            print("Usage: `/price` (reset to $1/$2/$3) or `/price <correct> <present> <absent>`")
            return
        print(f"Round total so far: ${wager.round_total}  |  session total: ${wager.session_total}")
        return

    print(f"Unknown command: {cmd}  (try 'help')")


def print_suggestions(solver: Solver, top_n: int, position_weight: float, presence_weight: float):
    n_remaining = len(solver.candidates)
    print(f"\n{n_remaining} possible answer(s) remain.")
    if n_remaining <= 20:
        print("  " + ", ".join(sorted(solver.candidates)))

    pool = solver.hard_mode_pool()
    suggestions = rank_guesses(pool, solver.candidates, top_n=top_n,
                                position_weight=position_weight, presence_weight=presence_weight)
    if not suggestions:
        print("No hard-mode-legal words left in the word list (check your entered results).")
        return

    print(f"\nTop {len(suggestions)} suggestion(s) (hard-mode legal):")
    for rank, (word, score, is_answer) in enumerate(suggestions, start=1):
        tag = "possible answer" if is_answer else "scout"
        print(f"  {rank:>2}. {word:<6} (heuristic {score:.3f}, {tag})")


def run(args=None):
    parser = argparse.ArgumentParser(description="Hard-mode Wordle solving assistant.")
    parser.add_argument("--top", type=int, default=10, help="number of suggestions to show (default: 10)")
    parser.add_argument("--position-weight", type=float, default=1.0,
                         help="weight on per-position letter frequency (default: 1.0)")
    parser.add_argument("--presence-weight", type=float, default=1.0,
                         help="weight on overall letter presence frequency (default: 1.0)")
    opts = parser.parse_args(args)

    answers = load_answers()
    extra_guesses = load_extra_guesses()
    solver = Solver(answers, extra_guesses)
    wager = Wager()
    state = {"secret": None, "guesses_made": 0}

    print("Wordle hard-mode assistant. Type 'help' for instructions.")
    print(f"Wager prices: {wager.prices_str()}")
    print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            break
        if line.lower() == "help":
            print(HELP_TEXT)
            continue
        if line.lower() == "reset":
            solver.reset()
            state["secret"] = None
            state["guesses_made"] = 0
            print("Reset.")
            print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)
            continue
        if line.startswith("/"):
            handle_slash_command(line, solver, wager, state, answers, opts)
            continue

        if state["secret"] is not None:
            guess = line.lower()
            if len(guess) != WORD_LEN or not guess.isalpha():
                print(f"Guess must be a {WORD_LEN}-letter word.")
                continue
            if guess not in solver.all_words:
                print("Not in word list.")
                continue
            green, min_count = solver.hard_mode_constraints()
            violation = hard_mode_violation(guess, green, min_count)
            if violation:
                print(f"Hard mode violation: {violation}")
                continue

            pattern = score_guess(guess, state["secret"])
            solver.apply(guess, pattern)
            state["guesses_made"] += 1
            cost = wager.add(pattern)
            print(format_result(guess, pattern))
            print(f"Cost: ${cost}  |  round total: ${wager.round_total}  |  session total: ${wager.session_total}")

            if pattern == (Clue.GREEN,) * WORD_LEN:
                print(f"Solved in {state['guesses_made']} guess(es)! The word was {guess.upper()} \U0001F389")
                print("'/practice' for another word, '/round' to switch back to manual mode.")
                state["secret"] = None
                continue
            if state["guesses_made"] >= MAX_GUESSES:
                print(f"Out of guesses. The word was {state['secret'].upper()}.")
                state["secret"] = None
                continue

            print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)
            continue

        try:
            guess, pattern = parse_line(line)
        except ValueError as e:
            print(f"Couldn't parse that: {e}")
            continue

        solver.apply(guess, pattern)
        cost = wager.add(pattern)
        print(f"Cost: ${cost}  |  round total: ${wager.round_total}  |  session total: ${wager.session_total}")

        if pattern == (Clue.GREEN,) * WORD_LEN:
            print(f"Solved: {guess.upper()} \U0001F389  ('/round' to start a new round)")
            continue

        if not solver.candidates:
            print("No remaining candidates match all the results entered so far — "
                  "double check the guess/result pairs, or 'reset' to start over.")
            continue

        print_suggestions(solver, opts.top, opts.position_weight, opts.presence_weight)


if __name__ == "__main__":
    run()
