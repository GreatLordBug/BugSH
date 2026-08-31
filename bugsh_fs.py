import socket
import copy
import os
from pathlib import Path
import json

def ensure_dir_exists(path):
    """Creates a nested directory path in the in-memory filesystem if it doesn't exist."""
    global fs
    if not isinstance(fs, dict) or "/" not in fs:
        return
    parts = [p for p in path.split("/") if p]
    current = fs["/"]
    for part in parts:
        if not isinstance(current, dict):
            break
        if part not in current:
            current[part] = {}
        current = current[part]
with open('main.py', 'r', encoding='utf-8') as main, open('bugsh_fs.py', 'r', encoding='utf-8') as bugsh_fs, open('bug_ai/source.txt', 'r', encoding='utf-8') as source, open('nws_api.py', 'r', encoding='utf-8') as nws_api:
    sedimenc_fs = {
        "/": {
            "home": {
                ".userpass.yaml": "root:\n  password: \"\"\n  rodoer: true\n  rm_rf_perm: true\n",
            },
            "dev": {
                "bugkern1": " part 1 of your compiled kernel ",
                "bugkern2": " part 2 of your compiled kernel ",
                "bugkern3": " OPRESSED. NO READ OPRESSED. ",
                "bugkern4": " part 4 of your compiled kernel "
            },
            "boot": {},
            "ip": {"ipconfigsettings": f"hostname: {socket.gethostname()} \nip: {socket.gethostbyname(socket.gethostname())}"},
            "deathroot": {},
            ".compsups": {
                "compiled": {
                    "bugkern1": main.read(),
                    "bugkern2": bugsh_fs.read(),
                    "bugkern4": nws_api.read()
                },
                ".supressed": {
                    "bugkern3": source.read()
                }
            }
        }
    }

fs = {}
location = "/"

def get_real_disk_path(snapshot_name):
    """Calculates the absolute path on the host computer's drive for the snapshot."""
    global location
    virtual_cwd = location.strip("/")
    
    if not virtual_cwd:
        base_dir = Path(".snapshots")
    else:
        base_dir = Path(virtual_cwd) / ".snapshots"
        
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to current working directory if virtual directory structure cannot be mirrored on host
        base_dir = Path(".snapshots")
        base_dir.mkdir(parents=True, exist_ok=True)
        
    # Sanitize snapshot name to prevent path traversal on host machine
    safe_name = Path(snapshot_name).name
    return base_dir / f"{safe_name}.json"

def cmd_setsnap(snapshot_name):
    """Serializes the current in-memory filesystem layout and saves it to the actual drive."""
    global fs
    try:
        real_path = get_real_disk_path(snapshot_name)
        with open(real_path, "w", encoding="utf-8") as f:
            json.dump(fs, f, indent=4)
        return f"Snapshot saved to actual drive: {real_path.resolve()}"
    except Exception as e:
        return f"Error writing snapshot to disk: {str(e)}"

def cmd_opensnap(snapshot_name):
    """Loads a snapshot configuration from the actual drive and overrides the in-memory state."""
    global fs, location
    try:
        real_path = get_real_disk_path(snapshot_name)
        if not real_path.exists():
            return f"opensnap: Snapshot file does not exist on disk: {real_path}"
            
        with open(real_path, "r", encoding="utf-8") as f:
            loaded_fs = json.load(f)
            
        if isinstance(loaded_fs, dict) and "/" in loaded_fs:
            fs = loaded_fs
            if get_dir_node(location) is None:
                location = "/"
            return f"Filesystem successfully restored from disk snapshot: {snapshot_name}"
        else:
            return "opensnap error: Snapshot file structure on disk is invalid."
    except json.JSONDecodeError:
        return "opensnap error: Snapshot file is corrupted or not valid JSON."
    except Exception as e:
        return f"Error reading snapshot from disk: {str(e)}"

def run_sedimenc():
    global fs
    fs = copy.deepcopy(sedimenc_fs)
    return "Filesystem reset to defaults successfully."

