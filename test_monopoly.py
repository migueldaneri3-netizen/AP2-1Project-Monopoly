import os
import pytest
import glob
from board import Board
from card import build_card, MoveCard
from player import Player
import const as c
from tile import Property, Street, Utility

# FIXTURES


@pytest.fixture
def board() -> Board:
    """
    Creates a completely real board, loading actual JSONs and generating real SVGs.
    It runs before every single test to ensure a fresh game state.
    """
    # 1. Create the 'frames' directory if it doesn't exist
    os.makedirs("frames", exist_ok=True)

    # 2. Clean up the old SVGs inside that specific folder
    for old_frame in glob.glob("frames/frame_*.svg"):
        try:
            os.remove(old_frame)
        except OSError:
            pass

    board = Board(
        tiles_json_path="data/tiles.json",
        chance_json_path="data/chance.json",
        community_chest_json_path="data/community-chest.json",
        players_json_path="data/players.json",
        num_players=4,
    )

    return board


def mock_handle_normal_roll(
    player: Player, doubles_count: int, board: Board
) -> tuple[bool, int]:
    """
    Executes a standard movement when the dice have been set.
    Returns a tuple: (is_turn_still_active, updated_doubles_count).
    """
    d1, d2 = board.dice
    total_roll = d1 + d2

    if board.is_double:
        doubles_count += 1
        if doubles_count == 3:
            player.go_to_jail()
            return False, doubles_count

        player.move(total_roll)

        if player.is_in_jail:
            return False, doubles_count
        if player.money < 0:
            return False, doubles_count

        return True, doubles_count  # Roll again
    player.move(total_roll)
    return False, doubles_count


def mock_handle_jail_logic(player: Player, board: Board) -> bool:
    """Executes jail rules with a preset dice roll.
    Returns True if the player escapes cleanly and takes a normal turn."""

    if player.use_get_out_of_jail_card():
        return True

    # Roll for escape
    d1, d2 = board.dice
    total_roll = d1 + d2

    if board.is_double:
        player.release_from_jail()
        player.move(total_roll)

    else:
        player.decrement_jail_turn()
        if player.turns_in_prison == 0:
            player.release_from_jail()
            player.move(total_roll)

    return False


#  TESTS

# BOARD SETUP AND INITIALIZATION


def test_board_initialization(board: Board):
    assert len(board.tiles) == 40
    assert len(board.players) == 4
    assert board._current_player_index == 0  # type: ignore
    assert board._current_dice == (1, 1)  # type: ignore


def test_tiles_have_correct_types(board: Board):
    assert board.tiles[1].type == "property"
    assert board.tiles[5].type == "station"
    assert board.tiles[12].type == "utility"
    assert board.tiles[4].type == "tax"
    assert board.tiles[20].type == "special"
    assert board.tiles[30].type == "special"


def test_players_have_strategies(board: Board):
    for player in board.players:
        assert player.strategy is not None


def test_players_loaded_with_correct_attributes(board: Board):
    player = board.players[0]
    assert player.name == "Jordi"
    assert player.money == 1500
    assert player.position == 0
    assert player.is_in_jail is False
    assert player.get_out_of_jail_free_cards == 0
    assert player.owned_properties == []


# PLAYER MOVEMENT & BASIC MECHANICS


def test_player_initial_state(board: Board):
    player = board.players[0]
    assert player.position == 0
    assert player.money == 1500
    assert player.is_in_jail is False
    assert player.turns_in_prison == 0


def test_simple_movement(board: Board):
    player = board.players[0]
    player.move(5)
    assert player.position == 5


def test_normal_roll(board: Board):
    player = board.players[0]

    board._handle_normal_roll(player, 0)  # type: ignore
    assert player.position != 0  # Should have moved


def test_brief_play(board: Board):
    c.MAX_TURNS = 2
    player = board.players[0]
    initial_position = player.position

    board.play()

    assert player.position != initial_position  # Should have moved


# STRATEGY


def test_smart_strategy_refuses_expensive_purchase_when_poor(board: Board):
    player = board.players[0]
    player._money = 100  # type: ignore

    property_tile: Property = board.tiles[39]  # type: ignore

    decision = player.strategy.should_buy_property(player, property_tile)

    assert decision is False


