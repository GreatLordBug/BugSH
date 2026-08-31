import time
import random
import sys
import bugsh_fs as bfs
import nws_api as nws
from bug_ai.model import BugAIModel, BugAIConversation

c = ""
current_user = "root"
bug_ai_model = BugAIModel("bug_ai/source.txt")
bug_ai_conversation = BugAIConversation(bug_ai_model)

def getc(prompt):
    global c, current_user
    try:
        prompt_sym = "#" if current_user == "root" or bfs.is_user_rodoer(current_user) else d
        c = input(f"[{current_user}@{bfs.location}] {prompt_sym} ")
    except (KeyboardInterrupt, EOFError):
        print("\nexit")
        sys.exit(0)

def newton_meter(num):
    if num:
        print(f"{num} Nm/s")

def foot_pound(num):
    if num:
        print(f"{num} fp/s")

def makeuser():
    print("\n--- BugSH user creation wizard ---")
    try:
        username = input("Enter new username: ").strip()
        if not username:
            print("Error: Username cannot be blank.")
            return

        users = bfs.load_users()
        if username in users or username == "root":
            print("Error: User already exists.")
            return

        password = input("Enter password: ")
        is_rodoer = input("Is this user a Rodoer? (y/n): ").strip().lower() == "y"
        has_rm_perm = input("Grant 'rm -rf /' permissions? (y/n): ").strip().lower() == "y"
    except (KeyboardInterrupt, EOFError):
        print("\nUser creation cancelled.")
        return

    users[username] = {
        "password": password,
        "rodoer": is_rodoer,
        "rm_rf_perm": has_rm_perm
    }

    new_yaml_lines = []
    for u, data in users.items():
        new_yaml_lines.append(f"{u}:")
        new_yaml_lines.append(f"  password: \"{data.get('password', '')}\"")
        new_yaml_lines.append(f"  rodoer: {str(data.get('rodoer', False)).lower()}")
        new_yaml_lines.append(f"  rm_rf_perm: {str(data.get('rm_rf_perm', False)).lower()}")
    
    home_node = bfs.get_dir_node("/home")
    if home_node is not None and isinstance(home_node, dict):
        home_node[".userpass.yaml"] = "\n".join(new_yaml_lines)
        home_node[username] = {}
        print(f"User '{username}' created successfully. Directory /home/{username} initialized.\n")
    else:
        print("Error: /home directory is missing or corrupted.")

def cmd_ls():
    node = bfs.get_dir_node(bfs.location)
    if node is None or not isinstance(node, dict):
        return "Error: Current location invalid."
    items = [k for k in node.keys() if not k.startswith(".")]
    if items:
        return "  ".join(items)
    return ""

def cmd_cd(target):
    test_path = bfs.resolve_path(target)
    if bfs.get_dir_node(test_path) is not None:
        bfs.location = test_path
        return ""
    else:
        return f"BugSH: cd: no such file or directory: {target}"

def cmd_mkdir(args):
    if not args:
        return "mkdir: missing operand"
    target = args[0]
    parent_path, dirname = bfs.split_path_and_name(target)
    parent_node = bfs.get_dir_node(parent_path)
    if parent_node is not None and isinstance(parent_node, dict):
        if dirname in parent_node:
            return f"mkdir: cannot create directory '{dirname}': File exists"
        else:
            parent_node[dirname] = {}
            return ""
    else:
        return f"mkdir: cannot create directory '{target}': No such file or directory"

def cmd_touch(args):
    if not args:
        return "touch: missing operand"
    target = args[0]
    parent_path, filename = bfs.split_path_and_name(target)
    parent_node = bfs.get_dir_node(parent_path)
    if parent_node is not None and isinstance(parent_node, dict):
        if filename not in parent_node:
            parent_node[filename] = ""
        return ""
    else:
        return f"touch: cannot touch '{target}': No such file or directory"

def cmd_cat(target, stdin_content=None):
    if (not target or target == "-") and stdin_content is not None:
        return stdin_content
    if not target:
        return "cat: missing operand"
        
    parent_path, filename = bfs.split_path_and_name(target)
    parent_node = bfs.get_dir_node(parent_path)
    if parent_node is not None and isinstance(parent_node, dict):
        if filename in parent_node:
            if isinstance(parent_node[filename], dict):
                return f"cat: {filename}: Is a directory"
            else:
                return str(parent_node[filename])
        else:
            return f"cat: {target}: No such file or directory"
    else:
        return f"cat: {target}: No such file or directory"