def get_dir_node(path):
    global fs
    if not isinstance(fs, dict) or "/" not in fs:
        return None
    if path == "/":
        return fs["/"]
    parts = [p for p in path.split("/") if p]
    current = fs["/"]
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

def resolve_path(target):
    global location
    if not target:
        return "/"
    if target.startswith("/"):
        tokens = [t for t in target.split("/") if t]
    else:
        tokens = [t for t in location.split("/") if t]
        for part in target.split("/"):
            if not part or part == ".":
                continue
            elif part == "..":
                if tokens:
                    tokens.pop()
            else:
                tokens.append(part)
    return "/" + "/".join(tokens)

def split_path_and_name(target):
    absolute_target = resolve_path(target)
    if absolute_target == "/":
        return "/", ""
    parts = absolute_target.rstrip("/").split("/")
    name = parts[-1]
    parent_path = "/" + "/".join(parts[:-1])
    return parent_path, name

def load_users():
    global fs
    try:
        home_node = fs["/"]["home"]
        raw_yaml = home_node.get(".userpass.yaml", "")
    except (KeyError, TypeError):
        return {}
        
    users = {}
    if raw_yaml and isinstance(raw_yaml, str):
        user_key = None
        for line in raw_yaml.splitlines():
            if not line.strip():
                continue
            if not line.startswith(" "):
                user_key = line.split(":")[0].strip()
                users[user_key] = {}
            elif user_key and ":" in line:
                try:
                    k, v = line.split(":", 1)
                    v = v.strip().strip('"').strip("'")
                    if v.lower() == "true": v = True
                    elif v.lower() == "false": v = False
                    users[user_key][k.strip()] = v
                except Exception:
                    continue # Skip malformed YAML configuration lines silently
    return users

def save_users(users: dict):
    """Serialize and save the users dictionary back into the in-memory '.userpass.yaml'."""
    try:
        home_node = fs["/"].get("home", {})
    except Exception:
        return False

    new_yaml_lines = []
    for u, data in users.items():
        new_yaml_lines.append(f"{u}:")
        new_yaml_lines.append(f"  password: \"{data.get('password', '')}\"")
        new_yaml_lines.append(f"  rodoer: {str(data.get('rodoer', False)).lower()}")
        new_yaml_lines.append(f"  rm_rf_perm: {str(data.get('rm_rf_perm', False)).lower()}")

    home_node[".userpass.yaml"] = "\n".join(new_yaml_lines)
    fs["/"]["home"] = home_node
    return True

def is_user_rodoer(user):
    if user == "root":
        return True
    return load_users().get(user, {}).get("rodoer", False)

def has_user_rm_perm(user):
    if user == "root":
        return True
    return load_users().get(user, {}).get("rm_rf_perm", False)

def run_nano(filepath=None, custom_input_func=input):
    if filepath is None:
        print("nano what")
        try:
            filepath = custom_input_func("nano > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting nano.")
            return False
    
    if not filepath:
        print("Error: No file specified.")
        return False

    print("--- BugSH Nano Editor ---")
    print("Type text. Press Enter for a newline.")
    print("Press Enter on a BLANK line to save and exit.")
    
    lines = []
    while True:
        try:
            line = custom_input_func()
            if line == "":
                break
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            print("\nChanges discarded.")
            return False
    
    file_content = "\n".join(lines)
    
    if filepath == "/deathroot/enabler.ers72":
        return bool(file_content)
        
    parent_path, filename = split_path_and_name(filepath)
    parent_node = get_dir_node(parent_path)
    if parent_node is not None and isinstance(parent_node, dict):
        if filename in parent_node and isinstance(parent_node[filename], dict):
            print(f"nano: {filename}: Is a directory")
        else:
            parent_node[filename] = file_content
            print(f"File '{filename}' written successfully.")
    else:
        print(f"nano: {filepath}: No such file or directory")
    return False