def test_smart_strategy_accepts_affordable_purchase(board: Board):

    player = board.players[0]
    player._money = 1000  # type: ignore

    property_tile: Property = board.tiles[39]  # type: ignore

    decision = player.strategy.should_buy_property(player, property_tile)

    assert decision is True


def test_smart_strategy_decides_to_build(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    player._money = 1500  # type: ignore
    player.strategy.manage_portfolio(player)

    assert s1.houses > 0 or s2.houses > 0


def test_smart_strategy_decided_to_mortgage(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    player._money = 0  # type: ignore
    player.strategy.manage_portfolio(player)

    assert s1.is_mortgaged or s2.is_mortgaged


def test_simple_strategy_always_buys(board: Board):
    player = board.players[2]
    s1: Street = board.tiles[1]  # type: ignore
    player._money = 60  # type: ignore
    s1.land_on(player)
    assert s1.owner == player


def test_simple_strategy_never_builds(board: Board):
    player = board.players[2]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    player._money = 1500  # type: ignore
    player.strategy.manage_portfolio(player)

    assert s1.houses == 0 and s2.houses == 0


# BOARD MECHANICS


def test_landing_go_gives_200(board: Board):
    player = board.players[0]
    initial_money = player.money

    # Teleport player to the last tile
    player.set_position(39)

    # Move 2 spaces, which crosses GO
    player.move(1)

    assert player.position == 0
    assert player.money == initial_money + 200


def test_passing_go_gives_200(board: Board):
    player = board.players[0]
    initial_money = player.money

    player.set_position(39)

    player.move(11)

    assert player.position == 10
    assert player.money == initial_money + 200


def test_go_to_jail_square_sends_to_jail(board: Board):
    player = board.players[0]
    jail_square = board.tiles[30]  # Go to Jail tile

    jail_square.land_on(player)

    assert player.position == 10
    assert player.is_in_jail is True
    assert player.turns_in_prison == 3


def test_income_tax_payment(board: Board):
    player = board.players[0]
    tax_tile = board.tiles[4]
    initial_money = player.money

    tax_tile.land_on(player)

    assert player.money == initial_money - 200


def test_super_tax_payment(board: Board):

    player = board.players[0]
    super_tax_tile = board.tiles[38]
    initial_money = player.money

    super_tax_tile.land_on(player)

    assert player.money == initial_money - 100


# DOUBLES AND JAIL


def test_doubles_allows_roll_again(board: Board):
    player = board.players[0]

    board._current_dice = (3, 3)  # Mock a double roll #type: ignore

    is_active, doubles_count = mock_handle_normal_roll(player, 0, board)  # type: ignore

    assert is_active is True  # Should be True so the while-loop in play() continues
    assert doubles_count == 1
    assert board.is_double is True


def test_triple_doubles_goes_to_jail(board: Board):

    player = board.players[0]
    board._current_dice = (3, 3)  # Mock a double roll #type: ignore

    assert player.is_in_jail is False
    mock_handle_normal_roll(player, 0, board)  # 1st double
    assert player.is_in_jail is False
    mock_handle_normal_roll(player, 1, board)  # 2nd double
    assert player.is_in_jail is False
    mock_handle_normal_roll(player, 2, board)  # 3rd double should send to jail
    assert player.is_in_jail is True


def test_doubles_takes_out_of_jail(board: Board):
    player = board.players[0]
    player.go_to_jail()
    assert player.is_in_jail
    assert player.turns_in_prison == 3

    board._current_dice = (4, 4)  # Mock a double roll #type: ignore
    gets_normal_turn = mock_handle_jail_logic(player, board)
    assert not player.is_in_jail
    assert (
        gets_normal_turn is False
    )  # The double counts as the escape roll, handled within the function


def test_use_get_out_of_jail_card(board: Board):
    player = board.players[0]
    player.add_get_out_of_jail_free_card()
    player.go_to_jail()

    assert player.is_in_jail
    success = player.use_get_out_of_jail_card()

    assert success is True
    assert not player.is_in_jail
    assert player.get_out_of_jail_free_cards == 0


def test_jail_release_after_3_turns(board: Board):
    board._current_dice = (1, 2)  # Mock a non-double roll #type: ignore
    player: Player = board.players[0]
    player._turns_left_in_prison = 1  # type: ignore
    assert player.is_in_jail is True

    mock_handle_jail_logic(player, board)
    assert player.is_in_jail is False
    assert player.turns_in_prison == 0


def test_collect_rent_while_in_jail(board: Board):
    player = board.players[0]
    player.go_to_jail()

    # Set up a property owned by another player
    other_player = board.players[1]
    property_tile: Property = board.tiles[1]  # type: ignore
    property_tile._owner = player  # type: ignore

    initial_money_player = player.money

    property_tile.land_on(other_player)

    assert player.money == initial_money_player + property_tile.calculate_rent(5)  # type: ignore


# BANKRUPTCY


def test_bankruptcy_frees_properties(board: Board):
    player = board.players[0]
    s1: Property = board.tiles[1]  # type: ignore
    s1.buy(player)

    assert s1.owner == player
    player.declare_bankruptcy(board)

    assert player.is_bankrupt
    assert player.money == 0
    assert len(player.owned_properties) == 0
    assert s1.owner is None  # Property returned to bank
    assert not s1.is_mortgaged


def test_insufficient_funds_bankruptcy(board: Board):
    player = board.players[0]
    player._money = 2  # type: ignore
    property_tile: Property = board.tiles[39]  # type: ignore
    property_tile._rent = 200  # type: ignore
    property_tile._owner = board.players[1]  # type: ignore

    property_tile.land_on(player)

    assert player.money <= 0


def test_unable_to_pay_tax_causes_bankruptcy(board: Board):
    """A player should go bankrupt if they cannot pay tax."""
    player = board.players[0]

    # Drain player's money
    player._money = 50  # type: ignore

    tax_tile = board.tiles[4]

    tax_tile.land_on(player)

    assert player.is_bankrupt is True or player.money < 0


def test_multiple_properties_returned_to_bank_on_bankruptcy(board: Board):
    """All properties owned by a bankrupt player should return to the bank."""
    player = board.players[0]

    properties_to_buy = [1, 3, 6, 8, 9]
    for tile_index in properties_to_buy:
        prop: Property = board.tiles[tile_index]  # type: ignore
        prop.buy(player)

    assert len(player.owned_properties) == len(properties_to_buy)

    player.declare_bankruptcy(board)

    assert len(player.owned_properties) == 0
    for tile_index in properties_to_buy:
        prop: Property = board.tiles[tile_index]  # type: ignore
        assert prop.owner is None


def test_bankrupt_player_loses_get_out_of_jail_cards(board: Board):
    player = board.players[0]

    player.add_get_out_of_jail_free_card()
    player.add_get_out_of_jail_free_card()

    assert player.get_out_of_jail_free_cards == 2

    player.declare_bankruptcy(board)

    assert player.get_out_of_jail_free_cards == 0


def test_player_turn_skips_bankrupt_players(board: Board):
    player = board.players[0]
    player.declare_bankruptcy(board)

    for _ in range(3):
        board._advance_turn()  # type: ignore
        next_player = board._current_player_index  # type: ignore
        assert next_player != 0  # Should skip index 0 since bankrupt


# RENT


def test_paying_rent(board: Board):
    player1 = board.players[0]
    player2 = board.players[1]
    property_tile: Property = board.tiles[1]  # type: ignore

    property_tile._owner = player2  # type: ignore
    player2._money += property_tile.price  # type: ignore

    property_tile.land_on(player1)

    assert player1.money < 1500
    assert player2.money > 1500


def test_having_colour_group_gives_extra_rent(board: Board):
    player1 = board.players[0]

    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player1)
    assert s1.calculate_rent(5) == 2

    s2.buy(player1)
    assert s1.has_monopoly is True
    assert s1.calculate_rent(5) == 4  # Monopoly rent kicks in


def test_rent_multiplier_with_mortgaged_properties(board: Board):
    player1 = board.players[0]
    player2 = board.players[1]

    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player1)
    s2.buy(player1)

    s1.mortgage()
    assert s1.is_mortgaged is True

    initial_money_player1 = player1.money
    s2.land_on(player2)

    assert player1.money == initial_money_player1 + s2.calculate_rent(5)


