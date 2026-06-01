#!/usr/bin/env python3
import os, urllib.request, subprocess, time, shutil, zipfile
from datetime import datetime

NEO_VERSION = "21.1.233"
SERVER_DIR  = "servidor_minecraft"
JAVA        = "/usr/lib/jvm/java-21-openjdk-amd64/bin/java"

def run(cmd):
    os.system(cmd)

def out(cmd):
    return subprocess.getoutput(cmd)

# ─────────────────────────────────────────
#  INSTALACIÓN (solo la primera vez)
# ─────────────────────────────────────────
def instalar():
    print("\n══════════════════════════════")
    print("  MSX NEO — Instalando todo")
    print("══════════════════════════════\n")

    # 1. Java 21
    print("[1/4] Instalando Java 21...")
    run("sudo apt-get update -qq")
    run("sudo apt-get install -y openjdk-21-jdk")
    run("sudo update-alternatives --set java /usr/lib/jvm/java-21-openjdk-amd64/bin/java 2>/dev/null")
    print(f"      {out('java -version 2>&1').splitlines()[0]}\n")

    # 2. Tailscale
    print("[2/4] Instalando Tailscale...")
    if not os.path.exists("tailscale-cs"):
        run("git clone https://github.com/elyxdev/tailscale-cs/ tailscale-cs -q")
    run("sudo bash tailscale-cs/script.sh")
    print()

    # 3. NeoForge + Minecraft Server
    print(f"[3/4] Descargando NeoForge {NEO_VERSION}...")
    os.makedirs(SERVER_DIR, exist_ok=True)
    url = (f"https://maven.neoforged.net/releases/net/neoforged/neoforge"
           f"/{NEO_VERSION}/neoforge-{NEO_VERSION}-installer.jar")
    installer = f"{SERVER_DIR}/installer.jar"
    urllib.request.urlretrieve(url, installer)

    print("      Instalando servidor (puede tardar)...")
    os.chdir(SERVER_DIR)
    run(f"{JAVA} -jar installer.jar --installServer")
    os.remove("installer.jar")
    open("eula.txt", "w").write("eula=true\n")
    os.makedirs("mods",  exist_ok=True)
    os.makedirs("world", exist_ok=True)
    os.makedirs("logs",  exist_ok=True)
    os.chdir("..")
    print()

    # 4. Carpeta de mods
    print("[4/4] Creando carpeta de mods...")
    os.makedirs("addons/mods", exist_ok=True)
    print()

    print("══════════════════════════════")
    print("  ✅ ¡Instalación completa!")
    print("══════════════════════════════")
    print(f"\n  📁 {SERVER_DIR}/   → servidor")
    print(f"  📁 addons/mods/   → pon aquí tus mods .jar")
    print()
    input("Presiona Enter para iniciar el servidor...")

# ─────────────────────────────────────────
#  BACKUP AL REPOSITORIO (modo luna)
# ─────────────────────────────────────────
def guardar_repositorio():
    print("\n[+] Guardando mundo en el repositorio...")

    # Verificar que hay repo git
    if subprocess.run("git status", shell=True, capture_output=True).returncode != 0:
        print("[-] No hay repositorio git. Saltando guardado.")
        return

    # Comprimir el mundo
    world_path = os.path.join(SERVER_DIR, "world")
    if not os.path.exists(world_path):
        print("[-] No hay mundo para guardar.")
        return

    os.makedirs("respaldos", exist_ok=True)
    zip_path = "respaldos/world_respaldo.zip"

    print("[+] Comprimiendo mundo...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(world_path):
            for f in files:
                fp = os.path.join(root, f)
                z.write(fp, os.path.relpath(fp, SERVER_DIR))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[+] Comprimido: {size_mb:.1f} MB")
    if size_mb > 100:
        print(f"[!] El respaldo pesa {size_mb:.1f} MB — puede haber problemas en GitHub.")

    # Modo luna: borrar historial y hacer un commit limpio
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("[+] Modo 🌙 Luna: reiniciando historial del repositorio...")

    run("git add .")
    # Deshacer staging de archivos mayores a 100MB
    run("git diff --cached --name-only | xargs -I {} bash -c "
        "'[[ $(stat -c%s \"{}\") -gt 100000000 ]] && git restore --staged \"{}\"' 2>/dev/null")
    run("git checkout --orphan temp_branch 2>/dev/null")
    run("git add -A")
    run(f'git commit -m "[🌙] Guardado {fecha}"')
    run("git branch -D main 2>/dev/null")
    run("git branch -m main")

    if run("git push -f origin main") == 0:
        print("[+] ¡Mundo guardado en el repositorio!")
    else:
        print("[!] Error al subir. Verifica los permisos del repositorio.")

# ─────────────────────────────────────────
#  INICIO (cada vez)
# ─────────────────────────────────────────
def iniciar():
    # Tailscale
    run("sudo bash tailscale-cs/iniciar.sh > tailscale_log.txt 2>&1 &")
    time.sleep(4)
    run("sudo tailscale up --accept-routes")
    ip = out("sudo tailscale ip 2>/dev/null").split("\n")[0].strip()
    if ip:
        print(f"[+] Tailscale listo — IP: {ip}\n")
    else:
        print("[!] No se obtuvo IP de Tailscale\n")

    # Copiar mods nuevos
    for mod in os.listdir("addons/mods"):
        if mod.endswith(".jar"):
            dest = f"{SERVER_DIR}/mods/{mod}"
            if not os.path.exists(dest):
                shutil.copy2(f"addons/mods/{mod}", dest)
                print(f"[+] Mod instalado: {mod}")

    # Iniciar servidor
    print("[+] Iniciando servidor NeoForge...\n")
    os.chdir(SERVER_DIR)
    run("bash run.sh nogui")
    os.chdir("..")

    # Guardar al repositorio cuando el servidor se cierra
    guardar_repositorio()

    input("\n[SERVIDOR APAGADO] Enter para salir...")

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
if not os.path.exists(f"{SERVER_DIR}/run.sh"):
    instalar()

iniciar()
