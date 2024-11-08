from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the meals table."""
    
    # Call the function to create a new meal
    create_meal(meal="Spaghetti", cuisine="Italian", price=12.99, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert that the arguments passed to the query are correct
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Spaghetti", "Italian", 12.99, "MED")
    assert actual_arguments == expected_arguments, f"Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal name (should raise an error)."""

    # Simulate a duplicate meal name by raising an IntegrityError
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with the specific message
    with pytest.raises(ValueError, match="Meal with name 'Spaghetti' already exists"):
        create_meal(meal="Spaghetti", cuisine="Italian", price=12.99, difficulty="MED")

# Test: Invalid price input (e.g., negative price)
def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price."""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -12.99. Price must be a positive number."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=-12.99, difficulty="MED")

    # Attempt to create a meal with a non-numeric price
    with pytest.raises(ValueError, match="Invalid price: invalid. Price must be a positive number."):
        create_meal(meal="Spaghetti", cuisine="Italian", price="invalid", difficulty="MED")

# Test: Invalid difficulty input (e.g., incorrect difficulty level)
def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty level."""
    
    # Attempt to create a meal with an invalid difficulty level
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Spaghetti", cuisine="Italian", price=12.99, difficulty="EASY")

# Test: Deleting a meal that exists
def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the meals table by meal ID."""

    # Simulate the meal exists (id = 1, not deleted)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Ensure the correct SQL queries were executed
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access the calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the SQL queries match the expected ones
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the arguments used for the SQL queries are correct
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"Expected {expected_update_args}, got {actual_update_args}."

# Test: Deleting a non-existent meal (should raise an error)
def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

# Test: Deleting a meal that has already been marked as deleted
def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has already been deleted"):
        delete_meal(999)

# Test: Clearing the meals table
def test_clear_meals(mock_cursor, mocker):
    """Test clearing all meals in the meals table."""

    # Mock the file reading for the create table script
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="CREATE TABLE statement"))

    # Call the clear_meals function
    clear_meals()

    # Ensure the file was opened correctly
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Ensure the SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Get Meal
#
######################################################

def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal by its name."""

    # Simulate meal data (name = "Spaghetti")
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 12.99, "Medium", False)

    # Call the function and check the result
    result = get_meal_by_name("Spaghetti")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Spaghetti", "Italian", 12.99, "Medium")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_meal_by_name_not_found(mock_cursor):
    """Test retrieving a meal by name when the meal does not exist."""

    # Simulate that the meal is not found (fetchone returns None)
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name Sushi not found"):
        get_meal_by_name("Sushi")

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal by its ID."""

    # Simulate meal data (id = 1)
    mock_cursor.fetchone.return_value = (1, "Spaghetti", "Italian", 12.99, "Medium", False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Spaghetti", "Italian", 12.99, "Medium")

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_meal_by_id_not_found(mock_cursor):
    """Test retrieving a meal by ID when the meal does not exist."""

    # Simulate that the meal is not found (fetchone returns None)
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted(mock_cursor):
    """Test retrieving a meal by ID when the meal is marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted (id = 1)
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when the meal is marked as deleted
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)


def test_get_leaderboard(mock_cursor):
    """Test retrieving the meal leaderboard sorted by wins."""

    # Simulate meals data
    mock_cursor.fetchall.return_value = [
        (1, "Spaghetti", "Italian", 12.99, "Medium", 10, 7, 0.7),
        (2, "Burger", "American", 8.99, "Easy", 15, 12, 0.8),
        (3, "Sushi", "Japanese", 15.99, "Hard", 5, 3, 0.6)
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard("wins")

    # Expected result based on the simulated fetchall return value
    expected_result = [
        {'id': 2, 'meal': "Burger", 'cuisine': "American", 'price': 8.99, 'difficulty': "Easy", 'battles': 15, 'wins': 12, 'win_pct': 80.0},
        {'id': 1, 'meal': "Spaghetti", 'cuisine': "Italian", 'price': 12.99, 'difficulty': "Medium", 'battles': 10, 'wins': 7, 'win_pct': 70.0},
        {'id': 3, 'meal': "Sushi", 'cuisine': "Japanese", 'price': 15.99, 'difficulty': "Hard", 'battles': 5, 'wins': 3, 'win_pct': 60.0}
    ]

    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort(mock_cursor):
    """Test invalid sort_by parameter in get_leaderboard."""

    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard("invalid")

######################################################
#
#    Update Meal
#
######################################################

def test_update_meal_stats_win(mock_cursor):
    """Test updating the meal stats with a win."""

    # Simulate meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_meal_stats function with 'win'
    update_meal_stats(1, 'win')

    # Ensure the correct SQL query was executed
    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Ensure the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == expected_arguments, f"Expected {expected_arguments}, got {actual_arguments}"

def test_update_meal_stats_meal_not_found(mock_cursor):
    """Test error when trying to update stats for a meal that doesn't exist."""

    # Simulate that the meal is not found (fetchone returns None)
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        update_meal_stats(1, 'win')

    # Ensure the select query ran to check for the meal's existence
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test updating the meal stats with an invalid result."""

    # Expect a ValueError for invalid result
    with pytest.raises(ValueError, match="Invalid result: invalid. Expected 'win' or 'loss'."):
        update_meal_stats(1, "invalid")