def cmd_rm(args):
    is_rf = False
    target = None
    
    clean_args = []
    for arg in args:
        if arg.startswith("-") and "r" in arg and "f" in arg:
            is_rf = True
        elif arg != "-rf":
            clean_args.append(arg)
            
    if clean_args:
        target = clean_args[0]

    if is_rf and target == "/":
        if not bfs.has_user_rm_perm(current_user):
            return f"BugSH: rm: Permission denied. User '{current_user}' does not have rm -rf / perms."
        print("autorm -rfy / --no-preserve-root")
        bfs.fs = {"/": {}}
        bfs.location = "/"
        print("System destroyed.")
        raise FileNotFoundError("Everything Not Found")

    if not target:
        return "rm: missing operand"

    parent_path, filename = bfs.split_path_and_name(target)
    parent_node = bfs.get_dir_node(parent_path)
    if parent_node is not None and isinstance(parent_node, dict) and filename in parent_node:
        if isinstance(parent_node[filename], dict) and not is_rf:
            return f"rm: cannot remove '{filename}': Is a directory"
        else:
            del parent_node[filename]
            return ""
    else:
        return f"rm: cannot remove '{target}': No such file or directory"

def cmd_compile(args):
    if len(args) < 2:
        return "compile: missing target file argument"
    execute_single_command(f"cat {args[1]} > /.compsubs/compiled{args[1]}")
    execute_single_command(f"echo 'compiled file' > {args[1]}", "root")
    return f"compiled file {args}"

def cmd_supress(args):
    if len(args) < 2:
        return "supress: missing target file argument"
    execute_single_command(f"cat {args[1]} > /.compsubs/.supressed{args[1]}")
    execute_single_command(f"echo 'OPRESSED. NO READ OPRESSED' > {args[1]}", "root")
    return f"supressed file {args}"

def parse_and_execute_pipeline(cmd_line, execution_user):
    if ">" in cmd_line:
        parts = cmd_line.split(">", 1)
        pipeline_part = parts[0]
        redirect_target = parts[1].strip()
        if not redirect_target:
            print("BugSH: syntax error near unexpected token `newline'")
            return None
    else:
        pipeline_part = cmd_line
        redirect_target = None

    pipe_segments = [seg.strip() for seg in pipeline_part.split("|")]
    
    stdin_content = None
    output_str = ""

    for segment in pipe_segments:
        if not segment:
            print("BugSH: syntax error near unexpected token `|'")
            return None
            
        output_str = execute_single_command(segment, execution_user, stdin_content)
        
        if output_str == "BREAK":
            return "BREAK"
        if output_str is None:
            output_str = ""
            
        stdin_content = output_str

    if redirect_target:
        parent_path, filename = bfs.split_path_and_name(redirect_target)
        parent_node = bfs.get_dir_node(parent_path)
        if parent_node is not None and isinstance(parent_node, dict):
            if filename in parent_node and isinstance(parent_node[filename], dict):
                print(f"BugSH: {filename}: Is a directory")
            else:
                parent_node[filename] = output_str
        else:
            print(f"BugSH: {redirect_target}: No such file or directory")
    else:
        if output_str:
            print(output_str)
            
    return None

