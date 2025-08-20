import importlib.util
import os
import platform
import subprocess
import sys
import urllib.request

# Nom de l'environnement = nom du répertoire courant
ENV_NAME = os.path.basename(os.getcwd())


def run_cmd(cmd, shell=False):
    """
    Exécute une commande shell et affiche le résultat en direct.
    """
    result = subprocess.run(cmd, shell=shell)
    if result.returncode != 0:
        sys.exit(f"Erreur lors de l'exécution de : {' '.join(cmd)}")


def install_requirements_colab(requirements_url):
    """
    Installe uniquement les dépendances manquantes sur Colab.
    """
    print("⚡ Exécution sur Colab : vérification des dépendances...")
    response = urllib.request.urlopen(requirements_url)
    requirements = response.read().decode("utf-8").splitlines()
    for line in requirements:
        pkg = line.strip()
        if not pkg or pkg.startswith("#"):
            continue
        module_name = pkg.split("==")[0]
        if importlib.util.find_spec(module_name) is None:
            print(f"⬇️ Installation de {pkg}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg]
            )
        else:
            print(f"✅ {module_name} déjà présent.")


def setup_local_env():
    """
    Crée un venv et installe toutes les dépendances localement.
    """
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


def main():
    if "google.colab" in sys.modules:
        # Mode Colab
        requirements_url = (
            "https://raw.githubusercontent.com/auduvignac/llm-finetuning/refs/"
            "heads/main/requirements.txt"
        )
        install_requirements_colab(requirements_url)
    else:
        # Mode local
        setup_local_env()


if __name__ == "__main__":
    main()
