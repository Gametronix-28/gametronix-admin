import os, sys, subprocess, webbrowser
from pathlib import Path

def main():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    os.chdir(base)
    webbrowser.open("http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(base / "app.py"), "--server.headless=true", "--browser.gatherUsageStats=false"])

if __name__ == "__main__":
    main()
