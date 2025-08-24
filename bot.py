import requests
import asyncio
from tqdm import tqdm
from telegram import Bot
from telegram.error import TelegramError

# --- CONFIGURATION: PASTE YOUR TELEGRAM DETAILS HERE ---
BOT_TOKEN = "8418721690:AAFB4pj29xxsAfgMGa32cI20GsRFi0mnCeM"
CHAT_ID = "6967887832"
# ---------------------------------------------------------

BASE_URL = "https://pokeapi.co/api/v2/"

async def send_long_telegram_message(bot, chat_id, text):
    max_length = 4096
    if len(text) <= max_length:
        await bot.send_message(chat_id=chat_id, text=text)
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
        await bot.send_message(chat_id=chat_id, text=part)

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

            # Get stats
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            speed = stats.get("speed")
            spa = stats.get("special-attack")

            # ✅ Conditions:
            # - Speed <= 130
            # - Special Attack is the highest stat
            if speed is not None and speed <= 130:
                highest_stat_name = max(stats, key=stats.get)
                if highest_stat_name == "special-attack":
                    qualifying_pokemon.append({
                        "name": data['name'].capitalize(),
                        "types": [t['type']['name'].capitalize() for t in data['types']],  # multiple types allowed
                        "speed": speed,
                        "special_attack": spa
                    })
        except requests.exceptions.RequestException:
            continue

    qualifying_pokemon.sort(key=lambda p: p['name'])

    # Console output
    console_output = []
    header_line_console = f"Found {len(qualifying_pokemon)} Pokémon (any type count) with Special Attack as highest stat and Speed <= 130:"
    console_output.append("\n" + "="*60)
    console_output.append(header_line_console)

    if qualifying_pokemon:
        for p in qualifying_pokemon:
            types_str = "/".join(p['types'])
            console_line = f"- {p['name']:<15} (Types: {types_str:<15} | Speed: {p['speed']}, SpA: {p['special_attack']})"
            console_output.append(console_line)
    else:
        console_output.append("No Pokémon found that match the criteria.")

    console_output.append("="*60)
    print("\n".join(console_output))

    # Telegram output
    telegram_output = []
    telegram_output.append(f"Found {len(qualifying_pokemon)} Pokémon (any type count) with Special Attack as highest stat and Speed <= 130:")
    telegram_output.append("="*60)
    if qualifying_pokemon:
        for p in qualifying_pokemon:
            types_str = "/".join(p['types'])
            line = f"- {p['name']:<15} (Types: {types_str:<15} | Speed: {p['speed']}, SpA: {p['special_attack']})"
            telegram_output.append(line)
    else:
        telegram_output.append("No Pokémon found that match the criteria.")
    telegram_output.append("="*60)

    final_message = "\n".join(telegram_output)

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
    
