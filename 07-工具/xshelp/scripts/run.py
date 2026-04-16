import os
import sys
import subprocess
import venv

# [CRITICAL Fix for Windows CP950]
# 強制將標準輸出設為 UTF-8，避免 print emoji 時發生 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
VENV_DIR = os.path.join(SKILL_ROOT, ".venv")

def setup_env():
    if not os.path.exists(VENV_DIR):
        print("Setting up virtual environment...")
        venv.create(VENV_DIR, with_pip=True)

def get_python_path():
    if os.name == "nt":
        return os.path.join(VENV_DIR, "Scripts", "python")
    return os.path.join(VENV_DIR, "bin", "python")

if __name__ == "__main__":
    setup_env()
    python_exec = get_python_path()
    if len(sys.argv) < 2:
        sys.exit(1)
    
    script_to_run = sys.argv[1]
    args = sys.argv[2:]
    full_script_path = os.path.join(SCRIPT_DIR, script_to_run)
    
    # [CRITICAL] 強制子進程使用 UTF-8，避免 CP950 錯誤
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    subprocess.call([python_exec, full_script_path] + args, env=env)
