import copy
import dataclasses
from collections import defaultdict

FluidElement = list[str, int]
BottleState = list[FluidElement]
FluidCombineGameState = list[BottleState]


def convert_game_state(game_state: str) -> FluidCombineGameState:
    return [
        [[item[0], int(item[1])] for item in bottle.split(".") if item != ""]
        for bottle in game_state.split("/")
    ]


def bottle_amount(bottle: BottleState) -> int:
    return sum([item[1] for item in bottle])


SAMPLE_GAME_STATES: list[FluidCombineGameState] = [
    convert_game_state("D1.C1.B1.A1/A1.D1.E2/F1.A1.E1.B1/E2/C1.B1/C1.A1/F1.E1.F1.B1/E2.C1.D1/D1.F1/"),
    convert_game_state("A1.B1/B3/A3"),
    convert_game_state("A1.B1.C1/A3/B3/C3"),
    convert_game_state("A1/B2/C3"),
    convert_game_state("A3/A3"),
    convert_game_state(
        "R1.H1.O1.B1/R1.P1.D1.H1/R2.G1.B1/O1.L1.S1.G1/H1.D1.L1.S1/O1.H1.D1.G1/O1.B1.L1.S1/P1.S1.G1.L1/P1.D1.B1.P1//"),
    convert_game_state("L1.O2.S1/R1.L1.P1.D1/O1.P1.L1.B1/R1.S1.D1.B1/S1.D1.B1.O1/S1.G1.R1.P1/B1.H1.L1.H1/G1.H2.G1/D1.G1.P1.R1//"),
    convert_game_state("G1.R1.H1.L1/B1.L1.H1.G1/D1.B1.S1.L1/S1.R1.D1.S1/G1.D1.S1.G1/D1.B1.R1.H1/H1.R1.L1.B1//"),
    convert_game_state("H1.O1.D1.H1/S1.D1.S1.B1/P2.D2/R1.B1.G1.L1/B1.P1.H2/B1.G1.O1.L1/R1.S1.R1.L1/L1.O1.P1.S1/O1.G1.R1.G1//") # 100
]


@dataclasses.dataclass
class PourAction:
    bottle_from: int
    bottle_to: int

    def __repr__(self):
        return f"{self.bottle_from} -> {self.bottle_to}"


class FluidCombineGame:
    def __init__(self, initial_state: FluidCombineGameState, bottle_size: int = 4):
        self.state = initial_state
        self.bottle_size = bottle_size

    def pprint(self):
        for i, bottle in enumerate(self.state):
            print(f"#{i}\t", end="")
            bottle_amount_ = 0
            for fluid_type, amount in bottle:
                print(fluid_type * amount, end="")
                bottle_amount_ += amount
            print("-" * (self.bottle_size - bottle_amount_))

    def is_finished(self):
        def is_bottle_pure(bottle: BottleState):
            return len(bottle) <= 1

        def bottle_type(bottle: BottleState):
            return bottle[0][0] if len(bottle) > 0 else None

        bottle_types = list(filter(lambda x: x is not None, (bottle_type(bottle) for bottle in self.state)))

        return all(is_bottle_pure(bottle) for bottle in self.state)# and len(bottle_types) == len(set(bottle_types))

    def do(self, pour_action: PourAction):
        assert 0 <= pour_action.bottle_from < len(self.state), \
            f"Origin bottle id is invalid. (id={pour_action.bottle_from!r})"
        assert 0 <= pour_action.bottle_to < len(self.state), \
            f"Target bottle id is invalid. (id={pour_action.bottle_to!r})"

        assert self.state[pour_action.bottle_from], \
            f"Origin bottle is empty. (id={pour_action.bottle_from!r})"

        if self.state[pour_action.bottle_to]:
            fluid_from = self.state[pour_action.bottle_from][-1]
            fluid_to = self.state[pour_action.bottle_to][-1]

            origin_fluid_type = fluid_from[0]
            target_fluid_type = fluid_to[0]
            assert origin_fluid_type == target_fluid_type, \
                f"Target bottle can only accept fluid type of origin bottle. " \
                f"({origin_fluid_type!r} != {target_fluid_type!r})"

            from_fullness = bottle_amount(self.state[pour_action.bottle_to])

            # noinspection PyTypeChecker
            if from_fullness + fluid_from[1] > self.bottle_size:
                poured_amount = self.bottle_size - from_fullness
                self.state[pour_action.bottle_from][-1][1] -= poured_amount
                self.state[pour_action.bottle_to][-1][1] += poured_amount
            else:
                self.state[pour_action.bottle_to][-1][1] += fluid_from[1]
                self.state[pour_action.bottle_from].pop()

        else:
            self.state[pour_action.bottle_to].append(
                self.state[pour_action.bottle_from].pop()
            )

    def is_possible(self):
        fluid_types = defaultdict(int)

        for bottle in self.state:
            for fluid_type, amount in bottle:
                if amount > self.bottle_size:
                    return "Too much fluid in a bottle."

                fluid_types[fluid_type] += amount

        for fluid_type, amount in fluid_types.items():
            if amount % self.bottle_size != 0:
                return f"Fluid type {fluid_type!r} has an invalid amount of fluid: {amount}"

        return "maybe possible"

    def get_possibilities(self):
        possibilities = []
        for bottle_from in range(len(self.state)):
            for bottle_to in range(len(self.state)):
                if bottle_from == bottle_to:
                    continue
                if not self.state[bottle_from]:
                    continue
                if self.state[bottle_to] and self.state[bottle_to][-1][0] != self.state[bottle_from][-1][0]:
                    continue
                possibilities.append(PourAction(bottle_from, bottle_to))
        return possibilities

    def solve(self):
        already_seen = set()

        def solve_recursive(game: FluidCombineGame, history: list[PourAction], max_depth: int = 37):
            if max_depth <= 0:
                return None

            game_hash = str(list(sorted(game.state)))
            if game_hash in already_seen:
                return None
            already_seen.add(game_hash)

            if game.is_finished():
                return history

            for action in game.get_possibilities():
                new_game = FluidCombineGame(copy.deepcopy(game.state), game.bottle_size)
                try:
                    new_game.do(action)
                except AssertionError as e:
                    continue
                result = solve_recursive(new_game, history + [action], max_depth - 1)
                if result:
                    return result

        return solve_recursive(self, [])


def main():
    game = FluidCombineGame(SAMPLE_GAME_STATES[-1])
    game.pprint()
    print(game.is_possible())
    # print(game.get_possibilities())
    print(game.solve())


if __name__ == '__main__':
    main()
