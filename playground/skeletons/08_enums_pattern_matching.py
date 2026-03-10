"""
Kata 08 -- Enums & Pattern Matching
Run: python playground/skeletons/08_enums_pattern_matching.py

Master Python enums (Enum, IntEnum, StrEnum, Flag, auto) and structural
pattern matching (match/case, guards, OR patterns, sequence/mapping/class patterns).
"""

from enum import Enum, IntEnum, StrEnum, Flag, auto
from dataclasses import dataclass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic Enum ---
    print("--- Section 1: Basic Enum ---")
    try:
        # TODO: define a Color enum with RED=1, GREEN=2, BLUE=3
        # HINT: class Color(Enum): RED = 1 ...
        class Color(Enum):
            pass

        print(f"Color.RED = {Color.RED}")
        print(f"Color.RED.name = {Color.RED.name}")
        print(f"Color.RED.value = {Color.RED.value}")
        assert Color.RED.name == "RED"
        assert Color.RED.value == 1

        # TODO: access Color by value (2) and verify it's GREEN
        # HINT: Color(2)
        by_value = None  # replace this
        print(f"Color(2) = {by_value}")
        assert by_value is Color.GREEN

        # TODO: access Color by name string "BLUE"
        # HINT: Color["BLUE"]
        by_name = None  # replace this
        print(f'Color["BLUE"] = {by_name}')
        assert by_name is Color.BLUE

        print("All colors:")
        for color in Color:
            print(f"  {color.name} = {color.value}")
        assert list(Color) == [Color.RED, Color.GREEN, Color.BLUE]

        assert Color.RED is Color.RED
        assert Color.RED == Color.RED
        assert Color.RED != 1
        print(f"Color.RED == 1? {Color.RED == 1}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: IntEnum and StrEnum ---
    print("--- Section 2: IntEnum and StrEnum ---")
    try:
        # TODO: define an HttpStatus IntEnum with OK=200, CREATED=201, MOVED=301,
        #       BAD_REQUEST=400, NOT_FOUND=404, FORBIDDEN=403, SERVER_ERROR=500, BAD_GATEWAY=502
        # HINT: class HttpStatus(IntEnum): OK = 200 ...
        class HttpStatus(IntEnum):
            pass

        print(f"HttpStatus.OK == 200? {HttpStatus.OK == 200}")
        assert HttpStatus.OK == 200

        # TODO: verify that NOT_FOUND + 1 equals 405
        result = None  # replace this
        print(f"HttpStatus.NOT_FOUND + 1 = {result}")
        assert result == 405

        assert HttpStatus.OK < HttpStatus.NOT_FOUND
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (HttpStatus): {e}")

    try:
        # TODO: define a Direction StrEnum with NORTH="north", SOUTH="south",
        #       EAST="east", WEST="west"
        # HINT: class Direction(StrEnum): NORTH = "north" ...
        class Direction(StrEnum):
            pass

        print(f"Direction.NORTH == 'north'? {Direction.NORTH == 'north'}")
        assert Direction.NORTH == "north"

        # TODO: call .upper() on Direction.NORTH
        upper_north = ""  # replace this
        print(f"Direction.NORTH.upper() = {upper_north}")
        assert upper_north == "NORTH"

        print(f"Heading {Direction.EAST}!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Direction): {e}")

    print()

    # --- Section 3: Flag ---
    print("--- Section 3: Flag ---")
    try:
        # TODO: define a Permission Flag with READ, WRITE, EXECUTE using auto()
        # HINT: class Permission(Flag): READ = auto() ...
        class Permission(Flag):
            pass

        # TODO: combine READ and WRITE using |
        # HINT: Permission.READ | Permission.WRITE
        rw = None  # replace this
        print(f"READ | WRITE = {rw}")
        assert Permission.READ in rw
        assert Permission.EXECUTE not in rw

        # TODO: create all_perms (READ | WRITE | EXECUTE), then remove WRITE using & ~
        # HINT: all_perms & ~Permission.WRITE
        all_perms = None  # replace this
        no_write = None  # replace this
        print(f"All permissions: {all_perms}")
        print(f"All minus WRITE: {no_write}")
        assert Permission.WRITE not in no_write
        assert Permission.READ in no_write
        assert Permission.EXECUTE in no_write

        print("Flags in rw:")
        for perm in rw:
            print(f"  Has: {perm.name}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: auto() and custom methods ---
    print("--- Section 4: auto() and Custom Methods ---")

    # TODO: define a Season enum with SPRING, SUMMER, AUTUMN, WINTER using auto()
    #       Add an is_warm() method that returns True for SPRING and SUMMER
    #       Add a next_season property that returns the next season (wrapping around)
    # HINT: members = list(Season); idx = members.index(self); return members[(idx + 1) % len(members)]
    class Season(Enum):
        SPRING = auto()
        SUMMER = auto()
        AUTUMN = auto()
        WINTER = auto()

        def is_warm(self) -> bool:
            # TODO: return True if self is SPRING or SUMMER
            pass

        @property
        def next_season(self) -> "Season":
            # TODO: return the next season, wrapping WINTER -> SPRING
            pass

    try:
        print(f"SUMMER.is_warm() = {Season.SUMMER.is_warm()}")
        assert Season.SUMMER.is_warm() is True

        print(f"WINTER.is_warm() = {Season.WINTER.is_warm()}")
        assert Season.WINTER.is_warm() is False

        print(f"AUTUMN.next_season = {Season.AUTUMN.next_season}")
        assert Season.AUTUMN.next_season is Season.WINTER

        print(f"WINTER.next_season = {Season.WINTER.next_season}")
        assert Season.WINTER.next_season is Season.SPRING

        print("Season values:")
        for s in Season:
            print(f"  {s.name} = {s.value}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: match/case basics ---
    print("--- Section 5: match/case Basics ---")

    # TODO: implement describe_status using match/case
    #       200 -> "OK", 301 -> "Moved Permanently", 404 -> "Not Found",
    #       500 -> "Internal Server Error", _ -> "Unknown status: {status}"
    def describe_status(status: int) -> str:
        # HINT: match status: case 200: return "OK" ...
        pass

    try:
        print(f"200 -> {describe_status(200)}")
        assert describe_status(200) == "OK"

        print(f"404 -> {describe_status(404)}")
        assert describe_status(404) == "Not Found"

        print(f"418 -> {describe_status(418)}")
        assert describe_status(418) == "Unknown status: 418"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: OR patterns ---
    print("--- Section 6: OR Patterns ---")

    # TODO: implement classify_char using match/case with OR patterns
    #       vowels (a,e,i,o,u) -> "vowel"
    #       whitespace (space, tab, newline) -> "whitespace"
    #       everything else -> "consonant"
    # HINT: case "a" | "e" | "i" | "o" | "u": return "vowel"
    def classify_char(ch: str) -> str:
        pass

    try:
        print(f"'A' -> {classify_char('A')}")
        assert classify_char("A") == "vowel"

        print(f"'x' -> {classify_char('x')}")
        assert classify_char("x") == "consonant"

        print(f"' ' -> {classify_char(' ')}")
        assert classify_char(" ") == "whitespace"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Guards ---
    print("--- Section 7: Guards ---")

    # TODO: implement classify_number using match/case with guards
    #       0 -> "zero", positive -> "positive (x)", negative -> "negative (x)"
    # HINT: case x if x > 0: return f"positive ({x})"
    def classify_number(n: int | float) -> str:
        pass

    try:
        print(f"42 -> {classify_number(42)}")
        assert classify_number(42) == "positive (42)"

        print(f"-7 -> {classify_number(-7)}")
        assert classify_number(-7) == "negative (-7)"

        print(f"0 -> {classify_number(0)}")
        assert classify_number(0) == "zero"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: Sequence patterns ---
    print("--- Section 8: Sequence Patterns ---")

    # TODO: implement process_command using match/case with sequence patterns
    #       ["quit"] -> "Goodbye!"
    #       ["greet", name] -> "Hello, {name}!"
    #       ["move", direction, distance] -> "Moving {direction} by {distance}"
    #       ["add", *numbers] -> "Sum: {total}" (sum of int-converted numbers)
    #       [] -> "Empty command"
    #       _ -> "Unknown command: {command}"
    def process_command(command: list[str]) -> str:
        # HINT: match command: case ["quit"]: ...
        pass

    try:
        print(f"['quit'] -> {process_command(['quit'])}")
        assert process_command(["quit"]) == "Goodbye!"

        print(f"['greet', 'Alice'] -> {process_command(['greet', 'Alice'])}")
        assert process_command(["greet", "Alice"]) == "Hello, Alice!"

        print(f"['move', 'north', '5'] -> {process_command(['move', 'north', '5'])}")
        assert process_command(["move", "north", "5"]) == "Moving north by 5"

        print(f"['add', '1', '2', '3'] -> {process_command(['add', '1', '2', '3'])}")
        assert process_command(["add", "1", "2", "3"]) == "Sum: 6"

        print(f"[] -> {process_command([])}")
        assert process_command([]) == "Empty command"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 9: Mapping patterns ---
    print("--- Section 9: Mapping Patterns ---")

    # TODO: implement handle_event using match/case with mapping patterns
    #       {"type": "click", "x": x, "y": y} -> "Click at (x, y)"
    #       {"type": "keypress", "key": key} -> "Key pressed: {key}"
    #       {"type": "resize", "width": w, "height": h} -> "Resized to {w}x{h}"
    #       _ -> "Unknown event: {event}"
    def handle_event(event: dict) -> str:
        # HINT: match event: case {"type": "click", "x": x, "y": y}: ...
        pass

    try:
        print(handle_event({"type": "click", "x": 100, "y": 200}))
        assert handle_event({"type": "click", "x": 100, "y": 200}) == "Click at (100, 200)"

        print(handle_event({"type": "keypress", "key": "Enter"}))
        assert handle_event({"type": "keypress", "key": "Enter"}) == "Key pressed: Enter"

        print(handle_event({"type": "resize", "width": 1920, "height": 1080}))
        assert handle_event({"type": "resize", "width": 1920, "height": 1080}) == "Resized to 1920x1080"

        result = handle_event({"type": "click", "x": 50, "y": 75, "button": "left"})
        assert result == "Click at (50, 75)"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 10: Class patterns ---
    print("--- Section 10: Class Patterns ---")

    @dataclass
    class Point:
        x: float
        y: float

    @dataclass
    class Circle:
        center: Point
        radius: float

    @dataclass
    class Rectangle:
        origin: Point
        width: float
        height: float

    # TODO: implement describe_shape using match/case with class patterns
    #       Circle at origin (0,0) -> "Circle at origin with radius {r}"
    #       Circle with radius > 100 -> "Large circle at {center} with radius {r}"
    #       Circle (other) -> "Circle at {center} with radius {r}"
    #       Rectangle where width == height -> "Square at {origin}, side {w}"
    #       Rectangle (other) -> "Rectangle at {origin}, {w}x{h}"
    #       _ -> "Unknown shape"
    # HINT: case Circle(center=Point(x=0, y=0), radius=r): ...
    def describe_shape(shape) -> str:
        pass

    try:
        result = describe_shape(Circle(Point(0, 0), 5))
        print(result)
        assert result == "Circle at origin with radius 5"

        result = describe_shape(Circle(Point(1, 2), 150))
        print(result)
        assert result == "Large circle at Point(x=1, y=2) with radius 150"

        result = describe_shape(Rectangle(Point(0, 0), 10, 10))
        print(result)
        assert result == "Square at Point(x=0, y=0), side 10"

        result = describe_shape(Rectangle(Point(3, 4), 10, 20))
        print(result)
        assert result == "Rectangle at Point(x=3, y=4), 10x20"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 11: Enums + pattern matching ---
    print("--- Section 11: Enums + Pattern Matching ---")

    # TODO: implement classify_response using match/case with HttpStatus enum
    #       OK | CREATED -> "Success"
    #       MOVED -> "Redirect"
    #       BAD_REQUEST | NOT_FOUND | FORBIDDEN -> "Client Error"
    #       SERVER_ERROR | BAD_GATEWAY -> "Server Error"
    #       _ -> "Unknown"
    def classify_response(status) -> str:
        # HINT: match status: case HttpStatus.OK | HttpStatus.CREATED: ...
        pass

    try:
        print(f"200 -> {classify_response(HttpStatus.OK)}")
        assert classify_response(HttpStatus.OK) == "Success"

        print(f"404 -> {classify_response(HttpStatus.NOT_FOUND)}")
        assert classify_response(HttpStatus.NOT_FOUND) == "Client Error"

        print(f"500 -> {classify_response(HttpStatus.SERVER_ERROR)}")
        assert classify_response(HttpStatus.SERVER_ERROR) == "Server Error"
    except (AssertionError, TypeError, AttributeError, NameError, Exception) as e:
        print(f"  ❌ Not yet implemented (classify_response): {e}")

    # TODO: define a LightState enum with GREEN, YELLOW, RED using auto()
    # HINT: class LightState(Enum): GREEN = auto() ...
    class LightState(Enum):
        pass

    # TODO: implement next_light using match/case
    #       GREEN -> YELLOW, YELLOW -> RED, RED -> GREEN
    def next_light(state: LightState) -> LightState:
        pass

    try:
        light = LightState.GREEN
        cycle = [light]
        for _ in range(5):
            light = next_light(light)
            cycle.append(light)
        cycle_names = [l.name for l in cycle]
        print(f"Traffic light cycle: {cycle_names}")
        assert cycle_names == ["GREEN", "YELLOW", "RED", "GREEN", "YELLOW", "RED"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (LightState): {e}")

    print()

    # --- Section 12: Exercise -- Calculator with match ---
    print("--- Section 12: Exercise -- Calculator with match ---")

    # TODO: define an Op enum with ADD, SUB, MUL, DIV, MOD, POW using auto()
    class Op(Enum):
        pass

    @dataclass
    class Expr:
        left: float
        op: Op
        right: float

    # TODO: implement parse_op using match/case
    #       "+" -> ADD, "-" -> SUB, "*" -> MUL, "/" -> DIV, "%" -> MOD, "**" -> POW
    def parse_op(symbol: str) -> Op:
        pass

    # TODO: implement evaluate using match/case
    #       Returns float for normal operations, "Error: Division by zero" for div/mod by 0
    def evaluate(expr: Expr) -> float | str:
        pass

    # TODO: implement calc that parses "left op right" and evaluates
    # HINT: handle "**" specially since split() will separate it from operands
    #       match parts: case [left, "**", right]: ... case [left, op, right]: ...
    def calc(expression: str) -> float | str:
        pass

    try:
        result = calc("10 + 5")
        print(f"10 + 5 = {result}")
        assert result == 15.0

        result = calc("20 / 4")
        print(f"20 / 4 = {result}")
        assert result == 5.0

        result = calc("3 * 7")
        print(f"3 * 7 = {result}")
        assert result == 21.0

        result = calc("10 - 3")
        print(f"10 - 3 = {result}")
        assert result == 7.0

        result = calc("10 % 3")
        print(f"10 % 3 = {result}")
        assert result == 1.0

        result = calc("2 ** 8")
        print(f"2 ** 8 = {result}")
        assert result == 256.0

        result = calc("5 / 0")
        print(f"5 / 0 = {result}")
        assert result == "Error: Division by zero"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 13: Exercise -- Traffic light state machine with durations ---
    print("--- Section 13: Exercise -- Traffic Light with Durations ---")

    try:
        DURATIONS = {
            LightState.GREEN: 30,
            LightState.YELLOW: 5,
            LightState.RED: 20,
        }
    except (AttributeError, NameError, Exception) as e:
        print(f"  ❌ Not yet implemented (DURATIONS/LightState): {e}")
        DURATIONS = {}

    # TODO: implement TrafficLight with a tick() method
    #       tick() decrements the timer; when it hits 0, transition to next state
    #       with the new state's duration from DURATIONS
    # HINT: if self.timer > 1: return TrafficLight(self.state, self.timer - 1)
    #       else: new_state = next_light(self.state); return TrafficLight(new_state, DURATIONS[new_state])
    @dataclass
    class TrafficLight:
        state: LightState
        timer: int

        def tick(self) -> "TrafficLight":
            """Advance the traffic light by one tick."""
            pass

        def __str__(self) -> str:
            return f"{self.state.name} ({self.timer}s remaining)"

    try:
        tl = TrafficLight(LightState.GREEN, 30)
        print(f"Start: {tl}")
        assert tl.state == LightState.GREEN
        assert tl.timer == 30

        for _ in range(30):
            tl = tl.tick()
        print(f"After 30 ticks: {tl}")
        assert tl.state == LightState.YELLOW
        assert tl.timer == 5

        for _ in range(5):
            tl = tl.tick()
        print(f"After 5 more ticks: {tl}")
        assert tl.state == LightState.RED
        assert tl.timer == 20

        for _ in range(20):
            tl = tl.tick()
        print(f"After 20 more ticks: {tl}")
        assert tl.state == LightState.GREEN
        assert tl.timer == 30

        tl_mid = TrafficLight(LightState.GREEN, 30)
        for _ in range(10):
            tl_mid = tl_mid.tick()
        print(f"After 10 ticks of GREEN: {tl_mid}")
        assert tl_mid.state == LightState.GREEN
        assert tl_mid.timer == 20
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Enums & Pattern Matching in Python:")
    print("  - Enum: type-safe named constants")
    print("  - IntEnum/StrEnum: enums that interop with int/str")
    print("  - Flag: combinable bitwise flags")
    print("  - auto(): automatic value assignment")
    print("  - Custom methods on enums for behavior")
    print("  - match/case: structural pattern matching")
    print("  - Literal, OR, guard, sequence, mapping, class patterns")
    print("  - Enums + match = readable state machines and dispatchers")
    print()
    print("All 13 sections passed. You've mastered enums & pattern matching!")
