import pytest

from meal_max.models.kitchen_model import Meal
from meal_max.models.battle_model import BattleModel


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

"""Fixtures providing sample meals for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="LOW")

@pytest.fixture
def sample_meal2():
    return Meal(id=2, meal="Ramen", cuisine="Japanese", price=15.0, difficulty="HIGH")

@pytest.fixture
def sample_battle_combatants(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]


##################################################
    # Score Calculation Test Cases
##################################################

def test_get_battle_score_low_difficulty(battle_model, sample_meal1):
    """Test that get_battle_score calculates correctly for LOW difficulty."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 2
    assert score == expected_score

def test_get_battle_score_high_difficulty(battle_model, sample_meal2):
    """Test that get_battle_score calculates correctly for HIGH difficulty."""
    score = battle_model.get_battle_score(sample_meal2)
    expected_score = (sample_meal2.price * len(sample_meal2.cuisine)) - 1
    assert score == expected_score

def test_get_battle_score_low_price(battle_model):
    """Test get_battle_score with a meal that has a very low price."""
    cheap_meal = Meal(id=3, meal="Salad", cuisine="American", price=0.5, difficulty="LOW")
    score = battle_model.get_battle_score(cheap_meal)
    expected_score = (cheap_meal.price * len(cheap_meal.cuisine)) - 3
    assert score == expected_score

def test_get_battle_score_unusual_cuisine(battle_model):
    """Test get_battle_score with a meal that has an unusual cuisine name length."""
    unusual_meal = Meal(id=4, meal="Exotic Dish", cuisine="Fusion", price=20.0, difficulty="HIGH")
    score = battle_model.get_battle_score(unusual_meal)
    expected_score = (unusual_meal.price * len(unusual_meal.cuisine)) - 1
    assert score == expected_score

##################################################
    # Combatant Management Test Cases (Add and Deleting)
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a single combatant to the BattleModel."""
    battle_model.prep_combatant(sample_meal1)
    combatants = battle_model.get_combatants()
    assert len(combatants) == 1
    assert combatants[0].meal == "Pizza"

def test_prep_two_combatants(battle_model, sample_battle_combatants):
    """Test adding two combatants to the BattleModel."""
    for meal in sample_battle_combatants:
        battle_model.prep_combatant(meal)
    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == "Pizza"
    assert combatants[1].meal == "Ramen"

def test_prep_combatant_over_capacity(battle_model, sample_battle_combatants, sample_meal1):
    """Test that adding more than two combatants raises a ValueError."""
    for meal in sample_battle_combatants:
        battle_model.prep_combatant(meal)
    with pytest.raises(ValueError):
        battle_model.prep_combatant(sample_meal1)

def test_clear_combatants(battle_model, sample_battle_combatants):
    """Test that clearing combatants works as expected."""
    for meal in sample_battle_combatants:
        battle_model.prep_combatant(meal)
    battle_model.clear_combatants()
    assert battle_model.get_combatants() == []

def test_battle_with_two_combatants(battle_model, sample_battle_combatants, mocker):
    """Test a battle between two combatants and validate the winner."""
    for meal in sample_battle_combatants:
        battle_model.prep_combatant(meal)
    mocker.patch("meal_max.models.battle_model.get_random", return_value=0.1)
    
    winner = battle_model.battle()
    assert winner in ["Pizza", "Ramen"]  # Winner should be one of the combatants
    assert len(battle_model.get_combatants()) == 1  # Only the winner remains

def test_battle_not_enough_combatants(battle_model, sample_meal1):
    """Test that battle raises a ValueError if there aren't enough combatants."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError):
        battle_model.battle()

def test_battle_logs_winner(battle_model, sample_battle_combatants, mocker):
    """Test that the battle logs the winner as expected."""
    for meal in sample_battle_combatants:
        battle_model.prep_combatant(meal)
    mocker.patch("meal_max.models.battle_model.get_random", return_value=0.1)
    mock_log = mocker.patch("meal_max.models.battle_model.logger.info")

    winner = battle_model.battle()
    assert winner in ["Pizza", "Ramen"]
    assert any("The winner is:" in call[0][0] for call in mock_log.call_args_list)
