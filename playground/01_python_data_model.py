"""
Kata 01 -- Python Data Model
Run: python playground/01_python_data_model.py

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
        return f"Card({self.rank!r}, {self.suit!r})"

    def __str__(self) -> str:
        """Pretty, human-readable representation."""
        symbol = self.SUIT_SYMBOLS.get(self.suit, self.suit)
        return f"{self.rank}{symbol}"

    def __eq__(self, other: object) -> bool:
        """Two cards are equal if they have the same rank and suit."""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        """Hash based on the same fields used in __eq__."""
        return hash((self.rank, self.suit))


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
        return f"Deck({self._cards!r})"

    def __len__(self) -> int:
        """Return the number of cards in the deck."""
        return len(self._cards)

    def __getitem__(self, index):
        """Support indexing and slicing. Slices return a new Deck."""
        if isinstance(index, slice):
            return Deck(self._cards[index])
        return self._cards[index]

    def __contains__(self, card: Card) -> bool:
        """Support 'card in deck' membership test."""
        return card in self._cards

    def __iter__(self):
        """Support iteration: for card in deck."""
        return iter(self._cards)

    def __bool__(self) -> bool:
        """A deck is truthy if it has at least one card."""
        return len(self._cards) > 0


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: __repr__ vs __str__ ---
    print("--- __repr__ vs __str__ ---")

    card = Card("A", "spades")

    print(f"repr(card) = {repr(card)}")
    # Output: repr(card) = Card('A', 'spades')
    assert repr(card) == "Card('A', 'spades')"

    print(f"str(card)  = {str(card)}")
    # Output: str(card)  = A♠
    assert str(card) == "A♠"

    print(f"print uses __str__: {card}")
    # Output: print uses __str__: A♠

    # In f-strings, !r forces __repr__, !s forces __str__
    print(f"f-string default:  {card}")
    # Output: f-string default:  A♠
    print(f"f-string !r:       {card!r}")
    # Output: f-string !r:       Card('A', 'spades')

    print()

    # --- Section 2: __eq__ (equality) ---
    print("--- __eq__ (equality) ---")

    card1 = Card("A", "spades")
    card2 = Card("A", "spades")
    card3 = Card("K", "hearts")

    print(f"card1 == card2: {card1 == card2}")
    # Output: card1 == card2: True
    assert card1 == card2

    print(f"card1 == card3: {card1 == card3}")
    # Output: card1 == card3: False
    assert card1 != card3

    print(f"card1 is card2: {card1 is card2}")
    # Output: card1 is card2: False
    # Note: == checks equality (__eq__), 'is' checks identity (same object in memory)

    # Comparing with a non-Card returns NotImplemented, which Python handles gracefully
    print(f'card1 == "not a card": {card1 == "not a card"}')
    # Output: card1 == "not a card": False

    print()

    # --- Section 3: __hash__ (sets and dict keys) ---
    print("--- __hash__ (sets and dict keys) ---")

    card_a = Card("A", "spades")
    card_b = Card("A", "spades")  # same rank and suit
    card_c = Card("K", "hearts")

    print(f"hash(card_a) = {hash(card_a)}")
    # Output: hash(card_a) = <some integer>
    print(f"hash(card_b) = {hash(card_b)}")
    # Output: hash(card_b) = <same integer as card_a>
    assert hash(card_a) == hash(card_b), "Equal objects MUST have equal hashes"

    # Sets deduplicate using __hash__ + __eq__
    hand = {card_a, card_b, card_c}
    print(f"Set with duplicate: {len(hand)} unique cards")
    # Output: Set with duplicate: 2 unique cards
    assert len(hand) == 2

    # Cards work as dict keys
    scores = {Card("A", "spades"): 11, Card("K", "hearts"): 10}
    print(f"Score for A♠: {scores[Card('A', 'spades')]}")
    # Output: Score for A♠: 11
    assert scores[Card("A", "spades")] == 11

    print()

    # --- Section 4: __len__ ---
    print("--- __len__ ---")

    deck = Deck()
    print(f"len(deck) = {len(deck)}")
    # Output: len(deck) = 52
    assert len(deck) == 52

    small = Deck([Card("A", "spades"), Card("K", "hearts")])
    print(f"len(small) = {len(small)}")
    # Output: len(small) = 2
    assert len(small) == 2

    print()

    # --- Section 5: __getitem__ (indexing and slicing) ---
    print("--- __getitem__ (indexing and slicing) ---")

    deck = Deck()

    print(f"deck[0]  = {deck[0]}")
    # Output: deck[0]  = 2♣
    assert str(deck[0]) == "2♣"

    print(f"deck[-1] = {deck[-1]}")
    # Output: deck[-1] = A♠
    assert str(deck[-1]) == "A♠"

    print(f"deck[12] = {deck[12]}")
    # Output: deck[12] = A♣
    assert str(deck[12]) == "A♣"

    # Slicing returns a new Deck (because we check for slice in __getitem__)
    top_three = deck[:3]
    print(f"deck[:3] = {[str(c) for c in top_three]}")
    # Output: deck[:3] = ['2♣', '3♣', '4♣']
    assert len(top_three) == 3
    assert isinstance(top_three, Deck)

    # Step slicing works too -- every 13th card gives one card per suit
    every_13th = deck[0::13]
    print(f"deck[0::13] = {[str(c) for c in every_13th]}")
    # Output: deck[0::13] = ['2♣', '2♦', '2♥', '2♠']
    assert len(every_13th) == 4

    print()

    # --- Section 6: __contains__ (membership test) ---
    print("--- __contains__ (membership test) ---")

    deck = Deck()
    ace_of_spades = Card("A", "spades")
    joker = Card("Joker", "wild")

    print(f"ace_of_spades in deck: {ace_of_spades in deck}")
    # Output: ace_of_spades in deck: True
    assert ace_of_spades in deck

    print(f"joker in deck: {joker in deck}")
    # Output: joker in deck: False
    assert joker not in deck

    print()

    # --- Section 7: __iter__ (iteration) ---
    print("--- __iter__ (iteration) ---")

    deck = Deck()

    # Collect all unique suits by iterating
    suits = set()
    for card in deck:
        suits.add(card.suit)
    print(f"Suits in deck: {sorted(suits)}")
    # Output: Suits in deck: ['clubs', 'diamonds', 'hearts', 'spades']
    assert len(suits) == 4

    # Iteration enables list(), sorted(), and comprehensions
    aces = [c for c in deck if c.rank == "A"]
    print(f"Number of aces: {len(aces)}")
    # Output: Number of aces: 4
    assert len(aces) == 4

    print(f"Aces: {[str(a) for a in aces]}")
    # Output: Aces: ['A♣', 'A♦', 'A♥', 'A♠']

    # reversed() works because __getitem__ + __len__ provide sequence protocol
    last_three = list(deck)[-3:]
    print(f"Last 3 cards: {[str(c) for c in last_three]}")
    # Output: Last 3 cards: ['Q♠', 'K♠', 'A♠']

    print()

    # --- Section 8: __bool__ (truthiness) ---
    print("--- __bool__ (truthiness) ---")

    full_deck = Deck()
    empty_deck = Deck([])

    print(f"bool(full_deck):  {bool(full_deck)}")
    # Output: bool(full_deck):  True
    assert bool(full_deck) is True

    print(f"bool(empty_deck): {bool(empty_deck)}")
    # Output: bool(empty_deck): False
    assert bool(empty_deck) is False

    # This means you can use deck directly in if/while:
    if full_deck:
        print("Full deck is truthy")
        # Output: Full deck is truthy

    if not empty_deck:
        print("Empty deck is falsy")
        # Output: Empty deck is falsy

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
    # Output:
    #   len(obj)             →  obj.__len__()
    #   obj[i]               →  obj.__getitem__(i)
    #   obj[1:3]             →  obj.__getitem__(slice(1, 3))
    #   item in obj          →  obj.__contains__(item)
    #   for x in obj:        →  iter(obj) → obj.__iter__()
    #   bool(obj)            →  obj.__bool__()
    #   str(obj)             →  obj.__str__()
    #   repr(obj)            →  obj.__repr__()
    #   obj1 == obj2         →  obj1.__eq__(obj2)
    #   hash(obj)            →  obj.__hash__()

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

    # __getitem__ alone gives us iteration (Python calls [0], [1], ... until IndexError)
    items = list(seq)
    print(f"Iteration from __getitem__ alone: {items}")
    # Output: Iteration from __getitem__ alone: [10, 20, 30]
    assert items == [10, 20, 30]

    # __getitem__ alone gives us 'in' (Python iterates to check)
    print(f"20 in seq: {20 in seq}")
    # Output: 20 in seq: True
    assert 20 in seq

    print(f"99 in seq: {99 in seq}")
    # Output: 99 in seq: False
    assert 99 not in seq

    print()

    # --- Section 11: Verifying the __eq__ / __hash__ contract ---
    print("--- __eq__ / __hash__ Contract ---")

    a = Card("A", "spades")
    b = Card("A", "spades")
    c = Card("K", "hearts")

    # Equal objects must have equal hashes
    assert a == b
    assert hash(a) == hash(b)
    print(f"a == b: {a == b}, hash(a) == hash(b): {hash(a) == hash(b)}")
    # Output: a == b: True, hash(a) == hash(b): True

    # Unequal objects may or may not have equal hashes (collisions are ok)
    assert a != c
    print(f"a != c: {a != c}, hashes may differ: hash(a)={hash(a)}, hash(c)={hash(c)}")
    # Output: a != c: True, hashes may differ: hash(a)=<int>, hash(c)=<int>

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
