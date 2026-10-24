import os
import sys
import argparse
import base64
import subprocess
import shutil

def main():
    parser = argparse.ArgumentParser(
        description="Konwertuje plik .bat/.cmd na plik .exe",
        usage="bat2exe <scieżka_pliku> -n <nazwa_exe> [-ico <ścieżka_ico>] [-hide]"
    )
    
    parser.add_argument("bat_file", help="Ścieżka do pliku .bat lub .cmd")
    parser.add_argument("-n", "--name", required=True, help="Nazwa wyjściowa pliku EXE (bez rozszerzenia)")
    parser.add_argument("-ico", "--icon", help="Ścieżka do pliku ikony (.ico) - opcjonalnie", default=None)
    parser.add_argument("-hide", "--hidden", action="store_true", help="Ukryj okno konsoli podczas uruchamiania")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    bat_path = args.bat_file
    exe_name = args.name
    icon_path = args.icon
    hide_window = args.hidden

    if not os.path.exists(bat_path):
        print(f"[BŁĄD] Plik BAT nie istnieje: {bat_path}")
        sys.exit(1)

    print(f"[*] Odczytywanie pliku BAT: {bat_path}")
    try:
        with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
            bat_content = f.read()
    except Exception as e:
        print(f"[BŁĄD] Nie udało się odczytać pliku: {e}")
        sys.exit(1)

    # Kodowanie treści BAT do Base64
    bat_encoded = base64.b64encode(bat_content.encode("utf-8")).decode("utf-8")

    output_dir = os.getcwd()
    temp_py_name = os.path.join(output_dir, f"temp_wrapper_{exe_name}.py")

    # Tworzenie wrappera w Pythonie, który osadza w sobie kod .bat
    wrapper_code = f"""import os
import sys
import base64
import tempfile
import subprocess

bat_data = "{bat_encoded}"
bat_content = base64.b64decode(bat_data).decode("utf-8")

temp_dir = tempfile.gettempdir()
temp_bat_path = os.path.join(temp_dir, "script_run_{exe_name}.bat")

with open(temp_bat_path, "w", encoding="utf-8") as f:
    f.write(bat_content)

if {str(hide_window)}:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call([temp_bat_path], startupinfo=startupinfo)
else:
    subprocess.call([temp_bat_path])

try:
    os.remove(temp_bat_path)
except:
    pass
"""

    with open(temp_py_name, "w", encoding="utf-8") as f:
        f.write(wrapper_code)

    print("[*] Kompilowanie wrappera do pliku EXE za pomocą PyInstallera...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole" if hide_window else "--console",
        f"--name={exe_name}",
        f"--distpath={output_dir}",
        "--clean"
    ]

    if icon_path:
        if os.path.exists(icon_path):
            cmd.append(f"--icon={icon_path}")
        else:
            print(f"[OSTRZEŻENIE] Plik ikony nie istnieje: {icon_path}. Pomijam ikonę.")

    cmd.append(temp_py_name)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Sprzątanie plików tymczasowych
        spec_file = f"{exe_name}.spec"
        if os.path.exists(spec_file): os.remove(spec_file)
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists(temp_py_name): os.remove(temp_py_name)

        if result.returncode == 0:
            print(f"\n[SUKCES] Pomyślnie utworzono plik EXE!")
            print(f"Lokalizacja: {os.path.join(output_dir, exe_name + '.exe')}")
        else:
            print(f"\n[BŁĄD] PyInstaller zwrócił błąd:\n{result.stderr}")

    except Exception as e:
        print(f"\n[BŁĄD] Wystąpił nieoczekiwany błąd: {e}")

if __name__ == "__main__":
    main()