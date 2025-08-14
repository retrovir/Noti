import requests
import asyncio # Required for the asynchronous telegram bot library
from tqdm import tqdm
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURATION: PASTE YOUR TELEGRAM DETAILS HERE ---
# Replace "YOUR_BOT_TOKEN" with the token you got from @BotFather
BOT_TOKEN = "8418721690:AAFB4pj29xxsAfgMGa32cI20GsRFi0mnCeM" 
# Replace "YOUR_CHAT_ID" with your user ID you got from @userinfobot
CHAT_ID = "6967887832"
# ---------------------------------------------------------

# The base URL for the PokéAPI v2
BASE_URL = "https://pokeapi.co/api/v2/"

async def send_long_telegram_message(bot, chat_id, text):
    """
    Sends a long message by splitting it into chunks if it exceeds Telegram's limit.
    """
    max_length = 4096
    if len(text) <= max_length:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='MarkdownV2')
        return

    parts = []
    while len(text) > 0:
        if len(text) > max_length:
            part = text[:max_length]
            # Find the last newline to avoid cutting a line in the middle
            last_newline = part.rfind('\n')
            if last_newline != -1:
                parts.append(part[:last_newline])
                text = text[last_newline+1:]
            else:
                # If no newline, just split at the max length
                parts.append(part)
                text = text[max_length:]
        else:
            parts.append(text)
            break
            
    for part in parts:
        await bot.send_message(chat_id=chat_id, text=part, parse_mode='MarkdownV2')


async def find_and_notify_pokemon():
    """
    Fetches Pokémon data, filters it, and sends the result to the console 
    and a Telegram bot.
    """
    print("Connecting to the PokéAPI to get the full list of Pokémon...")
    
    try:
        initial_response = requests.get(f"{BASE_URL}pokemon")
        initial_response.raise_for_status()
        count = initial_response.json()['count']

        print(f"Found {count} Pokémon. Fetching details for each...")
        all_pokemon_response = requests.get(f"{BASE_URL}pokemon?limit={count}")
        all_pokemon_response.raise_for_status()
        all_pokemon_list = all_pokemon_response.json()['results']
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to PokéAPI: {e}")
        return

    qualifying_pokemon = []
    for pokemon_info in tqdm(all_pokemon_list, desc="Processing Pokémon"):
        try:
            data = requests.get(pokemon_info['url']).json()

            # Filter 1: Single type
            if len(data['types']) == 1:
                # Filter 2: Speed <= 70
                speed = next((s['base_stat'] for s in data['stats'] if s['stat']['name'] == 'speed'), None)
                
                if speed is not None and speed <= 70:
                    qualifying_pokemon.append({
                        "name": data['name'].capitalize(),
                        "type": data['types'][0]['type']['name'].capitalize(),
                        "speed": speed
                    })
        except requests.exceptions.RequestException:
            continue

    # --- Step 3: Sort the list alphabetically by name ---
    qualifying_pokemon.sort(key=lambda p: p['name'])

    # --- Step 4: Format the output and print to console ---
    console_output = []
    telegram_output = []
    
    header_line_console = f"Found {len(qualifying_pokemon)} single-type Pokémon with speed <= 70:"
    # For Telegram, we escape special characters for MarkdownV2
    header_line_telegram = f"*Found {len(qualifying_pokemon)} single\\-type Pokémon with speed <= 70:*"

    console_output.append("\n" + "="*60)
    console_output.append(header_line_console)
    telegram_output.append(header_line_telegram)

    if qualifying_pokemon:
        # We use a monospace font in Telegram for perfect alignment by wrapping with ```
        telegram_output.append("```") 
        for p in qualifying_pokemon:
            # {:<15} creates a left-aligned string of 15 characters
            console_line = f"- {p['name']:<15} (Type: {p['type']:<10} | Speed: {p['speed']})"
            telegram_line = f"{p['name']:<15} | {p['type']:<10} | Speed: {p['speed']}"
            console_output.append(console_line)
            telegram_output.append(telegram_line)
        telegram_output.append("```")
    else:
        no_results_text = "No Pokémon found that match the criteria."
        console_output.append(no_results_text)
        telegram_output.append(no_results_text)

    console_output.append("="*60)
    
    # Print the formatted list to the console
    print("\n".join(console_output))

    # --- Step 5: Send the list to your Telegram bot ---
    if BOT_TOKEN == "YOUR_BOT_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
        print("\nTelegram credentials are not set. Skipping notification.")
        return

    print("\nSending list to your Telegram bot...")
    try:
        bot = Bot(token=BOT_TOKEN)
        final_message = "\n".join(telegram_output)
        await send_long_telegram_message(bot, CHAT_ID, final_message)
        print("Successfully sent!")
    except TelegramError as e:
        print(f"Error sending message to Telegram: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the Telegram process: {e}")


if __name__ == "__main__":
    # Use asyncio.run() to execute the asynchronous function
    asyncio.run(find_and_notify_pokemon())
                               
