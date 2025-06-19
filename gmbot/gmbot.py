import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import os
import re
import signal
import json
import psutil
from datetime import datetime
from a2s import info, players, rules
import socket

# Customs imports
from config import *
from functions.gmod_functions import *

# ========== LOCAL CONFIGURATION ==========
TOKEN='XXXX'


if not os.path.exists(CONFIG_STATUS_DIR):
    os.makedirs(CONFIG_STATUS_DIR)

# ========== FUNCTIONS ==========

def log_action(user: discord.User, action: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        msg = f"[{timestamp}] {user} ({user.id}) -> {action}\n"
        print(msg)
        f.write(msg)



def update_config(game, status):
    with open(f"{CONFIG_STATUS_DIR}/{game}.json", "w") as f:
        json.dump({"status": status}, f, indent=4)



async def set_status(_=None):
    up_lines = []
    down_lines = []
    for game in GAMES_CONFIG.keys():
        proc = RUNNING_PROCS.get(game)
        is_up = False
        if proc is True:
            is_up = True
        elif proc:
            # If proc is a Popen object, check poll
            if hasattr(proc, "poll"):
                is_up = proc.poll() is None
            # If proc is a PID (int), check with psutil
            elif isinstance(proc, int):
                try:
                    p = psutil.Process(proc)
                    is_up = p.is_running() and p.status() != psutil.STATUS_ZOMBIE
                except psutil.NoSuchProcess:
                    is_up = False
            # If proc is a psutil.Process object
            elif hasattr(proc, "is_running"):
                is_up = proc.is_running()
        if is_up:
            up_lines.append(f"{game.capitalize()}:🟢")
        else:
            down_lines.append(f"{game.capitalize()}:🔴")
    status_lines = up_lines + down_lines
    status_text = " | ".join(status_lines)
    if len(status_text) > 128:
        status_text = status_text[:125] + "..."
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=status_text))



def has_required_role(interaction: discord.Interaction, role_name):
    return any(role.name == role_name for role in interaction.user.roles)



def find_server_process_by_name(proc_name):
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == proc_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def load_start_maps():
    with open(START_MAPS_FILE, "r") as f:
        return json.load(f)

def save_start_maps(maps):
    with open(START_MAPS_FILE, "w") as f:
        json.dump(maps, f, indent=4)



# ========== DISCORD BOT SETUP ==========
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)



@client.event
async def on_ready():
    print(f"[+] Logged in as {client.user}")
    # Clear previous RUNNING_PROCS
    RUNNING_PROCS.clear()
    for game, config in GAMES_CONFIG.items():
        proc_name = config.get("server_process_name")
        port = str(config["command_args"][config["command_args"].index("-port") + 1]) if "-port" in config["command_args"] else None
        found = False
        for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
            try:
                if proc.info['name'] == proc_name and port and f"-port" in proc.info['cmdline'] and port in proc.info['cmdline']:
                    RUNNING_PROCS[game] = proc.info['pid']
                    found = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, IndexError, KeyError):
                continue
        if not found and game in RUNNING_PROCS:
            del RUNNING_PROCS[game]
    await set_status()
    await client.tree.sync()


@client.tree.command(name="help", description="Show information about available commands")
async def help_command(interaction: discord.Interaction):
    help_lines = ["**Available Commands:**\n"]
    for cmd in client.tree.get_commands():
        # Only show top-level commands (not subcommands)
        if isinstance(cmd, app_commands.Command):
            desc = cmd.description or "No description."
            params = " ".join(f"<{p.name}>" for p in cmd.parameters)
            help_lines.append(f"`/{cmd.name} {params}`\n{desc}\n")
    help_text = "\n".join(help_lines)
    await interaction.response.send_message(help_text)


