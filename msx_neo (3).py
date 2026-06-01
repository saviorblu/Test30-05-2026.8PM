#!/usr/bin/env python3
import os, urllib.request, subprocess, time, shutil

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

    # EULA + carpetas
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
    mods_src  = "addons/mods"
    mods_dest = f"{SERVER_DIR}/mods"
    for mod in os.listdir(mods_src):
        if mod.endswith(".jar"):
            dest = f"{mods_dest}/{mod}"
            if not os.path.exists(dest):
                shutil.copy2(f"{mods_src}/{mod}", dest)
                print(f"[+] Mod instalado: {mod}")

    # Iniciar servidor
    print("[+] Iniciando servidor NeoForge...\n")
    os.chdir(SERVER_DIR)
    run("bash run.sh nogui")
    os.chdir("..")

    input("\n[SERVIDOR APAGADO] Enter para salir...")

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
if not os.path.exists(f"{SERVER_DIR}/run.sh"):
    instalar()

iniciar()
