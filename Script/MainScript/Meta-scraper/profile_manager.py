import json
import os

# Define the path to the profile data file
PROFILE_FILE = 'profiles.json'

# Helper function to load profiles from a file
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, 'r') as file:
        return json.load(file)

# Helper function to save profiles to a file
def save_profiles(profiles):
    with open(PROFILE_FILE, 'w') as file:
        json.dump(profiles, file, indent=4)

def create_profile(username, password):
    """
    Create a new user profile.

    :param username: Username for the profile.
    :param password: Password for the profile.
    :return: Success message or error message.
    """
    profiles = load_profiles()
    if username in profiles:
        return "Profile already exists."
    
    profiles[username] = password
    save_profiles(profiles)
    return "Profile created successfully."

def login(username, password):
    """
    Log in to a user profile.

    :param username: Username for the profile.
    :param password: Password for the profile.
    :return: Success message or error message.
    """
    profiles = load_profiles()
    if username not in profiles:
        return "Profile does not exist."
    
    if profiles[username] != password:
        return "Incorrect password."
    
    return "Login successful."

def delete_profile(username):
    """
    Delete a user profile.

    :param username: Username of the profile to delete.
    :return: Success message or error message.
    """
    profiles = load_profiles()
    if username not in profiles:
        return "Profile does not exist."
    
    del profiles[username]
    save_profiles(profiles)
    return "Profile deleted successfully."
