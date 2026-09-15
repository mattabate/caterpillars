import json
from pathlib import Path

from caterpillars import Caterpillar, WordList, load_words, respace, search
from caterpillars.cli import main


def pair(a, b):
    x, y = sorted((tuple(a.split()), tuple(b.split())))
    return Caterpillar(x, y)


def test_bundled_list_loads():
    words = load_words()
    assert len(words) > 2500
    assert "a" in words and "independent" in words


def test_search_finds_the_example():
    words = WordList(["a", "at", "ten", "end", "ad", "dad"], min_len=1)
    found = search(words, max_words=3)
    assert pair("a ten dad", "at end ad") in found


def test_search_never_shares_an_inner_break():
    for p in search(load_words(), max_words=2):
        assert p.letters == "".join(p.second)
        cuts = [set(), set()]
        for side, ws in zip(cuts, (p.first, p.second)):
            at = 0
            for w in ws[:-1]:
                at += len(w)
                side.add(at)
        assert not cuts[0] & cuts[1], p


def test_search_two_words_bundled():
    found = search(load_words(), max_words=2)
    assert pair("economic selection", "economics election") in found
    assert all(len(p.first) == 2 and len(p.second) == 2 for p in found)


def test_respace():
    found = respace("for ms independent", load_words())
    assert pair("for ms independent", "form sin dependent") in found
    assert all(p.letters == "formsindependent" for p in found)


def test_respace_shared_breaks_flag():
    words = load_words()
    assert pair("for ms independent", "for ms in dependent") not in respace("for ms independent", words)
    assert pair("for ms independent", "for ms in dependent") in respace("for ms independent", words, shared_breaks=True)


def test_scored_list_ranks_by_worst_word(tmp_path: Path):
    src = tmp_path / "list.txt"
    src.write_text("CALCULATE;50\nCALCULATED;50\nDANGER;50\nANGER;50\nSATURATE;10\nSATURATED;50\n")
    found = search(load_words(src))
    assert [str(p) for p in found] == ["calculate danger / calculated anger", "saturate danger / saturated anger"]
    assert len(search(load_words(src, min_score=20))) == 1


def test_json_list(tmp_path: Path):
    src = tmp_path / "w.json"
    src.write_text(json.dumps(["Tea", "team", "mate", "ate"]))
    assert set(load_words(src)) == {"tea", "team", "mate", "ate"}


def test_cli(capsys):
    assert main(["respace", "for", "ms", "independent", "--limit", "0"]) == 0
    assert "for ms independent / form sin dependent" in capsys.readouterr().out
    assert main(["search", "--limit", "3"]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3
