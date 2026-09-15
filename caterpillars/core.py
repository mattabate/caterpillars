"""Find letter strings that read as two different phrases.

A caterpillar is a run of letters that splits into words two different ways:

    a ten dad
    at end ad

Both lines spell ``atendad``. The two spacings never break at the same place
(apart from the ends), so neither pair is two smaller pairs glued together.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterable, Iterator, Mapping

__all__ = ["Caterpillar", "WordList", "load_words", "search", "respace"]


@dataclass(frozen=True, order=True)
class Caterpillar:
    """Two spacings of the same letters, stored in a stable (sorted) order."""

    first: tuple[str, ...]
    second: tuple[str, ...]

    @property
    def letters(self) -> str:
        return "".join(self.first)

    @property
    def words(self) -> tuple[str, ...]:
        return self.first + self.second

    def __str__(self) -> str:
        return f"{' '.join(self.first)} / {' '.join(self.second)}"


def _pair(a: Iterable[str], b: Iterable[str]) -> Caterpillar:
    x, y = sorted((tuple(a), tuple(b)))
    return Caterpillar(x, y)


class WordList:
    """A set of lowercase words with optional scores (higher is better)."""

    def __init__(self, words: Iterable[str] | Mapping[str, int], min_len: int = 2, max_len: int | None = None):
        scored = words if isinstance(words, Mapping) else {w: 0 for w in words}
        self.scores: dict[str, int] = {}
        for word, score in scored.items():
            w = word.strip().lower()
            if not w.isalpha() or w in self.scores:
                continue
            if len(w) < min_len and w not in ("a", "i"):
                continue
            if max_len is not None and len(w) > max_len:
                continue
            self.scores[w] = score
        self._by_prefix: dict[str, list[str]] = defaultdict(list)
        for w in self.scores:
            for k in range(1, len(w) + 1):
                self._by_prefix[w[:k]].append(w)

    def __contains__(self, word: str) -> bool:
        return word in self.scores

    def __len__(self) -> int:
        return len(self.scores)

    def __iter__(self) -> Iterator[str]:
        return iter(self.scores)

    def starting_with(self, prefix: str) -> list[str]:
        return self._by_prefix.get(prefix, [])

    def rank(self, pair: Caterpillar) -> tuple:
        """Sort key: fewest words, best worst score, longest shortest word, longest."""
        ws = pair.words
        return (len(ws), -min(self.scores[w] for w in ws), -min(len(w) for w in ws), -len(pair.letters), pair)


def load_words(
    path: str | Path | None = None,
    *,
    min_len: int = 2,
    max_len: int | None = None,
    min_score: int = 0,
) -> WordList:
    """Load a word list.

    ``path`` may be a JSON list of words, a text file with one word per line, or
    ``WORD;score`` lines (a crossword-style scored list). With no path, the
    bundled list of about 3,000 common English words is used.
    """
    if path is None:
        text = resources.files("caterpillars").joinpath("words.json").read_text()
        return WordList(json.loads(text), min_len=min_len, max_len=max_len)
    path = Path(path)
    if path.suffix == ".json":
        return WordList(json.loads(path.read_text()), min_len=min_len, max_len=max_len)
    scored: dict[str, int] = {}
    for line in path.read_text().splitlines():
        word, _, score = line.strip().partition(";")
        value = int(score) if score.strip() else 0
        if word and value >= min_score:
            scored.setdefault(word.lower(), value)
    return WordList(scored, min_len=min_len, max_len=max_len)


def search(words: WordList, *, max_words: int = 2, min_words: int = 2) -> list[Caterpillar]:
    """Every caterpillar with ``min_words``..``max_words`` words on each side, best first.

    Two cursors walk one letter stream. Start from a word and a proper prefix of
    it; the side that is behind adds a word that ends inside the overhang, runs
    past it (the sides swap), or ends exactly with it (a find).
    """
    found: set[Caterpillar] = set()

    def extend(ahead: list[str], behind: list[str], over: str) -> None:
        # `ahead` has spelled `over` more letters than `behind`
        if len(behind) >= max_words:
            return
        if over in words and len(ahead) >= min_words and len(behind) + 1 >= min_words:
            found.add(_pair(ahead, behind + [over]))
        for k in range(1, len(over)):
            if over[:k] in words:
                extend(ahead, behind + [over[:k]], over[k:])
        for w in words.starting_with(over):
            if w != over:
                extend(behind + [w], ahead, w[len(over):])

    for w in words:
        for k in range(1, len(w)):
            if w[:k] in words:
                extend([w], [w[:k]], w[k:])
    return sorted(found, key=words.rank)


def respace(phrase: str, words: WordList, *, max_words: int = 4, shared_breaks: bool = False) -> list[Caterpillar]:
    """Other ways to space the letters of ``phrase``, best first.

    By default a respacing may not break where ``phrase`` breaks, which is what
    makes "for ms independent / form sin dependent" a caterpillar and
    "for ms in dependent" just a second reading.
    """
    original = tuple(phrase.lower().split())
    letters = "".join(original)
    breaks, at = set(), 0
    for w in original[:-1]:
        at += len(w)
        breaks.add(at)

    out: list[Caterpillar] = []

    def walk(start: int, taken: list[str]) -> None:
        if start == len(letters):
            if tuple(taken) != original:
                out.append(_pair(original, taken))
            return
        if len(taken) >= max_words:
            return
        for end in range(start + 1, len(letters) + 1):
            if end < len(letters) and end in breaks and not shared_breaks:
                continue
            if letters[start:end] in words:
                walk(end, taken + [letters[start:end]])

    walk(0, [])
    unknown = [w for w in original if w not in words]
    if unknown:  # rank on the respacing alone when the phrase uses words off the list
        return sorted(out, key=lambda p: (len(p.words), p))
    return sorted(out, key=words.rank)
