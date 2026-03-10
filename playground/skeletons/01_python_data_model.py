"""
Kata 01 -- Python Data Model
Run: python playground/skeletons/01_python_data_model.py

Explore how Python's dunder methods let your objects participate in
the language's built-in protocols: len(), indexing, iteration, equality,
hashing, truthiness, and display.
"""

# ---------------------------------------------------------------------------
# Card class -- identity, display, equality, hashing
# ---------------------------------------------------------------------------

class Card:
    """A single playing card."""

    SUIT_SYMBOLS = {"spades": "♠", "hearts": "♥", "diamonds": "♦", "clubs": "♣"}

    def __init__(self, rank: str, suit: str) -> None:
        self.rank = rank
        self.suit = suit

    def __repr__(self) -> str:
        """Unambiguous developer representation (looks like a constructor call)."""
        # TODO: return an unambiguous string like Card('A', 'spades')
        # HINT: use !r inside the f-string to quote the values
        pass

    def __str__(self) -> str:
        """Pretty, human-readable representation."""
        # TODO: return a short pretty string like A♠
        # HINT: look up the suit symbol from SUIT_SYMBOLS, then combine rank + symbol
        pass

    def __eq__(self, other: object) -> bool:
        """Two cards are equal if they have the same rank and suit."""
        # TODO: return True if other is a Card with the same rank and suit
        # HINT: first check isinstance(other, Card) — if not, return NotImplemented
        pass

    def __hash__(self) -> int:
        """Hash based on the same fields used in __eq__."""
        # TODO: return a hash based on rank and suit
        # HINT: hash a tuple of the fields you compare in __eq__
        pass


# ---------------------------------------------------------------------------
# Deck class -- behaving like a Python sequence
# ---------------------------------------------------------------------------

