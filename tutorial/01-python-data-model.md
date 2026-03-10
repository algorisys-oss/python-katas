# Kata 01 -- Python Data Model

[prev: 00-project-setup](./00-project-setup.md) | [next: 02-iterators-generators](./02-iterators-generators.md)

---

## What We're Building

Every Python object participates in a *protocol* -- a set of special ("dunder") methods that Python's operators and built-in functions call behind the scenes. When you write `len(deck)`, Python calls `deck.__len__()`. When you write `card in deck`, Python calls `deck.__contains__(card)`. This is the **Python Data Model**, and understanding it is the single most important step toward writing Pythonic code.

In this kata we build two classes -- `Card` and `Deck` -- that implement the most important dunder methods. By the end you'll know exactly what happens when Python evaluates expressions like `deck[3]`, `len(deck)`, `card == other`, and `if deck:`.

## Concepts You'll Learn

| Dunder Method | Triggered By | Purpose |
|---|---|---|
| `__repr__` | `repr(obj)`, REPL display | Unambiguous developer representation |
| `__str__` | `str(obj)`, `print(obj)` | Human-readable string |
| `__eq__` | `a == b` | Equality comparison |
| `__hash__` | `hash(obj)`, set/dict membership | Hashability for sets and dict keys |
| `__len__` | `len(obj)` | Collection size |
| `__getitem__` | `obj[key]`, slicing | Index/key access |
| `__contains__` | `item in obj` | Membership test |
| `__bool__` | `if obj:`, `bool(obj)` | Truthiness |
| `__iter__` | `for x in obj:` | Iteration support |

## The Code

### Step 1: The `Card` class -- identity and display

A playing card has a rank and a suit. Two cards with the same rank and suit should be equal, printable, and usable as dictionary keys.

```python
class Card:
    """A single playing card."""

    SUIT_SYMBOLS = {"spades": "♠", "hearts": "♥", "diamonds": "♦", "clubs": "♣"}

    def __init__(self, rank: str, suit: str) -> None:
        self.rank = rank
        self.suit = suit

    def __repr__(self) -> str:
        return f"Card({self.rank!r}, {self.suit!r})"

    def __str__(self) -> str:
        symbol = self.SUIT_SYMBOLS.get(self.suit, self.suit)
        return f"{self.rank}{symbol}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))
```

**Why two string methods?** `__repr__` is for developers -- it should look like a valid constructor call so you can recreate the object. `__str__` is for users -- it should be pretty. When you type an object's name in the REPL, Python calls `__repr__`. When you `print()` it, Python calls `__str__` (falling back to `__repr__` if `__str__` isn't defined).

**Why return `NotImplemented`?** When `__eq__` receives an object it doesn't know how to compare against, returning `NotImplemented` (not `NotImplementedError`!) tells Python to try the other operand's `__eq__` instead. This is how Python supports mixed-type comparisons gracefully.

**Why implement `__hash__`?** Python's rule: objects that compare equal *must* have the same hash. If you define `__eq__` without `__hash__`, Python sets `__hash__` to `None`, making your objects unhashable -- they can't go in sets or be dict keys. We hash a tuple of the fields used in `__eq__`.

```python
card = Card("A", "spades")
print(repr(card))
# Output: Card('A', 'spades')

print(card)
# Output: A♠

print(Card("A", "spades") == Card("A", "spades"))
# Output: True

print(Card("A", "spades") == Card("K", "hearts"))
# Output: False

# Usable as dict key and set member because __hash__ is defined
hand = {Card("A", "spades"), Card("K", "hearts"), Card("A", "spades")}
print(len(hand))
# Output: 2
```

### Step 2: The `Deck` class -- behaving like a collection

A deck is a collection of cards. Python has a rich vocabulary for talking about collections -- `len()`, indexing, slicing, `in`, `for`, `bool()` -- and each one maps to a dunder method.

```python
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
        return len(self._cards)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Deck(self._cards[index])
        return self._cards[index]

    def __contains__(self, card: Card) -> bool:
        return card in self._cards

    def __iter__(self):
        return iter(self._cards)

    def __bool__(self) -> bool:
        return len(self._cards) > 0
```

### Step 3: Using the Deck

Now watch how naturally our `Deck` works with Python's built-in operations:

```python
deck = Deck()

# __len__: how many cards?
print(len(deck))
# Output: 52

# __getitem__: index access
print(deck[0])
# Output: 2♣

print(deck[-1])
# Output: A♠

# __getitem__ with slices: returns a new Deck
top_three = deck[:3]
print(len(top_three))
# Output: 3

# __contains__: membership test
ace_of_spades = Card("A", "spades")
print(ace_of_spades in deck)
# Output: True

# __iter__: iteration
suits = set()
for card in deck:
    suits.add(card.suit)
print(sorted(suits))
# Output: ['clubs', 'diamonds', 'hearts', 'spades']

# __bool__: truthiness
print(bool(deck))
# Output: True

empty_deck = Deck([])
print(bool(empty_deck))
# Output: False
```

### Step 4: The protocol concept

