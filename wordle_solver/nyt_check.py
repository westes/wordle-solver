"""Silent, once-a-day check of the NYT Wordle answer against our word list.

NYT's `svc/wordle/v2` endpoint discloses the solution for a given date as
soon as the local calendar rolls to that date. On startup we check today's
date once per day and add the word via the same mechanism as `/addword` if
it's missing from `answers.txt`. Never prints anything and never raises —
failures are silently ignored and retried on the next run.
"""

import json
import urllib.request
from datetime import date
from pathlib import Path

from .game import score_guess
from .solver import WORD_LEN, Solver
from .words import DATA_DIR, add_answer_word

STATE_PATH = Path.home() / ".wordle_solver" / "state.json"
NYT_URL_TEMPLATE = "https://www.nytimes.com/svc/wordle/v2/{date}.json"
REQUEST_TIMEOUT = 3


def get_state_path() -> Path:
    return STATE_PATH


def load_state(state_path: Path = STATE_PATH) -> dict:
    try:
        return json.loads(state_path.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state: dict, state_path: Path = STATE_PATH) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state))


def fetch_todays_answer() -> str | None:
    url = NYT_URL_TEMPLATE.format(date=date.today().isoformat())
    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as resp:
            body = json.loads(resp.read())
        word = body["solution"].strip().lower()
    except Exception:
        return None
    if len(word) != WORD_LEN or not word.isalpha():
        return None
    return word


def maybe_check_nyt_word(solver: Solver, data_dir: Path = DATA_DIR,
                          state_path: Path = STATE_PATH,
                          skip: bool = False, force: bool = False) -> str | None:
    if skip:
        return None

    today = date.today().isoformat()
    state = load_state(state_path)
    if not force and state.get("last_checked") == today:
        return None

    word = fetch_todays_answer()
    if word is None:
        return None

    state["last_checked"] = today
    save_state(state, state_path)

    if word in solver.answers:
        return None

    result = add_answer_word(word, data_dir)
    solver.answers.append(word)
    solver.answers.sort()
    if result["removed_from_guesses"]:
        solver.extra_guesses.remove(word)

    if all(score_guess(rec.guess, word) == rec.pattern for rec in solver.history):
        solver.candidates.append(word)

    return word
