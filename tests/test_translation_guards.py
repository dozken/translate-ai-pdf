"""
Regression tests for translation output guards: finish_reason validation,
output normalization, and recitation/truncation '....' detection.

These cover the fixes for the bug where translations of religious/classical
texts intermittently gained '....' runs and spurious paragraph breaks.
"""

import pytest

from utils.translator import (
    IncompleteTranslationError,
    _check_finish_reason,
    _normalize_translation,
)


class _Candidate:
    def __init__(self, finish_reason):
        self.finish_reason = finish_reason


class _Response:
    def __init__(self, finish_reason):
        self.candidates = [_Candidate(finish_reason)]


def test_normalize_strips_prompt_echo():
    assert _normalize_translation("Russian translation: привет", "Russian") == "привет"
    assert _normalize_translation("Translation: hello", "Russian") == "hello"


def test_normalize_collapses_internal_newlines():
    # One source paragraph must stay one output paragraph (no spurious breaks).
    assert _normalize_translation("line1\n\nline2", "Russian") == "line1 line2"
    assert _normalize_translation("a\nb\nc", "Russian") == "a b c"


def test_normalize_rejects_four_dot_run():
    with pytest.raises(IncompleteTranslationError):
        _normalize_translation("текст....", "Russian")
    with pytest.raises(IncompleteTranslationError):
        _normalize_translation("часть .... ещё", "Russian")


def test_normalize_allows_normal_ellipsis():
    # A legitimate 3-dot ellipsis must pass untouched.
    assert _normalize_translation("текст... конец", "Russian") == "текст... конец"


def test_finish_reason_stop_ok():
    _check_finish_reason(_Response(1))  # STOP — no raise


@pytest.mark.parametrize("code", [2, 3, 4, 5])  # MAX_TOKENS, SAFETY, RECITATION, OTHER
def test_finish_reason_non_stop_raises(code):
    with pytest.raises(IncompleteTranslationError):
        _check_finish_reason(_Response(code))


def test_finish_reason_missing_metadata_tolerated():
    _check_finish_reason(_Response(None))  # no usable reason — no raise

    class _Empty:
        candidates = []

    _check_finish_reason(_Empty())  # no candidates — no raise
