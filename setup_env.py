import os
import platform
import subprocess
import sys

# Nom de l'environnement = nom du répertoire courant
ENV_NAME = os.path.basename(os.getcwd())

def run_cmd(cmd, shell=False):
    """Exécute une commande shell et affiche le résultat en direct."""
    result = subprocess.run(cmd, shell=shell)
    if result.returncode != 0:
        sys.exit(f"Erreur lors de l'exécution de : {' '.join(cmd)}")

def main():
    print(f"📦 Création de l'environnement virtuel : {ENV_NAME}...")
    run_cmd([sys.executable, "-m", "venv", ENV_NAME])

    # Détermination du chemin vers pip de l'environnement
    if platform.system() == "Windows":
        pip_path = os.path.join(ENV_NAME, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(ENV_NAME, "bin", "pip")

    print("⬇️ Installation des dépendances depuis requirements.txt...")
    run_cmd([pip_path, "install", "--upgrade", "pip"])
    run_cmd([pip_path, "install", "-r", "requirements.txt"])

    print("\n✅ Environnement créé avec succès !")
    print("Pour l'activer :\n")

    if platform.system() == "Windows":
        print(f"   {ENV_NAME}\\Scripts\\activate")
    else:
        print(f"   source {ENV_NAME}/bin/activate")

if __name__ == "__main__":
    main()