def run_ai_chat():
    global bug_ai_conversation
    print("BugAI chat started. Type 'exit' to leave.")
    while True:
        try:
            prompt = input("ai> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        print(bug_ai_conversation.ask(prompt))


def execute_single_command(cmd_str, execution_user, stdin_content=None):
    global current_user
    parts = cmd_str.strip().split()
    if not parts:
        return ""
    cmd = parts[0]
    args = parts[1:]

    if cmd == "rodo":
        if not bfs.is_user_rodoer(execution_user):
            return f"BugSH: {execution_user} is not in the rodoers file. This incident will be reported."
        if len(parts) < 2:
            return "rodo: what command do you want to run as root?"
        remaining_cmd = " ".join(parts[1:])
        return execute_single_command(remaining_cmd, "root", stdin_content)

    if cmd == "echo":
        text = " ".join(parts[1:])
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        return text
    elif cmd == "makeuser":
        if execution_user != "root":
            return "makeuser: Only root or elevated users can make a user."
        makeuser()
        return ""
    elif cmd == "ls":
        return cmd_ls()
    elif cmd == "cd":
        target = args[0] if len(args) > 0 else "/"
        return cmd_cd(target)
    elif cmd == "mkdir":
        return cmd_mkdir(args)
    elif cmd == "touch":
        return cmd_touch(args)
    elif cmd == "cat":
        return cmd_cat(args[0] if len(args) > 0 else None, stdin_content)
    elif cmd == "nano":
        bfs.run_nano(args[0] if len(args) > 0 else None)
        return ""
    elif cmd == "rm":
        return cmd_rm(args)
    elif cmd == "whoami":
        return execution_user
    elif cmd == "su":
        if len(args) > 0:
            target_user = args[0]
            if target_user == "root":
                current_user = "root"
            else:
                users = bfs.load_users()
                if target_user in users:
                    current_user = target_user
                else:
                    return f"su: user {target_user} does not exist"
        else:
            current_user = "root"
        return ""
    elif cmd == "pydo":
        runner = " ".join(args)
        try:
            if execution_user == "root":
                exec(runner, globals())
            else:
                exec(runner)
        except Exception as e:
            print(f"Python Execution Error: {e}")
        return ""
    elif cmd == "help":
        return f"""
        BugSH Commands:
            echo: repeats params
            makeuser: makes a new user
            ls: returns all files in current working directory
            cd: changes current working directory
            touch: makes new file
            cat: returns contents of file selected
            nano: basic text editor
            rm: delete stuff
            whoami: see current execution user
            su: changes user
            pydo: executes parameter as python
            rodo: runs command as root, equivalent to sudo
            cwd: prints current working directory"""
    elif cmd == "sudo":
        return "sudo doesn't exist, try rodo"
    elif cmd == "cwd":
        return bfs.location
    elif cmd == "compile":
        return cmd_compile(parts) if execution_user == "root" else "user must be root"
    elif cmd == "supress":
        if not args:
            return "supress: missing file argument"
        try:
            yn = input(f"Are you sure you wish to supress file {parts}? y/n > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return "supression cancelled"
        if yn == "y" and execution_user == "root":
            return cmd_supress(parts)
        return "user must be root" if yn == "y" else "supression cancelled"
    elif cmd == "sedimenc":
        try:
            yn = input(f"Are you sure you wish to reset filesystem to default? y/n > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return "sedimenc cancelled"
        if yn == "y" and execution_user == "root":
            return bfs.run_sedimenc()
        return "user must be root" if yn == "y" else "sedimenc cancelled"
    elif cmd == "alerts":
        if not args:
            return "alerts: missing UGC county/zone code"
        return nws.get_nws_alerts_by_ugc(args[0])
    elif cmd == "ai":
        if not args:
            return "ai: missing prompt"
        return bug_ai_model.ask(" ".join(args))
    elif cmd in {"aichat", "chat"}:
        run_ai_chat()
        return ""
    elif cmd == "setsnap":
        if len(args) > 0:
            return bfs.cmd_setsnap(args)
        else:
            return "setsnap: missing snapshot name"
    elif cmd == "opensnap":
        if len(args) > 0:
            return bfs.cmd_opensnap(args)
        else:
            return "opensnap: missing snapshot name"
    elif cmd == "exit":
        return "BREAK"
    else:
        return f"BugSH: command not found: {cmd}"

def start_install():
    global c
    print("transferring BugKern v2.4 packages")
    print("setting buginstall to false")
    buginstall = False
    time.sleep(random.randint(1, 4) + random.random())
    print("please compile root")
    rootcomp = False
    while not rootcomp:
        if buginstall:
            c = "rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3"
        else:
            getc("# ")
        if c == "rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3":
            rootcomp = True
        if c == "buginstall":
            buginstall = True
            
    for i in range(50):
        print("... COMPILING ...", i + 1, "out of 50 packages")
        time.sleep(0.05)
    print(rootcomp, "ROOT COMPILED")
    print("please remove install packages")
    
    incomp = False
    while not incomp:
        if buginstall:
            c = "rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer"
        else:
            getc("# ")
        if c == "rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer":
            bfs.run_sedimenc()
            incomp = True
            
    print("fat40, fat320, or bug4ext.esrt")
    if not buginstall:
        getc("#")
    else:
        c = "bug4ext.esrt --noinstall"
        
    if c == "fat40":
        print("installing 40 bit fat packages")
        for i in range(500):
            print(f"{i + 1} of 500 kb\n10kb/s")
            time.sleep(0.1)
        print("innit 40 bit sysprocess\nautorm -f ^2")
    elif c == "fat320":
        for i in range(5000):
            print(f"{i + 1}kb of 5 mb\n15kb/s")
            time.sleep(1/15)
    elif c == "bug4ext.esrt":
        print("already innited, borking\nautorm -rfy / --no-preserve-root")
        raise FileNotFoundError("Everything Not Found")
    elif c == "bug4ext.esrt --noinstall":
        print("done")
    else:
        print("autorm -rfy / --no-preserve-root")
        raise FileNotFoundError("Everything Not Found")
        
    print("innitalizing newton_meter_second programs\ninnitalizing foot_pound_second programs")
    newton_meter(5000)
    foot_pound(5000)
    getc("#..#")
    
    enabler_ers72 = False
    print("validate understanding by adding text to  /deathroot/enabler.ers72")
    if c == "nano":
        enabler_ers72 = bfs.run_nano("/deathroot/enabler.ers72")
    if not enabler_ers72:
        print("autorm -rfy / --no-preserve-root")
        raise FileNotFoundError("Everything Not Found")
    return True

if __name__ == '__main__':
    bfs.run_sedimenc()
    try:
        if start_install():
            print("BugSH Initializing. Do Not Quote any BugSH AI Content in your essays.")
            print("BugSH Terminal Access. You must reinstall every time")
            
            current_user = "root"
            while True:
                getc("#" if current_user == "root" else "$")
                if not c.strip():
                    continue
                try:
                    status = parse_and_execute_pipeline(c, current_user)
                    if status == "BREAK":
                        break
                except FileNotFoundError as e:
                    if "Everything Not Found" in str(e):
                        print("Critical: System root was deleted.")
                        sys.exit(1)
                    print(f"Error: {e}")
                except Exception as e:
                    print(f"BugSH Runtime Exception: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nSession terminated.")