def test_station_rent_scales(board: Board):
    player = board.players[0]
    st1: Street = board.tiles[5]  # type: ignore
    st2: Street = board.tiles[15]  # type: ignore

    st1.buy(player)
    assert st1.calculate_rent(5) == 25

    st2.buy(player)
    assert st1.calculate_rent(5) == 50


def test_utility_rent_scales(board: Board):
    player = board.players[0]
    u1: Utility = board.tiles[12]  # type: ignore
    u2: Utility = board.tiles[28]  # type: ignore

    u1.buy(player)
    assert u1.calculate_rent(7) == 28  # 7 roll * 4

    u2.buy(player)
    assert u1.calculate_rent(7) == 70  # 7 roll * 10


def test_rent_not_paid_if_mortgaged(board: Board):
    player = board.players[0]
    s1: Property = board.tiles[1]  # type: ignore

    s1.buy(player)
    s1.mortgage()

    player2 = board.players[1]
    p2_initial_money = player2.money

    s1.land_on(player2)
    assert player2.money == p2_initial_money  # Did not pay rent


def test_no_rent_paid_to_self(board: Board):
    player = board.players[0]
    s1: Property = board.tiles[1]  # type: ignore

    s1.buy(player)

    initial_money = player.money
    s1.land_on(player)
    assert player.money == initial_money


