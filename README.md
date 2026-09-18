# Caterpillars

A caterpillar is two line poem where the second line comes from moving the spaces in the first.

```
at end ad
a ten dad
```

```
for ms independent
form sin dependent
```

```
there also no fun
the real son of un
```

This code helps you make your own. It searches a word list for letters that can be spaced two ways, and the two spacings never break in the same place, so a caterpillar can't be cut into two smaller ones. It started in 2024 as Puzzle Poetry II in [mattabate/wordplay](https://github.com/mattabate/wordplay), a search for two grammatical sentences made of the same letters. A few favourites are on [mattabate.com/projects](https://mattabate.com/projects).

## Install

Python 3.10 or newer, no dependencies:

```bash
pip install git+https://github.com/mattabate/caterpillars
```

## Usage

Other ways to space a phrase:

```console
$ caterpillars respace a ten dad
a ten dad / at end ad
$ caterpillars respace for ms independent
for ms independent / form sin dependent
```

Every two-word caterpillar in the bundled list of about 3,000 common words, best first:

```console
$ caterpillars search --limit 5
economic selection / economics election
consume revolution / consumer evolution
observe revolution / observer evolution
strength encounter / strengthen counter
strength encourage / strengthen courage
```

Options (`caterpillars search --help` and `caterpillars respace --help` list them all):

| Option | Meaning |
|---|---|
| `--words FILE` | your own word list: a JSON list, one word per line, or `WORD;score` lines |
| `--min-score N` | with a scored list, skip words scored below `N` |
| `--min-len N` / `--max-len N` | word length limits (`a` and `i` always pass) |
| `--max-words N` | most words on a side (search: 2, respace: 4) |
| `--limit N` | how many to print, `0` for all |
| `--reuse N` | search only: print each word at most `N` times, so one hinge doesn't fill the page |
| `--shared-breaks` | respace only: also list spacings that break where the phrase does |

To use [my wordlist](https://github.com/mattabate/wordlist), download [`matts_wordlist.txt`](https://raw.githubusercontent.com/mattabate/wordlist/refs/heads/main/quickstart/matts_wordlist.txt) and pass `--words matts_wordlist.txt --min-score 40`. It's a crossword list, so it has no words shorter than three letters. Poems that need `a`, `at` or `un` come from the bundled list.

With `--max-words 3` the number of results grows quickly (about 50,000 from the bundled list), and a list of hundreds of thousands of words can take a very long time. Trim a big list with `--min-score` or `--max-len` first.

From Python:

```python
from caterpillars import load_words, respace, search

words = load_words()                     # or load_words("my_list.txt", min_score=40)
print(respace("for ms independent", words)[0])
# for ms independent / form sin dependent
print(len(search(words, max_words=2)))   # all two-word pairs, best first
```

## How it works

`search` walks two cursors along one stream of letters. It starts from a word and a shorter word that begins it (`strengthen` / `strength`). The side that is behind then adds a word. That word either ends inside the letters the other side has already spelled, runs past them (and the two sides swap roles), or ends exactly where the other side ends, which is a match. Because the side that is behind always has letters left to cover before the end, the two phrases never break in the same place.

Results are sorted by:
1. fewest words,
2. highest score of the lowest-scored word (scored lists only),
3. longest shortest word (so filler like `a` and `an` sinks),
4. longest total length.

`respace` tries every way of splitting the phrase's letters into listed words, and skips the phrase's own break points unless `--shared-breaks` is set.

The original 2024 study script is kept in [`2024/`](2024/).

## Development

```bash
pip install -e . pytest
pytest
```

## License

MIT.
