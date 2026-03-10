"""
Kata 08 -- Enums & Pattern Matching
Run: python playground/08_enums_pattern_matching.py

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

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    # Access by attribute, name, and value
    print(f"Color.RED = {Color.RED}")
    # Output: Color.RED = Color.RED
    print(f"Color.RED.name = {Color.RED.name}")
    # Output: Color.RED.name = RED
    print(f"Color.RED.value = {Color.RED.value}")
    # Output: Color.RED.value = 1
    assert Color.RED.name == "RED"
    assert Color.RED.value == 1

    # Access by value
    print(f"Color(2) = {Color(2)}")
    # Output: Color(2) = Color.GREEN
    assert Color(2) is Color.GREEN

    # Access by name string
    print(f'Color["BLUE"] = {Color["BLUE"]}')
    # Output: Color["BLUE"] = Color.BLUE
    assert Color["BLUE"] is Color.BLUE

    # Iteration
    print("All colors:")
    for color in Color:
        print(f"  {color.name} = {color.value}")
    # Output:
    #   RED = 1
    #   GREEN = 2
    #   BLUE = 3
    assert list(Color) == [Color.RED, Color.GREEN, Color.BLUE]

    # Identity and equality
    assert Color.RED is Color.RED
    assert Color.RED == Color.RED
    assert Color.RED != 1  # Enum != int

    # Membership
    assert isinstance(Color.RED, Color)
    print(f"Color.RED == 1? {Color.RED == 1}")
    # Output: Color.RED == 1? False

    print()

    # --- Section 2: IntEnum and StrEnum ---
    print("--- Section 2: IntEnum and StrEnum ---")

    class HttpStatus(IntEnum):
        OK = 200
        CREATED = 201
        MOVED = 301
        BAD_REQUEST = 400
        NOT_FOUND = 404
        FORBIDDEN = 403
        SERVER_ERROR = 500
        BAD_GATEWAY = 502

    # IntEnum members compare equal to their int values
    print(f"HttpStatus.OK == 200? {HttpStatus.OK == 200}")
    # Output: HttpStatus.OK == 200? True
    assert HttpStatus.OK == 200

    # Arithmetic works
    print(f"HttpStatus.NOT_FOUND + 1 = {HttpStatus.NOT_FOUND + 1}")
    # Output: HttpStatus.NOT_FOUND + 1 = 405
    assert HttpStatus.NOT_FOUND + 1 == 405

    # Comparison works
    assert HttpStatus.OK < HttpStatus.NOT_FOUND

    class Direction(StrEnum):
        NORTH = "north"
        SOUTH = "south"
        EAST = "east"
        WEST = "west"

    # StrEnum members behave like strings
    print(f"Direction.NORTH == 'north'? {Direction.NORTH == 'north'}")
    # Output: Direction.NORTH == 'north'? True
    assert Direction.NORTH == "north"

    print(f"Direction.NORTH.upper() = {Direction.NORTH.upper()}")
    # Output: Direction.NORTH.upper() = NORTH
    assert Direction.NORTH.upper() == "NORTH"

    print(f"Heading {Direction.EAST}!")
    # Output: Heading east!

    print()

    # --- Section 3: Flag ---
    print("--- Section 3: Flag ---")

    class Permission(Flag):
        READ = auto()      # 1
        WRITE = auto()     # 2
        EXECUTE = auto()   # 4

    # Combine flags
    rw = Permission.READ | Permission.WRITE
    print(f"READ | WRITE = {rw}")
    # Output: READ | WRITE = Permission.READ|WRITE
    assert Permission.READ in rw
    assert Permission.EXECUTE not in rw

    # All permissions
    all_perms = Permission.READ | Permission.WRITE | Permission.EXECUTE
    print(f"All permissions: {all_perms}")
    # Output: All permissions: Permission.READ|WRITE|EXECUTE

    # Remove a permission
    no_write = all_perms & ~Permission.WRITE
    print(f"All minus WRITE: {no_write}")
    # Output: All minus WRITE: Permission.READ|EXECUTE
    assert Permission.WRITE not in no_write
    assert Permission.READ in no_write
    assert Permission.EXECUTE in no_write

    # Iterate over set flags
    print("Flags in rw:")
    for perm in rw:
        print(f"  Has: {perm.name}")
    # Output:
    #   Has: READ
    #   Has: WRITE

    print()

    # --- Section 4: auto() and custom methods ---
    print("--- Section 4: auto() and Custom Methods ---")

    class Season(Enum):
        SPRING = auto()
        SUMMER = auto()
        AUTUMN = auto()
        WINTER = auto()

        def is_warm(self) -> bool:
            return self in (Season.SPRING, Season.SUMMER)

        @property
        def next_season(self) -> "Season":
            members = list(Season)
            idx = members.index(self)
            return members[(idx + 1) % len(members)]

    print(f"SUMMER.is_warm() = {Season.SUMMER.is_warm()}")
    # Output: SUMMER.is_warm() = True
    assert Season.SUMMER.is_warm() is True

    print(f"WINTER.is_warm() = {Season.WINTER.is_warm()}")
    # Output: WINTER.is_warm() = False
    assert Season.WINTER.is_warm() is False

    print(f"AUTUMN.next_season = {Season.AUTUMN.next_season}")
    # Output: AUTUMN.next_season = Season.WINTER
    assert Season.AUTUMN.next_season is Season.WINTER

    print(f"WINTER.next_season = {Season.WINTER.next_season}")
    # Output: WINTER.next_season = Season.SPRING
    assert Season.WINTER.next_season is Season.SPRING

    # auto() values
    print("Season values:")
    for s in Season:
        print(f"  {s.name} = {s.value}")
    # Output:
    #   SPRING = 1
    #   SUMMER = 2
    #   AUTUMN = 3
    #   WINTER = 4

    print()

    # --- Section 5: match/case basics ---
    print("--- Section 5: match/case Basics ---")

    def describe_status(status: int) -> str:
        match status:
            case 200:
                return "OK"
            case 301:
                return "Moved Permanently"
            case 404:
                return "Not Found"
            case 500:
                return "Internal Server Error"
            case _:
                return f"Unknown status: {status}"

    print(f"200 -> {describe_status(200)}")
    # Output: 200 -> OK
    assert describe_status(200) == "OK"

    print(f"404 -> {describe_status(404)}")
    # Output: 404 -> Not Found
    assert describe_status(404) == "Not Found"

    print(f"418 -> {describe_status(418)}")
    # Output: 418 -> Unknown status: 418
    assert describe_status(418) == "Unknown status: 418"

    print()

    # --- Section 6: OR patterns ---
    print("--- Section 6: OR Patterns ---")

    def classify_char(ch: str) -> str:
        match ch.lower():
            case "a" | "e" | "i" | "o" | "u":
                return "vowel"
            case " " | "\t" | "\n":
                return "whitespace"
            case _:
                return "consonant"

    print(f"'A' -> {classify_char('A')}")
    # Output: 'A' -> vowel
    assert classify_char("A") == "vowel"

    print(f"'x' -> {classify_char('x')}")
    # Output: 'x' -> consonant
    assert classify_char("x") == "consonant"

    print(f"' ' -> {classify_char(' ')}")
    # Output: ' ' -> whitespace
    assert classify_char(" ") == "whitespace"

    print()

    # --- Section 7: Guards ---
    print("--- Section 7: Guards ---")

    def classify_number(n: int | float) -> str:
        match n:
            case 0:
                return "zero"
            case x if x > 0:
                return f"positive ({x})"
            case x if x < 0:
                return f"negative ({x})"

    print(f"42 -> {classify_number(42)}")
    # Output: 42 -> positive (42)
    assert classify_number(42) == "positive (42)"

    print(f"-7 -> {classify_number(-7)}")
    # Output: -7 -> negative (-7)
    assert classify_number(-7) == "negative (-7)"

    print(f"0 -> {classify_number(0)}")
    # Output: 0 -> zero
    assert classify_number(0) == "zero"

    print()

    # --- Section 8: Sequence patterns ---
    print("--- Section 8: Sequence Patterns ---")

    def process_command(command: list[str]) -> str:
        match command:
            case ["quit"]:
                return "Goodbye!"
            case ["greet", name]:
                return f"Hello, {name}!"
            case ["move", direction, distance]:
                return f"Moving {direction} by {distance}"
            case ["add", *numbers]:
                total = sum(int(n) for n in numbers)
                return f"Sum: {total}"
            case []:
                return "Empty command"
            case _:
                return f"Unknown command: {command}"

    print(f"['quit'] -> {process_command(['quit'])}")
    # Output: ['quit'] -> Goodbye!
    assert process_command(["quit"]) == "Goodbye!"

    print(f"['greet', 'Alice'] -> {process_command(['greet', 'Alice'])}")
    # Output: ['greet', 'Alice'] -> Hello, Alice!
    assert process_command(["greet", "Alice"]) == "Hello, Alice!"

    print(f"['move', 'north', '5'] -> {process_command(['move', 'north', '5'])}")
    # Output: ['move', 'north', '5'] -> Moving north by 5
    assert process_command(["move", "north", "5"]) == "Moving north by 5"

    print(f"['add', '1', '2', '3'] -> {process_command(['add', '1', '2', '3'])}")
    # Output: ['add', '1', '2', '3'] -> Sum: 6
    assert process_command(["add", "1", "2", "3"]) == "Sum: 6"

    print(f"[] -> {process_command([])}")
    # Output: [] -> Empty command
    assert process_command([]) == "Empty command"

    print()

    # --- Section 9: Mapping patterns ---
    print("--- Section 9: Mapping Patterns ---")

    def handle_event(event: dict) -> str:
        match event:
            case {"type": "click", "x": x, "y": y}:
                return f"Click at ({x}, {y})"
            case {"type": "keypress", "key": key}:
                return f"Key pressed: {key}"
            case {"type": "resize", "width": w, "height": h}:
                return f"Resized to {w}x{h}"
            case _:
                return f"Unknown event: {event}"

    print(handle_event({"type": "click", "x": 100, "y": 200}))
    # Output: Click at (100, 200)
    assert handle_event({"type": "click", "x": 100, "y": 200}) == "Click at (100, 200)"

    print(handle_event({"type": "keypress", "key": "Enter"}))
    # Output: Key pressed: Enter
    assert handle_event({"type": "keypress", "key": "Enter"}) == "Key pressed: Enter"

    print(handle_event({"type": "resize", "width": 1920, "height": 1080}))
    # Output: Resized to 1920x1080
    assert handle_event({"type": "resize", "width": 1920, "height": 1080}) == "Resized to 1920x1080"

    # Extra keys are ignored (partial matching)
    result = handle_event({"type": "click", "x": 50, "y": 75, "button": "left"})
    assert result == "Click at (50, 75)"

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

    def describe_shape(shape) -> str:
        match shape:
            case Circle(center=Point(x=0, y=0), radius=r):
                return f"Circle at origin with radius {r}"
            case Circle(center=center, radius=r) if r > 100:
                return f"Large circle at {center} with radius {r}"
            case Circle(center=center, radius=r):
                return f"Circle at {center} with radius {r}"
            case Rectangle(origin=origin, width=w, height=h) if w == h:
                return f"Square at {origin}, side {w}"
            case Rectangle(origin=origin, width=w, height=h):
                return f"Rectangle at {origin}, {w}x{h}"
            case _:
                return "Unknown shape"

    result = describe_shape(Circle(Point(0, 0), 5))
    print(result)
    # Output: Circle at origin with radius 5
    assert result == "Circle at origin with radius 5"

    result = describe_shape(Circle(Point(1, 2), 150))
    print(result)
    # Output: Large circle at Point(x=1, y=2) with radius 150
    assert result == "Large circle at Point(x=1, y=2) with radius 150"

    result = describe_shape(Rectangle(Point(0, 0), 10, 10))
    print(result)
    # Output: Square at Point(x=0, y=0), side 10
    assert result == "Square at Point(x=0, y=0), side 10"

    result = describe_shape(Rectangle(Point(3, 4), 10, 20))
    print(result)
    # Output: Rectangle at Point(x=3, y=4), 10x20
    assert result == "Rectangle at Point(x=3, y=4), 10x20"

    print()

    # --- Section 11: Enums + pattern matching ---
    print("--- Section 11: Enums + Pattern Matching ---")

    def classify_response(status: HttpStatus) -> str:
        match status:
            case HttpStatus.OK | HttpStatus.CREATED:
                return "Success"
            case HttpStatus.MOVED:
                return "Redirect"
            case HttpStatus.BAD_REQUEST | HttpStatus.NOT_FOUND | HttpStatus.FORBIDDEN:
                return "Client Error"
            case HttpStatus.SERVER_ERROR | HttpStatus.BAD_GATEWAY:
                return "Server Error"
            case _:
                return "Unknown"

    print(f"200 -> {classify_response(HttpStatus.OK)}")
    # Output: 200 -> Success
    assert classify_response(HttpStatus.OK) == "Success"

    print(f"404 -> {classify_response(HttpStatus.NOT_FOUND)}")
    # Output: 404 -> Client Error
    assert classify_response(HttpStatus.NOT_FOUND) == "Client Error"

    print(f"500 -> {classify_response(HttpStatus.SERVER_ERROR)}")
    # Output: 500 -> Server Error
    assert classify_response(HttpStatus.SERVER_ERROR) == "Server Error"

    # Traffic light state machine
    class LightState(Enum):
        GREEN = auto()
        YELLOW = auto()
        RED = auto()

    def next_light(state: LightState) -> LightState:
        match state:
            case LightState.GREEN:
                return LightState.YELLOW
            case LightState.YELLOW:
                return LightState.RED
            case LightState.RED:
                return LightState.GREEN

    light = LightState.GREEN
    cycle = [light]
    for _ in range(5):
        light = next_light(light)
        cycle.append(light)
    cycle_names = [l.name for l in cycle]
    print(f"Traffic light cycle: {cycle_names}")
    # Output: Traffic light cycle: ['GREEN', 'YELLOW', 'RED', 'GREEN', 'YELLOW', 'RED']
    assert cycle_names == ["GREEN", "YELLOW", "RED", "GREEN", "YELLOW", "RED"]

    print()

    # --- Section 12: Exercise -- Calculator with match ---
    print("--- Section 12: Exercise -- Calculator with match ---")

    class Op(Enum):
        ADD = auto()
        SUB = auto()
        MUL = auto()
        DIV = auto()
        MOD = auto()
        POW = auto()

    @dataclass
    class Expr:
        left: float
        op: Op
        right: float

    def parse_op(symbol: str) -> Op:
        match symbol:
            case "+":
                return Op.ADD
            case "-":
                return Op.SUB
            case "*":
                return Op.MUL
            case "/":
                return Op.DIV
            case "%":
                return Op.MOD
            case "**":
                return Op.POW
            case _:
                raise ValueError(f"Unknown operator: {symbol}")

    def evaluate(expr: Expr) -> float | str:
        match expr.op:
            case Op.ADD:
                return expr.left + expr.right
            case Op.SUB:
                return expr.left - expr.right
            case Op.MUL:
                return expr.left * expr.right
            case Op.DIV:
                if expr.right == 0:
                    return "Error: Division by zero"
                return expr.left / expr.right
            case Op.MOD:
                if expr.right == 0:
                    return "Error: Division by zero"
                return expr.left % expr.right
            case Op.POW:
                return expr.left ** expr.right

    def calc(expression: str) -> float | str:
        parts = expression.split()
        match parts:
            case [left, "**", right]:
                return evaluate(Expr(float(left), Op.POW, float(right)))
            case [left, op, right]:
                return evaluate(Expr(float(left), parse_op(op), float(right)))
            case _:
                return f"Error: Invalid expression: {expression}"

    result = calc("10 + 5")
    print(f"10 + 5 = {result}")
    # Output: 10 + 5 = 15.0
    assert result == 15.0

    result = calc("20 / 4")
    print(f"20 / 4 = {result}")
    # Output: 20 / 4 = 5.0
    assert result == 5.0

    result = calc("3 * 7")
    print(f"3 * 7 = {result}")
    # Output: 3 * 7 = 21.0
    assert result == 21.0

    result = calc("10 - 3")
    print(f"10 - 3 = {result}")
    # Output: 10 - 3 = 7.0
    assert result == 7.0

    result = calc("10 % 3")
    print(f"10 % 3 = {result}")
    # Output: 10 % 3 = 1.0
    assert result == 1.0

    result = calc("2 ** 8")
    print(f"2 ** 8 = {result}")
    # Output: 2 ** 8 = 256.0
    assert result == 256.0

    result = calc("5 / 0")
    print(f"5 / 0 = {result}")
    # Output: 5 / 0 = Error: Division by zero
    assert result == "Error: Division by zero"

    print()

    # --- Section 13: Exercise -- Traffic light state machine with durations ---
    print("--- Section 13: Exercise -- Traffic Light with Durations ---")

    DURATIONS = {
        LightState.GREEN: 30,
        LightState.YELLOW: 5,
        LightState.RED: 20,
    }

    @dataclass
    class TrafficLight:
        state: LightState
        timer: int

        def tick(self) -> "TrafficLight":
            """Advance the traffic light by one tick."""
            if self.timer > 1:
                return TrafficLight(self.state, self.timer - 1)
            # Timer expired -- transition to next state
            new_state = next_light(self.state)
            return TrafficLight(new_state, DURATIONS[new_state])

        def __str__(self) -> str:
            return f"{self.state.name} ({self.timer}s remaining)"

    tl = TrafficLight(LightState.GREEN, 30)
    print(f"Start: {tl}")
    # Output: Start: GREEN (30s remaining)
    assert tl.state == LightState.GREEN
    assert tl.timer == 30

    # Fast-forward through GREEN
    for _ in range(30):
        tl = tl.tick()
    print(f"After 30 ticks: {tl}")
    # Output: After 30 ticks: YELLOW (5s remaining)
    assert tl.state == LightState.YELLOW
    assert tl.timer == 5

    # Fast-forward through YELLOW
    for _ in range(5):
        tl = tl.tick()
    print(f"After 5 more ticks: {tl}")
    # Output: After 5 more ticks: RED (20s remaining)
    assert tl.state == LightState.RED
    assert tl.timer == 20

    # Fast-forward through RED
    for _ in range(20):
        tl = tl.tick()
    print(f"After 20 more ticks: {tl}")
    # Output: After 20 more ticks: GREEN (30s remaining)
    assert tl.state == LightState.GREEN
    assert tl.timer == 30

    # Partial tick
    tl_mid = TrafficLight(LightState.GREEN, 30)
    for _ in range(10):
        tl_mid = tl_mid.tick()
    print(f"After 10 ticks of GREEN: {tl_mid}")
    # Output: After 10 ticks of GREEN: GREEN (20s remaining)
    assert tl_mid.state == LightState.GREEN
    assert tl_mid.timer == 20

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