The key insight is that Python doesn't care about your class hierarchy -- it cares about what methods you implement. This is called "duck typing" or, more formally, **protocols**. If your object has `__len__` and `__getitem__`, it behaves like a sequence. If it has `__iter__`, it's iterable. You don't need to inherit from any base class.

```python
# Python's built-in functions call your dunder methods:
#
#   len(x)        →  x.__len__()
#   x[i]          →  x.__getitem__(i)
#   item in x     →  x.__contains__(item)
#   for i in x:   →  iter(x) → x.__iter__()
#   bool(x)       →  x.__bool__()
#   str(x)        →  x.__str__()
#   repr(x)       →  x.__repr__()
#   x == y        →  x.__eq__(y)
#   hash(x)       →  x.__hash__()
```

## Playground

Run the full interactive demo:

```bash
python playground/01_python_data_model.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### The dispatch chain

When Python encounters an expression like `len(deck)`, here's what happens:

```
len(deck)
  → Python checks: does deck's type define __len__?
    → Yes: call type(deck).__len__(deck)
    → No: raise TypeError("object of type '...' has no len()")
```

The same pattern applies to every operator and built-in function:

```
deck[0]        → type(deck).__getitem__(deck, 0)
card in deck   → type(deck).__contains__(deck, card)
if deck:       → type(deck).__bool__(deck)
for c in deck: → type(deck).__iter__(deck)  →  returns an iterator
str(card)      → type(card).__str__(card)
card == other  → type(card).__eq__(card, other)
```

### Fallback behavior

Python has sensible fallbacks:

- If `__contains__` is missing but `__iter__` exists, Python iterates to check membership.
- If `__bool__` is missing but `__len__` exists, Python uses `len(obj) != 0`.
- If `__str__` is missing, Python falls back to `__repr__`.
- If `__iter__` is missing but `__getitem__` exists, Python creates an iterator that calls `__getitem__` with 0, 1, 2, ... until `IndexError`.

This means even a minimal `__getitem__` gives you iteration, membership testing, and more -- for free.

### `__eq__` and `__hash__` contract

This is a critical rule:

> **If `a == b`, then `hash(a) == hash(b)` must also be true.**

The reverse is not required (different objects can have the same hash -- that's just a collision). But if equal objects have different hashes, sets and dicts will silently break:

```python
# Bad: equal objects with different hashes
card1 = Card("A", "spades")
card2 = Card("A", "spades")
assert card1 == card2                  # True
assert hash(card1) == hash(card2)      # Must also be True!

# If this contract is violated, sets won't deduplicate:
# {card1, card2} might have 2 elements instead of 1
```

### Default `__hash__` behavior

- If you don't define `__eq__` or `__hash__`: objects use identity (`id()`) for both.
- If you define `__eq__` but not `__hash__`: Python sets `__hash__ = None` → unhashable.
- If you define both: you control equality and hashing.

This is why we always define `__hash__` alongside `__eq__` when we want objects usable in sets/dicts.

## Exercises

### Exercise 1: Add `__add__` to combine decks

Implement `__add__` on `Deck` so you can combine two decks:

```python
deck1 = Deck([Card("A", "spades"), Card("K", "hearts")])
deck2 = Deck([Card("Q", "diamonds")])
combined = deck1 + deck2
print(len(combined))
# Output: 3
print(combined[2])
# Output: Q♦
```

Hint: `__add__` should return a new `Deck`, not modify either operand.

### Exercise 2: Add `__mul__` for repeating a deck

Implement `__mul__` so `deck * 3` creates a deck with all cards repeated 3 times:

```python
small = Deck([Card("A", "spades")])
triple = small * 3
print(len(triple))
# Output: 3
```

### Exercise 3: Implement a custom `Hand` collection

Build a `Hand` class that represents a player's hand in a card game:

- `__init__` accepts a list of `Card` objects
- `__len__` returns how many cards are in the hand
- `__contains__` checks if a card is in the hand
- `__repr__` shows something like `Hand([Card('A', 'spades'), Card('K', 'hearts')])`
- `__str__` shows something pretty like `Hand: A♠ K♥`
- `__eq__` -- two hands are equal if they have the same cards (regardless of order)
- `__bool__` -- an empty hand is falsy
- `add(card)` -- adds a card to the hand
- `discard(card)` -- removes a card from the hand

### Exercise 4: Implement `__lt__` for card comparison

Add comparison methods to `Card` so cards can be sorted by rank:

```python
cards = [Card("K", "hearts"), Card("2", "clubs"), Card("A", "spades")]
print(sorted(cards))
# Output: [Card('2', 'clubs'), Card('K', 'hearts'), Card('A', 'spades')]
```

Hint: use `functools.total_ordering` -- implement `__eq__` and `__lt__`, and the decorator fills in `__le__`, `__gt__`, `__ge__`.

## What's Next

In [Kata 02 -- Iterators & Generators](./02-iterators-generators.md), we'll go deeper into the iteration protocol. You'll learn how `__iter__` and `__next__` work under the hood, build custom iterators, and discover `yield` -- Python's most elegant feature for lazy data processing.

---

[prev: 00-project-setup](./00-project-setup.md) | [next: 02-iterators-generators](./02-iterators-generators.md)
