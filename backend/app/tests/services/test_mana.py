from app.services.mana import calculate_cmc


def test_empty_or_none_mana_cost_is_zero():
    assert calculate_cmc("") == 0
    assert calculate_cmc(None) == 0


def test_generic_mana_sums_numbers():
    assert calculate_cmc("{2}") == 2
    assert calculate_cmc("{3}{R}{R}") == 5


def test_colored_pip_contributes_one():
    assert calculate_cmc("{W}") == 1
    assert calculate_cmc("{U}{U}") == 2


def test_hybrid_mana_contributes_one():
    assert calculate_cmc("{G/U}") == 1
    assert calculate_cmc("{2}{G/U}") == 3


def test_phyrexian_mana_contributes_one():
    assert calculate_cmc("{G/P}") == 1
    assert calculate_cmc("{1}{G/P}") == 2


def test_x_symbol_contributes_zero():
    """The fixed bug: {X} must be 0, not 1 like other bracket symbols."""
    assert calculate_cmc("{X}") == 0
    assert calculate_cmc("{X}{R}") == 1
    assert calculate_cmc("{X}{X}{R}{R}") == 2
