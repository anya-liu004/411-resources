#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:8080/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Meals cleared successfully."
  else
    echo "Failed to clear meals."
    exit 1
  fi
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal, $cuisine, $price, $difficulty)..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

#delete meal by name

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    echo "Meal JSON (ID $meal_id):"
    echo "$response" | jq .
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

#update back to file
get_meal_by_name() {
  #meal_name=Spaghetti Bolognese

  echo "Getting meal by name ( Bolognese)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/Bolognese")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name (Bolognese)."
    echo "Meal JSON (name Bolognese):"
    echo "$response" | jq .
  else
    echo "Failed to get meal by name (Bolognese)."
    exit 1
  fi
}

update_meal_stats() {
  meal_id=$1
  result=$2

  echo "Updating meal stats (ID: $meal_id, Result: $result)..."
  response=$(curl -s -X POST "$BASE_URL/update-meal-stats" -H "Content-Type: application/json" \
    -d "{\"meal_id\":$meal_id, \"result\":\"$result\"}")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal stats updated successfully (ID: $meal_id)."
  else
    echo "Failed to update meal stats (ID: $meal_id)."
    exit 1
  fi
}


############################################################
#
# Battle Management
#
############################################################
clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

get_battle_score() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Getting battle score for combatant ($meal, $cuisine, $price, $difficulty)..."
  response=$(curl -s -X GET "$BASE_URL/get-battle-score" \
    -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle score retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Score JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve battle score."
    exit 1
  fi
}

get_combatants() {
  echo "Retrieving current list of combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}

prep_combatant() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Preparing combatant ($meal, $cuisine, $price, $difficulty)..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" \
    -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant added successfully."
  else
    echo "Failed to add combatant."
    exit 1
  fi
}



######################################################
#
# Leaderboard
#
######################################################

get_leaderboard() {
  echo "Getting leaderboard..."
  response=$(curl -s -X GET "$BASE_URL/get-leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    echo "Leaderboard JSON:"
    echo "$response" | jq .
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}

# Health checks
check_health
check_db

# Clear the meals
clear_meals

# Create meals
create_meal "Bolognese" "Italian" 12.99 "MED"

# Get all meals
get_all_meals

# Test retrieving a meal by ID (replace 1 with a valid meal ID)
get_meal_by_id 1

# Test retrieving a meal by name
get_meal_by_name "Bolognese"

# Test updating meal stats (replace 1 with a valid meal ID and result with 'win' or 'loss')
update_meal_stats 1 "win"

# Get leaderboard
get_leaderboard

# Test deleting a meal by ID
delete_meal_by_id 1

clear_combatants
prep_combatant "udon" 
prep_combatant "vindaloo" 
battle

get_combatants