# ========== SERVER COMMANDS ==========
@client.tree.command(name="start_server", description="Start a game server")
@app_commands.describe(game="The game to start", map="(Optional) Map to start on")
async def start_server(interaction: discord.Interaction, game: str, map: str = None):
    global GMOD_SERVER_RUNNING

    RUN_GAME = False
    game = game.lower()

    config = get_game_config(game)
    if not config:
        await interaction.response.send_message(f"❌ Unknown game: {game}")
        return

    if interaction.user.id == ADMIN_ID:
        RUN_GAME = True
    elif has_required_role(interaction, config['role']):
        RUN_GAME = True 

    if not RUN_GAME:
        await interaction.response.send_message("❌ You don't have permission to start this server.", ephemeral=True)
        return

    if not re.fullmatch(r"[\w\-]+", game):
        await interaction.response.send_message("❌ Invalid game input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return
    if map and not re.fullmatch(r"[\w\-]+", map):
        await interaction.response.send_message("❌ Invalid map input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return

    # Validate map prefix for GMOD games
    if game in GMOD_GAMES:
        if map:
            if game == "ttt" and not map.startswith("ttt"):
                await interaction.response.send_message("❌ TTT maps must start with 'ttt'.", ephemeral=True)
                return
            if game == "prophunt" and not map.startswith("ph_"):
                await interaction.response.send_message("❌ Prophunt maps must start with 'ph_'.", ephemeral=True)
                return
            # Optionally, check if map exists
            if game == "ttt":
                available_maps = list_gmod_maps(TTT_ROOT, prefix="ttt")
            elif game == "sandbox":
                available_maps = list_gmod_maps(SANDBOX_ROOT)
            elif game == "prophunt":
                available_maps = list_gmod_maps(PROPHUNT_ROOT, prefix="ph")
            else:
                available_maps = []
            if map not in available_maps:
                await interaction.response.send_message(f"❌ Map '{map}' not found for {game}.", ephemeral=True)
                return

    if game in GMOD_GAMES and GMOD_SERVER_RUNNING:
        await interaction.response.send_message(f"⚠️ Garry's Mod server is already running.")
        return

    # --- NEW LOGIC: Use persistent start map if not specified ---
    start_maps = load_start_maps()
    map_to_use = map if map else start_maps.get(game, config.get("map"))

    # Build the command, replacing the map argument if needed
    command = [config["exec_path"]] + [arg.format(**config) for arg in config["command_args"]]
    if "+map" in command:
        idx = command.index("+map")
        command[idx + 1] = map_to_use

    try:
        # INIT GAME SPECIFIC LOGIC
        if game in GMOD_GAMES:
            fast_proc = start_gmod_fastdl(game)
        proc = subprocess.Popen(command, preexec_fn=os.setsid)
        if game in GMOD_GAMES:
            GMOD_SERVER_RUNNING = True
        RUNNING_PROCS[game] = proc
        update_config(game, "running")
        log_action(interaction.user, f"START_SERVER {game} on {map_to_use}")
        await set_status(game)
        await interaction.response.send_message(f"✅ {game.capitalize()} server started on map `{map_to_use}`!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to start server: {e}")



@client.tree.command(name="stop_server", description="Stop a game server")
@app_commands.describe(game="The game to stop")
async def stop_server(interaction: discord.Interaction, game: str):
    global GMOD_SERVER_RUNNING

    RUN_GAME = False
    game = game.lower()

    if interaction.user.id == ADMIN_ID:
        RUN_GAME = True
    elif game == 'arma' and (interaction.user.id == 121809298253807620 or interaction.user.id == 267123970770337792):
        RUN_GAME = True
    
    if not RUN_GAME:
        await interaction.response.send_message("❌ You don't have permission to stop this server.", ephemeral=True)
        return

    if game not in RUNNING_PROCS:
        await interaction.response.send_message(f"⚠️ No running {game} server found.")
        return

    proc = RUNNING_PROCS[game]
    try:
        if hasattr(proc, "pid"):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            # Find and kill by name if not a Popen object
            proc_name = GAMES_CONFIG[game].get("server_process_name")
            for p in psutil.process_iter(['name', 'pid']):
                if p.info['name'] == proc_name:
                    os.killpg(os.getpgid(p.info['pid']), signal.SIGTERM)
        if game in GMOD_GAMES:
            stop_gmod_fastdl(game)
    except psutil.NoSuchProcess:
        await interaction.response.send_message(f"⚠️ No running {game} server found.")
        return
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to stop server: {e}")
        return

    if game in GMOD_GAMES:
        GMOD_SERVER_RUNNING = False
    del RUNNING_PROCS[game]
    update_config(game, "stopped")
    log_action(interaction.user, f"STOP_SERVER {game}")
    await set_status(game)
    await interaction.response.send_message(f"🛑 {game.capitalize()} server stopped.")



@client.tree.command(name="list_games", description="List all supported game servers")
async def list_servers(interaction: discord.Interaction):
    server_list = "\n".join(GAMES_CONFIG.keys())
    await interaction.response.send_message(f"🎮 Sc00b's Supported Servers:\n```\n{server_list}```")



@client.tree.command(name="status", description="Get server status and player count")
@app_commands.describe(game="The game to check (e.g., ttt, sandbox, prophunt, arma). Leave blank for all.")
async def status(interaction: discord.Interaction, game: str = None):
    await interaction.response.defer(thinking=True, ephemeral=True)

    def get_gmod_status(game, port):
        address = (LAN_IP, port)
        try:
            server_info = info(address, timeout=1.0)
            return (
                f"🟢 **{server_info.server_name}**\n"
                f"Players online: **{server_info.player_count}/{server_info.max_players}**"
            )
        except (socket.timeout, ConnectionRefusedError):
            return "🔴 Server not running or not reachable."
        except Exception as e:
            # Handle other errors gracefully
            return f"❌ Error: {type(e).__name__}: {e}"

    def get_arma_status():
        try:
            if find_server_process_by_name(GAMES_CONFIG["arma"]["server_process_name"]):
                return "🟢 Arma server is online."
            else:
                return "🔴 Arma server is down."
        except Exception as e:
            return f"❌ Error: {type(e).__name__}: {e}"

    ports = {
        "ttt": TTT_PORT,
        "sandbox": SANDBOX_PORT,
        "prophunt": PROPHUNT_PORT,
    }

    # If a game is specified, show only that game's status
    if game:
        game = game.lower()
        if not re.fullmatch(r"[\w\-]+", game):
            await interaction.followup.send("❌ Invalid game input. Only letters, numbers, underscores, and dashes are allowed.")
            return

        if game in ports:
            msg = f"**{game.upper()}**: {get_gmod_status(game, ports[game])}"
        elif game == "arma":
            msg = f"**ARMA**: {get_arma_status()}"
        else:
            msg = "Unknown game."
        await interaction.followup.send(msg)
        return

    # If no game specified, show all statuses
    status_msgs = []
    for g in ports:
        status_msgs.append(f"**{g.upper()}**: {get_gmod_status(g, ports[g])}\n")
    status_msgs.append(f"**{'ARMA'}**: {get_arma_status()}\n")
    await interaction.followup.send("\n".join(status_msgs))



# GMOD COMMANDS
@client.tree.command(name="ttt_leaderboard", description="Get the TTT leaderboard (K/D, kills, or deaths)")
@app_commands.describe(type="Leaderboard type: kd, kills, or deaths (default: kd)")
async def ttt_leaderboard(interaction: discord.Interaction, type: str = "kd"):
    type = type.lower()
    if type not in ("kd", "kills", "deaths"):
        await interaction.response.send_message("❌ Invalid type. Choose from: kd, kills, deaths.", ephemeral=True)
        return

    if type == "kills":
        leaderboard = get_ttt_kills_leaderboard()
        title = "🗡️ TTT Kills Leaderboard"
    elif type == "deaths":
        leaderboard = get_ttt_deaths_leaderboard()
        title = "💀 TTT Deaths Leaderboard"
    else:
        leaderboard = get_ttt_kd_leaderboard()
        title = "⚖️ TTT Leaderboard"

    if leaderboard:
        await interaction.response.send_message(f"{title}:\n```\n{leaderboard}```")
    else:
        await interaction.response.send_message("⚠️ No data found in the logs.", ephemeral=True)



@client.tree.command(name="list_maps", description="List available maps for a GMOD server")
@app_commands.describe(game=f"The GMOD game mode {str(GMOD_GAMES)}")
async def list_maps(interaction: discord.Interaction, game: str):
    if not re.fullmatch(r"[\w\-]+", game):
        await interaction.response.send_message("❌ Invalid input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return

    game = game.lower()
    if game == "ttt":
        maps = list_gmod_maps(TTT_ROOT, prefix="ttt")
    elif game == "sandbox":
        maps = list_gmod_maps(SANDBOX_ROOT)
    elif game == "prophunt":
        maps = list_gmod_maps(PROPHUNT_ROOT, prefix="ph")
    else:
        await interaction.response.send_message("Unknown GMOD game mode.", ephemeral=True)
        return

    if not maps:
        await interaction.response.send_message(f"No maps found for {game}.", ephemeral=True)
        return

    # Split maps into chunks that fit Discord's 2000 character limit
    chunk = []
    chunk_len = 0
    max_len = 1900  # leave room for formatting
    sent_first = False
    for map_name in maps:
        line = map_name + "\n"
        if chunk_len + len(line) > max_len:
            msg = f"Available maps for {game.upper()}:\n```\n{''.join(chunk)}```" if not sent_first else f"```\n{''.join(chunk)}```"
            if not sent_first:
                await interaction.response.send_message(msg)
                sent_first = True
            else:
                await interaction.followup.send(msg)
            chunk = []
            chunk_len = 0
        chunk.append(line)
        chunk_len += len(line)
    if chunk:
        msg = f"Available maps for {game.upper()}:\n```\n{''.join(chunk)}```" if not sent_first else f"```\n{''.join(chunk)}```"
        if not sent_first:
            await interaction.response.send_message(msg)
        else:
            await interaction.followup.send(msg)



@client.tree.command(name="search_maps", description="Search for maps by name substring")
@app_commands.describe(game=f"The GMOD game mode {str(GMOD_GAMES)}", query="Substring to search for in map names")
async def search_maps(interaction: discord.Interaction, game: str, query: str):
    if not re.fullmatch(r"[\w\-]+", game):
        await interaction.response.send_message("❌ Invalid game input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return
    if not re.fullmatch(r"[\w\-]+", query):
        await interaction.response.send_message("❌ Invalid search input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return

    game = game.lower()
    if game == "ttt":
        maps = list_gmod_maps(TTT_ROOT, prefix="ttt")
    elif game == "sandbox":
        maps = list_gmod_maps(SANDBOX_ROOT)
    elif game == "prophunt":
        maps = list_gmod_maps(PROPHUNT_ROOT, prefix="ph")
    else:
        await interaction.response.send_message("Unknown GMOD game mode.", ephemeral=True)
        return

    results = [m for m in maps if query.lower() in m.lower()]
    if not results:
        await interaction.response.send_message(f"No maps found for '{query}' in {game}.", ephemeral=True)
        return

    # Split results into chunks
    chunk = []
    chunk_len = 0
    max_len = 1900
    sent_first = False
    for map_name in results:
        line = map_name + "\n"
        if chunk_len + len(line) > max_len:
            msg = f"Map search results for '{query}' maps in {game.upper()}:\n```\n{''.join(chunk)}```" if not sent_first else f"```\n{''.join(chunk)}```"
            if not sent_first:
                await interaction.response.send_message(msg)
                sent_first = True
            else:
                await interaction.followup.send(msg)
            chunk = []
            chunk_len = 0
        chunk.append(line)
        chunk_len += len(line)
    if chunk:
        msg = f"Map search results for '{query}' in {game.upper()}:\n```\n{''.join(chunk)}```" if not sent_first else f"```\n{''.join(chunk)}```"
        if not sent_first:
            await interaction.response.send_message(msg)
        else:
            await interaction.followup.send(msg)



@client.tree.command(name="set_start_map", description="Set the default start map for a game")
@app_commands.describe(game="The game to set the map for", map="The map name")
async def set_start_map(interaction: discord.Interaction, game: str, map: str):
    # Check for gary role
    if not any(role.name == "gary" for role in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    # Validate game
    if game not in ["ttt", "sandbox", "prophunt"]:
        await interaction.response.send_message("❌ Invalid game. Choose from: ttt, sandbox, prophunt.", ephemeral=True)
        return

    # Update and save
    start_maps = load_start_maps()
    start_maps[game] = map
    save_start_maps(start_maps)
    await interaction.response.send_message(f"✅ Default start map for **{game}** set to `{map}`.")



@client.tree.command(name="connect_command", description="Get the GMOD in-game console command to connect to a server")
@app_commands.describe(game="The GMOD game mode (ttt, sandbox, prophunt)")
async def connect_command(interaction: discord.Interaction, game: str):
    game = game.lower()
    # Validate input
    if not re.fullmatch(r"[\w\-]+", game):
        await interaction.response.send_message("❌ Invalid game input. Only letters, numbers, underscores, and dashes are allowed.", ephemeral=True)
        return

    # Map game to port
    ports = {
        "ttt": TTT_PORT,
        "sandbox": SANDBOX_PORT,
        "prophunt": PROPHUNT_PORT,
    }
    if game not in ports:
        await interaction.response.send_message("❌ Unknown GMOD game mode.", ephemeral=True)
        return

    # Use your public DNS or IP
    address = f"{DOMAIN}:{ports[game]}"
    command = f"connect {address}"
    await interaction.response.send_message(
        f"To connect to **{game}**, open your GMOD console and enter:\n```\n{command}\n```"
    )

client.run(TOKEN)