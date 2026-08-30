# BugSH README

BugSH is a tiny mock shell implemented in `main.py`. It is not a real Unix environment; it is a simulated terminal with a fake filesystem, fake install routine, and a few intentionally playful commands.

## Running BugSH

From the project root:

```bash
python main.py
```

When it starts, the program immediately runs:

```python
bfs.run_sedimenc()
```

and then begins the faux installation routine in `start_install()`.

---

## Shell commands available in the main prompt

After installation completes, the shell accepts commands at the prompt. The command dispatch is handled in `execute_single_command()`.

### 1. echo

```bash
echo hello
```

Prints the text back, stripping surrounding quotes if present.

### 2. makeuser

```bash
makeuser
```

Creates a new user via an interactive wizard. Only `root` may do this.

### 3. ls

```bash
ls
```

Lists visible entries in the current directory.

### 4. cd

```bash
cd /
cd /home
cd some/folder
```

Changes the current working directory.

### 5. mkdir

```bash
mkdir newdir
```

Creates a directory.

### 6. touch

```bash
touch file.txt
```

Creates a file if it does not already exist.

### 7. cat

```bash
cat file.txt
```

Prints the contents of a file. If the file is a directory, it prints an error.

### 8. nano

```bash
nano file.txt
```

Opens a basic file editor via `bfs.run_nano()`.

### 9. rm

```bash
rm file.txt
rm -rf some_directory
rm -rf /
```

Deletes a file or directory. `rm -rf /` is a special destructive case that can only run if the current user has the required permission.

### 10. whoami

```bash
whoami
```

Prints the active user name.

### 11. su

```bash
su root
su alice
```

Switches to another user if it exists.

### 12. pydo

```bash
pydo print("hello from python")
```

Executes Python code in the running process. If the execution user is not `root`, it runs in a restricted local scope.

### 13. rodo

```bash
rodo ls
rodo rm -rf /
```

Runs a command as root. This is the shell’s equivalent of `sudo`.

### 14. help

```bash
help
```

Shows the built-in command list.

### 15. cwd

```bash
cwd
```

Prints the current working directory.

### 16. compile

```bash
compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4
```

This is one of the fake install commands used during startup. It can only be used by `root`.

### 17. supress

```bash
supress /dev/bugkern3
```

A deliberately misspelled command that writes a canned output file and is used during the installation script. It is a root-only action.

### 18. sedimenc

```bash
sedimenc
```

Prompts for confirmation and resets the fake filesystem to default if confirmed by `root`.

### 19. alerts

```bash
alerts USNC003
```

Queries weather alerts using the NOAA/NWS API layer and a UGC code.

### 20. ai

```bash
ai tell me a funny bug report
```

Runs a prompt through the local BugAI model.

### 21. aichat / chat

```bash
aichat
```

Starts the interactive chat loop.

### 22. setsnap

```bash
setsnap checkpoint1
```

Saves a snapshot of the fake filesystem state.

### 23. opensnap

```bash
opensnap checkpoint1
```

Restores a previously saved snapshot.

### 24. exit

```bash
exit
```

Exits the shell loop.

### 25. sudo

```bash
sudo ls
```

This is intentionally not implemented. The program responds:

```text
sudo doesn't exist, try rodo
```

---

## The faux install routine (`start_install()`)

When the program starts, it runs the fake install process in `start_install()`. This routine is intentionally scripted and checks for exact strings.

It does not actually install an OS. It is a comedic, “fake root install” sequence that expects the user to type certain commands or trigger the `buginstall` shortcut.

### Stage 1: root compile step

The script prints:

```text
please compile root
```

The expected command is exactly:

```bash
rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3
```

If the user types that exact command, the install flow proceeds.

### Stage 2: package cleanup step

The script then prints:

```text
please remove install packages
```

The expected command is exactly:

```bash
rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer
```

Typing that exact string advances the script.

### Stage 3: choose filesystem flavor

The script then prints:

```text
fat40, fat320, or bug4ext.esrt
```

The valid choices are:

- `fat40`
- `fat320`
- `bug4ext.esrt --noinstall`

If you type `bug4ext.esrt`, the script deliberately crashes with:

```text
autorm -rfy / --no-preserve-root
```

and raises `FileNotFoundError("Everything Not Found")`.

If you type `bug4ext.esrt --noinstall`, it prints:

```text
done
```

and continues.

### Stage 4: final root validation

After the filesystem step, the script asks the user to validate understanding by editing:

```text
/deathroot/enabler.ers72
```

The expected action is to type:

```bash
nano
```

and then write the file. If that validation does not succeed, the script triggers the destructive failure path.

---

## How to do the faux install properly

There are two supported ways to complete the scripted install.

### Method 1: type `buginstall`

If at the prompt you type:

```bash
buginstall
```

then the program sets a flag and automatically supplies the exact required commands behind the scenes.

This is the shortcut flow. It effectively does:

```bash
rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3
rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer
bug4ext.esrt --noinstall
nano
```

This is the easiest path because the script is designed to accept the shortcut and keep moving.

### Method 2: manually type the install commands

If you do not type `buginstall`, the script waits for exact strings typed by the user.

Use this sequence manually:

1. At the first prompt, type:

```bash
rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3
```

2. At the second prompt, type:

```bash
rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer
```

3. At the filesystem selection prompt, type:

```bash
bug4ext.esrt --noinstall
```

4. At the validation prompt, type:

```bash
nano
```

Then create or edit `/deathroot/enabler.ers72` in the faux editor so the script sees the validation succeed.

> Important: the install routine checks for exact strings. Minor mismatch, capitalization differences, or extra whitespace can fail the scripted install.

---

## Note about the fake system

This project intentionally contains deliberately broken or absurd commands and “root install” wording. The purpose is not to be realistic Linux behavior; it is to simulate a goofy, intentionally buggy shell environment. Some commands are destructive by design, and the install process can crash the program if the wrong input is used.

If you want a clean run, the safest path is:

```bash
buginstall
```

or the equivalent manual sequence above.

---

## Example startup flow

```bash
python main.py
buginstall
```

or:

```bash
python main.py
rodo compile /dev/bugkern1 /dev/bugkern2 /dev/bugkern4; rodo suppress /dev/bugkern3
rodo sedimenc; rodo rm -rf /boot/install_bootload /ip/default_root_installer
bug4ext.esrt --noinstall
nano
```

After that, the session moves into the interactive BugSH shell, where the normal commands above become available.
