import requests
import asyncio  # Required for the asynchronous telegram bot library
from tqdm import tqdm
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURATION: PASTE YOUR TELEGRAM DETAILS HERE ---
BOT_TOKEN = "8418721690:AAFB4pj29xxsAfgMGa32cI20GsRFi0mnCeM"
CHAT_ID = "6967887832"
# ---------------------------------------------------------

BASE_URL = "https://pokeapi.co/api/v2/"

def escape_markdown_v2(text: str) -> str:
    # Escape characters as required by Telegram MarkdownV2 except inside code blocks
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def escape_telegram_message(text: str) -> str:
    """
    Escapes all special characters for MarkdownV2 except those inside code blocks (``````).
    Splits text by code blocks and escapes only outside the code blocks.
    """
    parts = text.split('```')
    for i in range(len(parts)):
        # Escape every non-code block part (even indexes)
        if i % 2 == 0:
            parts[i] = escape_markdown_v2(parts[i])
        # Leave code block parts (odd indexes) untouched
    return '```'.join(parts)

async def send_long_telegram_message(bot, chat_id, text):
    max_length = 4096
    if len(text) <= max_length:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='MarkdownV2')
        return

    parts = []
    while len(text) > 0:
        if len(text) > max_length:
            part = text[:max_length]
            last_newline = part.rfind('\n')
            if last_newline != -1:
                parts.append(text[:last_newline])
                text = text[last_newline+1:]
            else:
                parts.append(text[:max_length])
                text = text[max_length:]
        else:
            parts.append(text)
            break

    for part in parts:
        await bot.send_message(chat_id=chat_id, text=part, parse_mode='MarkdownV2')

async def find_and_notify_pokemon():
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

            if len(data['types']) == 1:
                speed = next((s['base_stat'] for s in data['stats'] if s['stat']['name'] == 'speed'), None)
                if speed is not None and speed <= 70:
                    qualifying_pokemon.append({
                        "name": data['name'].capitalize(),
                        "type": data['types'][0]['type']['name'].capitalize(),
                        "speed": speed
                    })
        except requests.exceptions.RequestException:
            continue

    qualifying_pokemon.sort(key=lambda p: p['name'])

    # Console output
    console_output = []
    header_line_console = f"Found {len(qualifying_pokemon)} single-type Pokémon with speed <= 70:"
    console_output.append("\n" + "="*60)
    console_output.append(header_line_console)

    if qualifying_pokemon:
        for p in qualifying_pokemon:
            console_line = f"- {p['name']:<15} (Type: {p['type']:<10} | Speed: {p['speed']})"
            console_output.append(console_line)
    else:
        console_output.append("No Pokémon found that match the criteria.")

    console_output.append("="*60)
    print("\n".join(console_output))

    # Telegram output (with code block for monospaced alignment)
    telegram_output = []
    telegram_output.append(f"*Found {len(qualifying_pokemon)} single-type Pokémon with speed <= 70:*")
    if qualifying_pokemon:
        telegram_output.append("```")
        for p in qualifying_pokemon:
            line = f"{p['name']:<15} | {p['type']:<10} | Speed: {p['speed']}"
            telegram_output.append(line)
        telegram_output.append("```")
    else:
        telegram_output.append("No Pokémon found that match the criteria.")

    final_message = "\n".join(telegram_output)
    # Escape message except inside code blocks
    final_message = escape_telegram_message(final_message)

    if BOT_TOKEN == "YOUR_BOT_TOKEN" or CHAT_ID == "YOUR_CHAT_ID":
        print("\nTelegram credentials are not set. Skipping notification.")
        return

    print("\nSending list to your Telegram bot...")
    try:
        bot = Bot(token=BOT_TOKEN)
        await send_long_telegram_message(bot, CHAT_ID, final_message)
        print("Successfully sent!")
    except TelegramError as e:
        print(f"Error sending message to Telegram: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the Telegram process: {e}")

if __name__ == "__main__":
    asyncio.run(find_and_notify_pokemon())
        
