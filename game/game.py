import requests
import time

# Define the endpoints
BASE_URL = "https://ads-backend-4ho2.onrender.com/api/games"
GET_URL = f"{BASE_URL}/current-game/"
POST_URL = f"{BASE_URL}/play-game/"

# Add your Bearer token here
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM4MDM0OTAxLCJpYXQiOjE3MzgwMzM2OTYsImp0aSI6IjI3ZWMzZjYyNDAxYjQyZTA5NDg2ZjA4ZjRlZTk0ZDZmIiwidXNlcl9pZCI6Mn0.PJgh7Oi-F7aTPwx-3P3zVvK6Xc4OyzqQn2KTJ8h4dGw"

# Headers with Authorization token
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Send a GET request
def fetch_current_game():
    try:
        response = requests.get(GET_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("GET Response:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error fetching current game:", e)
        return None

# Step 2: Send a POST request
def play_game():
    payload = {
        "rating_score": 4,
        "comment": ""
    }
    try:
        response = requests.post(POST_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("POST Response:", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error playing game:", e)
        return None

# Main script execution
if __name__ == "__main__":
    for i in range(30):  # Loop 30 times
        print(f"Iteration {i + 1}/30")
        print("Fetching current game details...")
        current_game = fetch_current_game()
        if current_game:
            print("Playing game...")
            play_game()
        time.sleep(1)  # Optional: Add delay between iterations to avoid overwhelming the server