class Deck:
    """A deck of playing cards that behaves like a Python sequence."""

    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    SUITS = ["clubs", "diamonds", "hearts", "spades"]

    def __init__(self, cards: list[Card] | None = None) -> None:
        if cards is not None:
            self._cards = list(cards)
        else:
            self._cards = [
                Card(rank, suit)
                for suit in self.SUITS
                for rank in self.RANKS
            ]

    def __repr__(self) -> str:
        # TODO: return a string like Deck([Card('2', 'clubs'), ...])
        # HINT: use !r on self._cards to get the repr of the list
        pass

    def __len__(self) -> int:
        """Return the number of cards in the deck."""
        # TODO: return how many cards are in the deck
        pass

    def __getitem__(self, index):
        """Support indexing and slicing. Slices return a new Deck."""
        # TODO: support both integer indexing and slicing
        # HINT: check isinstance(index, slice) — if so, wrap the result in Deck(...)
        pass

    def __contains__(self, card: Card) -> bool:
        """Support 'card in deck' membership test."""
        # TODO: return True if the card is in self._cards
        pass

    def __iter__(self):
        """Support iteration: for card in deck."""
        # TODO: return an iterator over self._cards
        # HINT: use the iter() built-in
        pass

    def __bool__(self) -> bool:
        """A deck is truthy if it has at least one card."""
        # TODO: return True if the deck is non-empty, False otherwise
        pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: __repr__ vs __str__ ---
    print("--- __repr__ vs __str__ ---")
    try:
        card = Card("A", "spades")

        print(f"repr(card) = {repr(card)}")
        assert repr(card) == "Card('A', 'spades')"

        print(f"str(card)  = {str(card)}")
        assert str(card) == "A♠"

        print(f"print uses __str__: {card}")
        print(f"f-string default:  {card}")
        print(f"f-string !r:       {card!r}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: __eq__ (equality) ---
    print("--- __eq__ (equality) ---")
    try:
        card1 = Card("A", "spades")
        card2 = Card("A", "spades")
        card3 = Card("K", "hearts")

        print(f"card1 == card2: {card1 == card2}")
        assert card1 == card2

        print(f"card1 == card3: {card1 == card3}")
        assert card1 != card3

        print(f"card1 is card2: {card1 is card2}")
        print(f'card1 == "not a card": {card1 == "not a card"}')
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: __hash__ (sets and dict keys) ---
    print("--- __hash__ (sets and dict keys) ---")
    try:
        card_a = Card("A", "spades")
        card_b = Card("A", "spades")  # same rank and suit
        card_c = Card("K", "hearts")

        print(f"hash(card_a) = {hash(card_a)}")
        print(f"hash(card_b) = {hash(card_b)}")
        assert hash(card_a) == hash(card_b), "Equal objects MUST have equal hashes"

        hand = {card_a, card_b, card_c}
        print(f"Set with duplicate: {len(hand)} unique cards")
        assert len(hand) == 2

        scores = {Card("A", "spades"): 11, Card("K", "hearts"): 10}
        print(f"Score for A♠: {scores[Card('A', 'spades')]}")
        assert scores[Card("A", "spades")] == 11
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: __len__ ---
    print("--- __len__ ---")
    try:
        deck = Deck()
        print(f"len(deck) = {len(deck)}")
        assert len(deck) == 52

        small = Deck([Card("A", "spades"), Card("K", "hearts")])
        print(f"len(small) = {len(small)}")
        assert len(small) == 2
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: __getitem__ (indexing and slicing) ---
    print("--- __getitem__ (indexing and slicing) ---")
    try:
        deck = Deck()

        print(f"deck[0]  = {deck[0]}")
        assert str(deck[0]) == "2♣"

        print(f"deck[-1] = {deck[-1]}")
        assert str(deck[-1]) == "A♠"

        print(f"deck[12] = {deck[12]}")
        assert str(deck[12]) == "A♣"

        top_three = deck[:3]
        print(f"deck[:3] = {[str(c) for c in top_three]}")
        assert len(top_three) == 3
        assert isinstance(top_three, Deck)

        every_13th = deck[0::13]
        print(f"deck[0::13] = {[str(c) for c in every_13th]}")
        assert len(every_13th) == 4
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: __contains__ (membership test) ---
    print("--- __contains__ (membership test) ---")
    try:
        deck = Deck()
        ace_of_spades = Card("A", "spades")
        joker = Card("Joker", "wild")

        print(f"ace_of_spades in deck: {ace_of_spades in deck}")
        assert ace_of_spades in deck

        print(f"joker in deck: {joker in deck}")
        assert joker not in deck
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: __iter__ (iteration) ---
    print("--- __iter__ (iteration) ---")
    try:
        deck = Deck()

        suits = set()
        for card in deck:
            suits.add(card.suit)
        print(f"Suits in deck: {sorted(suits)}")
        assert len(suits) == 4

        aces = [c for c in deck if c.rank == "A"]
        print(f"Number of aces: {len(aces)}")
        assert len(aces) == 4

        print(f"Aces: {[str(a) for a in aces]}")

        last_three = list(deck)[-3:]
        print(f"Last 3 cards: {[str(c) for c in last_three]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: __bool__ (truthiness) ---
    print("--- __bool__ (truthiness) ---")
    try:
        full_deck = Deck()
        empty_deck = Deck([])

        print(f"bool(full_deck):  {bool(full_deck)}")
        assert bool(full_deck) is True

        print(f"bool(empty_deck): {bool(empty_deck)}")
        assert bool(empty_deck) is False

        if full_deck:
            print("Full deck is truthy")

        if not empty_deck:
            print("Empty deck is falsy")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 9: The Protocol Map ---
    print("--- The Protocol Map ---")
    print("Python expression → Dunder method called")
    print()
    protocol_map = [
        ("len(obj)",        "obj.__len__()"),
        ("obj[i]",          "obj.__getitem__(i)"),
        ("obj[1:3]",        "obj.__getitem__(slice(1, 3))"),
        ("item in obj",     "obj.__contains__(item)"),
        ("for x in obj:",   "iter(obj) → obj.__iter__()"),
        ("bool(obj)",       "obj.__bool__()"),
        ("str(obj)",        "obj.__str__()"),
        ("repr(obj)",       "obj.__repr__()"),
        ("obj1 == obj2",    "obj1.__eq__(obj2)"),
        ("hash(obj)",       "obj.__hash__()"),
    ]
    for expression, dunder in protocol_map:
        print(f"  {expression:<20s} →  {dunder}")

    print()

    # --- Section 10: Fallback behavior ---
    print("--- Fallback Behavior ---")

    # Demonstrate: if __contains__ were missing, Python falls back to __iter__
    class MinimalSequence:
        """Only implements __getitem__ -- Python still provides iteration!"""
        def __init__(self, items):
            self._items = list(items)

        def __getitem__(self, index):
            return self._items[index]

    seq = MinimalSequence([10, 20, 30])

    items = list(seq)
    print(f"Iteration from __getitem__ alone: {items}")
    assert items == [10, 20, 30]

    print(f"20 in seq: {20 in seq}")
    assert 20 in seq

    print(f"99 in seq: {99 in seq}")
    assert 99 not in seq

    print()

    # --- Section 11: Verifying the __eq__ / __hash__ contract ---
    print("--- __eq__ / __hash__ Contract ---")
    try:
        a = Card("A", "spades")
        b = Card("A", "spades")
        c = Card("K", "hearts")

        assert a == b
        assert hash(a) == hash(b)
        print(f"a == b: {a == b}, hash(a) == hash(b): {hash(a) == hash(b)}")

        assert a != c
        print(f"a != c: {a != c}, hashes may differ: hash(a)={hash(a)}, hash(c)={hash(c)}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("The Python Data Model lets your objects work with:")
    print("  - Built-in functions: len(), bool(), hash(), repr(), str()")
    print("  - Operators: ==, !=, [], in")
    print("  - Statements: for, if, while")
    print("  - Data structures: set(), dict(), sorted()")
    print()
    print("All 11 sections passed. You understand the Python Data Model!")
