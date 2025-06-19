from config import *
import subprocess
import os
import re
import shlex
import signal
from datetime import datetime
import glob
from collections import Counter

def start_gmod_fastdl(game):
    """Start the FastDL HTTP server for a specific Garry's Mod game."""
    config = GAMES_CONFIG[game]
    fastdl_path = config.get("fastdl_path", f"{GMOD_FASTDL_ROOT_DIR}{game}/")
    fastdl_port = str(config.get("fastdl_port", 27000))
    RUNTIME_UTC = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    http_logfile = os.path.expandvars(f"{GMOD_LOGFILE_ROOT}{game}{RUNTIME_UTC}.log")
    http_proc = subprocess.Popen(
        [
            "python3", "-u", "-m", "http.server", fastdl_port, "-d", fastdl_path
        ],
        stderr=open(http_logfile, "w"),
        stdout=open(http_logfile, "w") if DEBUG else subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    return http_proc

def stop_gmod_fastdl(game):
    """Stop the FastDL HTTP server for a specific Garry's Mod game."""
    config = GAMES_CONFIG[game]
    fastdl_port = str(config.get("fastdl_port", 27000))
    try:
        lsof_cmd = f"lsof -ti:{fastdl_port}"
        pid = subprocess.check_output(shlex.split(lsof_cmd)).decode().strip()
        if pid:
            os.kill(int(pid), signal.SIGTERM)
    except subprocess.CalledProcessError:
        pass


def get_ttt_kills_leaderboard(log_dir=TTT_ULX_LOGS):
    # Gather all log lines
    lines = []
    for filename in glob.glob(os.path.join(log_dir, '*')):
        try:
            with open(filename, 'r', errors='ignore') as f:
                lines.extend(f.readlines())
        except Exception:
            continue

    # Exclude lines with Bot followed by two digits, and filter for kills
    bot_pattern = re.compile(r'Bot\d{2}')
    filtered = [
        line for line in lines
        if " killed" in line and "using" in line and not bot_pattern.search(line)
    ]

    # Extract the part after the first ']' (like awk -F ']')
    filtered = [line.split(']', 1)[1] if ']' in line else line for line in filtered]

    # Extract killer name (before ' killed ')
    killers = []
    for line in filtered:
        if ' killed ' in line:
            killer = line.split(' killed ', 1)[0].strip().strip('"')
            killers.append(killer)

    leaderboard = Counter(killers)
    sorted_leaderboard = leaderboard.most_common()

    # Format leaderboard as a table-like string with Rank
    if not sorted_leaderboard:
        return ""

    header = f"{'Rank':>4}  {'Kills':>5}  Player"
    rows = [f"{i+1:>4}  {count:>5}  {name}" for i, (name, count) in enumerate(sorted_leaderboard)]
    leaderboard_str = "\n".join([header] + rows)
    return leaderboard_str


def get_ttt_deaths_leaderboard(log_dir=TTT_ULX_LOGS):
    import glob
    import re
    from collections import Counter
    death_counts = Counter()
    bot_pattern = re.compile(r'Bot\d{2}')
    log_files = glob.glob(os.path.join(log_dir, "*.txt"))
    for log_file in log_files:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Player killed by another player: Killer killed Victim using ...
                match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) killed (.+?) using ', line)
                if match:
                    victim = match.group(2).strip('"')
                    if not bot_pattern.search(victim):
                        death_counts[victim] += 1
                    continue
                # Player was killed by environment/npc: Victim was killed by ...
                match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) was killed by ', line)
                if match:
                    victim = match.group(1).strip('"')
                    if not bot_pattern.search(victim):
                        death_counts[victim] += 1
                    continue
                # Player sillybillied (self-death)
                match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) sillybillied!', line)
                if match:
                    victim = match.group(1).strip('"')
                    if not bot_pattern.search(victim):
                        death_counts[victim] += 1
    if not death_counts:
        return None
    sorted_deaths = death_counts.most_common()
    header = f"{'Rank':>4}  {'Deaths':>6}  Player"
    rows = [f"{i+1:>4}  {count:>6}  {name}" for i, (name, count) in enumerate(sorted_deaths)]
    leaderboard = "\n".join([header] + rows)
    return leaderboard


def get_ttt_kd_leaderboard(log_dir=TTT_ULX_LOGS):
    import glob
    import re
    from collections import Counter

    # --- Gather kills ---
    lines = []
    for filename in glob.glob(os.path.join(log_dir, '*')):
        try:
            with open(filename, 'r', errors='ignore') as f:
                lines.extend(f.readlines())
        except Exception:
            continue

    bot_pattern = re.compile(r'Bot\d{2}')
    # Kills
    filtered_kills = [
        line for line in lines
        if " killed" in line and "using" in line and not bot_pattern.search(line)
    ]
    filtered_kills = [line.split(']', 1)[1] if ']' in line else line for line in filtered_kills]
    killers = []
    for line in filtered_kills:
        if ' killed ' in line:
            killer = line.split(' killed ', 1)[0].strip().strip('"')
            killers.append(killer)
    kills_counter = Counter(killers)

    # --- Gather deaths ---
    deaths_counter = Counter()
    for line in lines:
        # Player killed by another player
        match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) killed (.+?) using ', line)
        if match:
            victim = match.group(2).strip('"')
            if not bot_pattern.search(victim):
                deaths_counter[victim] += 1
            continue
        # Player was killed by environment/npc
        match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) was killed by ', line)
        if match:
            victim = match.group(1).strip('"')
            if not bot_pattern.search(victim):
                deaths_counter[victim] += 1
            continue
        # Player sillybillied (self-death)
        match = re.search(r'^(?:\[\d{2}:\d{2}:\d{2}\] )?(.+?) suicided!', line)
        if match:
            victim = match.group(1).strip('"')
            if not bot_pattern.search(victim):
                deaths_counter[victim] += 1

    # --- Combine for K/D ---
    all_players = set(kills_counter.keys()) | set(deaths_counter.keys())
    kd_list = []
    for player in all_players:
        kills = kills_counter.get(player, 0)
        deaths = deaths_counter.get(player, 0)
        kd = kills / (deaths if deaths > 0 else 1)
        kd_list.append((player, kills, deaths, kd))

    if not kd_list:
        return None

    # Sort by K/D ratio descending, then kills descending
    kd_list.sort(key=lambda x: (x[1], x[3]), reverse=True)

    header = f"{'Rank':>4}  {'K':>4}  {'D':>4}  {'K/D':>6}  Player"
    rows = [
        f"{i+1:>4}  {k:>4}  {d:>4}  {kd:>6.2f}  {name}"
        for i, (name, k, d, kd) in enumerate(kd_list)
    ]
    leaderboard = "\n".join([header] + rows)
    return leaderboard


def list_gmod_maps(root_dir, prefix=None):
    maps_dir = os.path.join(root_dir, "garrysmod", "maps")
    if not os.path.isdir(maps_dir):
        return []
    maps = []
    for fname in os.listdir(maps_dir):
        if fname.endswith(".bsp"):
            map_name = fname.split(".")[0]
            if prefix is None or map_name.startswith(prefix):
                maps.append(map_name)
    return sorted(maps)