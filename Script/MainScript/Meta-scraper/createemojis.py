import json
import emoji

def generate_emoji_json():
    # Get the emoji list from the emoji package
    emoji_list = emoji.EMOJI_DATA

    # Prepare a list to hold emoji data
    emoji_data = []

    # Iterate over emoji data
    for code, details in emoji_list.items():
        # Add unicode and name to the list
        emoji_data.append({
            "unicode": code,
            "name": details.get('name', 'Unknown Emoji')
        })

    # Save to emoji.json
    with open('emoji.json', 'w', encoding='utf-8') as f:
        json.dump(emoji_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    generate_emoji_json()
