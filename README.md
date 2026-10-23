# Wordle Solver

A hard-mode Wordle solving assistant. It narrows the candidate word list as you enter each guess and its result, and suggests the best next guesses using a letter-frequency heuristic. Includes a wager tracker for games played with per-letter betting rules.

## Install

### With uv (recommended)

[uv](https://docs.astral.sh/uv/) installs the `wordle` command globally in an isolated environment — no virtual environment to manage.

```bash
uv tool install .
```

To pick up code changes after editing the source:

```bash
uv tool install --reinstall .
```

Or install it editable (`uv tool install --editable .`) and edits take effect immediately.

### Development

Requires Python 3.9+.

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

This installs the `wordle` command into the virtual environment's `bin/`.

### Options

```
wordle [--top N] [--position-weight F] [--presence-weight F]
```

| Flag | Default | Description |
|---|---|---|
| `--top N` | 10 | Number of suggestions to show after each guess |
| `--position-weight F` | 1.0 | Weight on per-position letter frequency in the heuristic |
| `--presence-weight F` | 1.0 | Weight on overall letter presence frequency in the heuristic |

## Usage

### Assisted mode (playing on an external Wordle board)

After each guess you make on the Wordle site, enter the word and its color result as a single string of letter–digit pairs:

```
> c2r1a0n0e0
```

Each digit encodes the tile color:

| Digit | Meaning |
|---|---|
| `2` | Correct letter, correct spot (green / orange in colorblind mode) |
| `1` | Correct letter, wrong spot (yellow / blue in colorblind mode) |
| `0` | Letter not in the word (grey / black) |

The solver prints how many candidates remain, lists them when 20 or fewer are left, and shows the top-ranked hard-mode-valid suggestions.

### Practice mode

`/practice` picks a secret word and lets you play through a full game. Type your guess as a plain word — no digits needed, the solver scores it for you. Hard mode is enforced: green letters must stay in their position, and all revealed letters must appear in every subsequent guess.

## Commands

| Command | Description |
|---|---|
| `help` | Print the help text |
| `reset` | Clear the solver state for a new puzzle (keeps wager session total) |
| `quit` | Exit |
| `/practice` | Start a practice game: solver picks a secret word, scores your guesses |
| `/round` | Start a new wager round: clears solver state and the round total, exits practice mode |
| `/price` | Reset per-letter wager prices to the defaults ($1 correct / $2 present / $3 absent) |
| `/price <g> <y> <b>` | Set custom per-letter prices, e.g. `/price 2 3 5` |
| `/addword <word>` | Add a missing word to the answers list, removing it from the guesses-only list if it was there |

## Wager tracking

The solver tracks a running dollar cost for each guess based on its tile results. Default prices:

- Correct (green): **$1**
- Present (yellow): **$2**
- Absent (grey): **$3**

After each guess the solver prints the cost of that guess, the round total, and the session total. Use `/price` to match whatever betting rules your game uses.
