"""Tests de extracción de teléfono (RF-1, RF-2)."""

from app.domain.phone import extract_phone


def test_extracts_valid_phone():
    assert extract_phone("Tel: +573001234567") == "+573001234567"


def test_normalizes_spaces_dashes_parentheses():
    assert extract_phone("Tel: +57 300-123-4567") == "+573001234567"
    assert extract_phone("Tel: (+57) 300 123 4567") == "+573001234567"


def test_returns_none_without_tel_line():
    assert extract_phone("Paciente nuevo") is None
    assert extract_phone("") is None


def test_returns_none_without_plus():
    assert extract_phone("Tel: 3001234567") is None


def test_returns_none_with_wrong_digit_count():
    assert extract_phone("Tel: +123") is None
    assert extract_phone("Tel: +1234567890123456") is None
