"""Tests for the model catalog and model-string parsing."""

import pytest

from xdr_modbus import XdrModelError, models, parse_model


def test_catalog_covers_the_series() -> None:
    """Every documented variant exists; the XDR-960 has no 12 V model."""
    catalog = models()
    assert len(catalog) == 19
    assert "XDR-75-12" in catalog
    assert "XDR-120-48" in catalog
    assert "XDR-240-24" in catalog
    assert "XDR-480-24" in catalog
    assert "XDR-960-48" in catalog
    assert "XDR-960-12" not in catalog


def test_modbus_only_on_larger_families() -> None:
    """The 75/120 W families have no Modbus communication."""
    catalog = models()
    assert catalog["XDR-75-24"].has_modbus is False
    assert catalog["XDR-120-24"].has_modbus is False
    assert catalog["XDR-240-24"].has_modbus is True
    assert catalog["XDR-480-24"].has_modbus is True
    assert catalog["XDR-960-24"].has_modbus is True


def test_xdr_480_12_is_a_360w_variant() -> None:
    """The XDR-480-12 deviates from the family power rating."""
    definition = models()["XDR-480-12"]
    assert definition.rated_current == 30.0
    assert definition.rated_power == 360.0
    assert definition.iout_set_range == (6.0, 37.5)


def test_parse_model_variants() -> None:
    """Device-reported strings parse, padding and case tolerated."""
    assert parse_model("XDR-480-24").name == "XDR-480-24"
    assert parse_model("XDR-240-24  ").name == "XDR-240-24"
    assert parse_model("xdr-960-48").name == "XDR-960-48"


def test_parse_model_rejects_garbage() -> None:
    """Unknown strings raise instead of guessing."""
    with pytest.raises(XdrModelError):
        parse_model("DRP-480-24")
    with pytest.raises(XdrModelError):
        parse_model("XDR-360-24")