# BUILDING AND MORTGAGE


def test_mortgage_and_unmortgage(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s1.buy(player)
    initial_money = player.money

    s1.mortgage()
    assert s1.is_mortgaged is True
    assert player.money == initial_money + s1._mortgage  # type: ignore

    s1.unmortgage()
    assert s1.is_mortgaged is False
    assert player.money == initial_money + s1._mortgage - s1.unmortgage_price  # type: ignore


def test_cant_build_without_colour_group(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    assert s1.can_build_house is False

    s2.buy(player)
    assert s1.can_build_house is True


def test_uniform_building_rule(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    s1.build_house()
    assert s1.houses == 1

    # Cannot build a 2nd house on s1 until s2 also has 1 house
    assert s1.can_build_house is False
    assert s2.can_build_house is True

    s2.build_house()
    assert s1.can_build_house is True  # Uniformity restored


def test_cannot_mortgage_property_with_houses(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    s1.build_house()
    assert s1.can_mortgage is False


def test_hotel_upgrade_requires_four_houses(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    s1.build_house()
    s2.build_house()
    assert s1.can_build_hotel is False

    s1.build_house()
    s2.build_house()
    assert s1.can_build_hotel is False

    s1.build_house()
    s2.build_house()
    assert s1.can_build_hotel is False

    s1.build_house()
    s2.build_house()
    assert s1.can_build_hotel is True


def test_max_building_limit_enforced(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    for _ in range(4):
        s1.build_house()
        s2.build_house()

    s1.build_hotel()
    assert s1.houses == 0
    assert s1.hotels == 1

    assert s1.can_build_hotel is False
    assert s1.can_build_house is False


def test_selling_houses_is_uniform(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    for _ in range(2):
        s1.build_house()
        s2.build_house()
    assert s1.houses == 2 and s2.houses == 2
    s1.sell_house()

    assert s1.can_sell_house is False
    assert s2.can_sell_house is True


def test_selling_hotel_reverts_to_four_houses(board: Board):
    player = board.players[0]
    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    for _ in range(4):
        s1.build_house()
        s2.build_house()

    s1.build_hotel()
    assert s1.hotels == 1

    s1.sell_hotel()
    assert s1.hotels == 0
    assert s1.houses == 4


# LANDING AND BUYING


def test_landing_on_property(board: Board):
    player = board.players[0]
    property_tile = board.tiles[1]
    player.set_position(1)
    property_tile.land_on(player)
    # Property should be available for purchase
    assert property_tile.owner is None or property_tile.owner == player  # type: ignore


def test_buying_property(board: Board):
    player = board.players[0]
    property_tile: Property = board.tiles[1]  # type: ignore
    initial_money = player.money
    property_price = property_tile.price

    property_tile.buy(player)

    assert property_tile.owner == player
    assert player.money == initial_money - property_price


def test_landing_on_free_parking(board: Board):
    player = board.players[0]
    free_parking = board.tiles[20]
    initial_money = player.money

    free_parking.land_on(player)

    assert player.money == initial_money
    assert not player.is_in_jail


def test_card_movement_triggers_pass_go(board: Board):
    player = board.players[0]
    initial_money = player.money

    player.set_position(36)

    card_data: dict[str, int | str] = {
        "id": 1,
        "action": "move_to_position",
        "position": 20,
    }
    move_card: MoveCard = build_card(card_data)  # type: ignore

    move_card._do_execute(player, board)  # type: ignore

    assert player.position == 20
    assert player.money == initial_money + c.GO_SALARY  # Passed GO and collected salary


def test_card_sends_to_jail_does_not_pass_go(board: Board):
    player = board.players[0]
    initial_money = player.money

    # Put player at tile 36. Moving to Jail (tile 10) means index decreases,
    # so we must ensure the pass GO logic isn't accidentally triggered.
    player.set_position(36)

    # Mock a "Go directly to jail" card
    card_data: dict[str, int | str] = {"id": 2, "action": "go_to_jail"}
    jail_card = build_card(card_data)

    jail_card.execute(player, board)

    assert player.position == 10
    assert player.is_in_jail is True
    assert player.money == initial_money  # Ensure money remains unchanged


def test_repairs_card_calculates_correctly(board: Board):
    player = board.players[0]

    s1: Street = board.tiles[1]  # type: ignore
    s2: Street = board.tiles[3]  # type: ignore

    s1.buy(player)
    s2.buy(player)

    s1._houses = 3  # type: ignore
    s1._hotels = 0  # type: ignore
    s2._houses = 0  # type: ignore
    s2._hotels = 1  # type: ignore

    initial_money = player.money

    card_data: dict[str, int | str] = {
        "id": 3,
        "action": "property_repairs",
        "amountPerHouse": 40,
        "amountPerHotel": 115,
    }
    repairs_card = build_card(card_data)

    repairs_card.execute(player, board)

    # Expected cost: (3 houses * $40) + (1 hotel * $115) = $120 + $115 = $235
    expected_cost = 235
    assert player.money == initial_money - expected_cost


# GAME END CONDITIONS


def test_game_ends_when_only_one_player_remains(board: Board):
    player1 = board.players[0]
    player2 = board.players[1]
    player3 = board.players[2]
    player4 = board.players[3]

    player2.declare_bankruptcy(board)
    player3.declare_bankruptcy(board)
    player4.declare_bankruptcy(board)

    assert player1.is_bankrupt is False
    assert player2.is_bankrupt is True
    assert player3.is_bankrupt is True
    assert player4.is_bankrupt is True

    active_players = [p for p in board.players if not p.is_bankrupt]
    assert len(active_players) == 1


def test_winner_is_determined_correctly(board: Board):
    player1 = board.players[0]
    player2 = board.players[1]
    player3 = board.players[2]
    player4 = board.players[3]

    player2.declare_bankruptcy(board)
    player3.declare_bankruptcy(board)
    player4.declare_bankruptcy(board)

    winner = next((p for p in board.players if not p.is_bankrupt), None)
    assert winner == player1


def test_game_ends_after_all_turns_except_one_player_bankrupt(board: Board):
    players = board.players

    # Start with 4 players
    assert len([p for p in players if not p.is_bankrupt]) == 4

    # First bankruptcy
    players[1].declare_bankruptcy(board)
    assert len([p for p in players if not p.is_bankrupt]) == 3

    # Second bankruptcy
    players[2].declare_bankruptcy(board)
    assert len([p for p in players if not p.is_bankrupt]) == 2

    # Third bankruptcy
    players[3].declare_bankruptcy(board)
    assert len([p for p in players if not p.is_bankrupt]) == 1

    # Game should end
    assert players[0].is_bankrupt is False
    assert board._is_game_over(0) is True  # type: ignore
