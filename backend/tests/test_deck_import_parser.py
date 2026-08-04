from app.services.deck_import import parse_decklist


def test_simple_list_no_headers_defaults_to_main():
    text = "4 Blanchwood Prowler\n3 Swamp"
    deck = parse_decklist(text)

    assert deck.name is None
    assert [(e.name, e.quantity, e.board) for e in deck.entries] == [
        ("Blanchwood Prowler", 4, "main"),
        ("Swamp", 3, "main"),
    ]


def test_mtga_export_with_set_and_collector_number():
    text = (
        "Deck\n"
        "4 Blanchwood Prowler (BRO) 172\n"
        "3 Swamp (ONE) 211\n"
        "\n"
        "Sideboard\n"
        "2 Gnaw to the Bone (ISD) 183\n"
    )
    deck = parse_decklist(text)

    prowler, swamp, gnaw = deck.entries
    assert (prowler.name, prowler.set_code, prowler.collector_number, prowler.board) == (
        "Blanchwood Prowler",
        "BRO",
        "172",
        "main",
    )
    assert (swamp.set_code, swamp.collector_number) == ("ONE", "211")
    assert (gnaw.board, gnaw.set_code, gnaw.collector_number) == ("side", "ISD", "183")


def test_about_name_header_sets_deck_name():
    text = "About\nName Dredge\n\nDeck\n4 Blanchwood Prowler\n"
    deck = parse_decklist(text)

    assert deck.name == "Dredge"
    assert deck.entries[0].board == "main"


def test_commander_zone():
    text = "Commander\n1 Atraxa, Praetors' Voice\n\nDeck\n1 Sol Ring\n"
    deck = parse_decklist(text)

    commander, sol_ring = deck.entries
    assert commander.board == "commander"
    assert sol_ring.board == "main"


def test_blank_lines_and_unrecognized_lines_are_skipped():
    text = "Deck\n\n4 Forest\n\n// this is a comment, not a card\nnot a valid line at all\n"
    deck = parse_decklist(text)

    assert len(deck.entries) == 1
    assert deck.entries[0].name == "Forest"


def test_raw_line_preserved_for_error_reporting():
    text = "3 Totally Fake Card That Does Not Exist"
    deck = parse_decklist(text)

    assert deck.entries[0].raw_line == "3 Totally Fake Card That Does Not Exist"
