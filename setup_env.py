import importlib.util
import importlib.metadata as ilmd
from importlib.metadata import PackageNotFoundError
import os
import platform
import subprocess
import sys
import urllib.request
import re

# Nom de l'environnement (caché)
ENV_NAME = ".env"


def run_cmd(cmd, shell=False, check=True):
    """
    Exécute une commande shell en affichant la sortie en direct.
    Lève une erreur si le code de retour != 0 lorsque check=True.
    """
    print(" $", " ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd)
    result = subprocess.run(cmd, shell=shell)
    if check and result.returncode != 0:
        sys.exit(
            f"❌ Erreur lors de l'exécution de : {' '.join(cmd) if isinstance(cmd, (list, tuple)) else cmd}"
        )


def is_colab() -> bool:
    return "google.colab" in sys.modules


# --- Helpers venv paths ---
def env_python_path(env_name: str) -> str:
    if platform.system() == "Windows":
        return os.path.join(env_name, "Scripts", "python.exe")
    return os.path.join(env_name, "bin", "python")


def env_pip_cmd(env_name: str):
    """
    Retourne la commande (liste) pour invoquer pip du venv de façon fiable:
    [<python_du_venv>, "-m", "pip", ...]
    """
    return [env_python_path(env_name), "-m", "pip"]


# --- Colab: installer seulement ce qui manque, avec contrôle de version strict ---
def _strip_inline_comment(line: str) -> str:
    """
    Retire les commentaires ' # ...' en conservant les URLs contenant '#'
    (on ne retire que si ' #' est précédé d'un espace).
    """
    return re.split(r"\s+#", line, 1)[0].strip()


def _raw_requirement_line(line: str) -> bool:
    """
    Détecte les lignes qui doivent être passées à pip telles quelles
    (editable, VCS/URL, local path, PEP 508 direct refs avec ' @ ').
    """
    l = line.strip()
    return (
        l.startswith(("-e ", "--editable "))
        or " @ " in l
        or l.startswith(
            ("git+", "http://", "https://", "file:", "svn+", "hg+", "bzr+")
        )
        or l.startswith(
            (
                "-f ",
                "--find-links ",
                "--extra-index-url ",
                "--index-url ",
                "--trusted-host ",
            )
        )
        or l.startswith(
            ("-r ", "--requirement ")
        )  # inclusions: on laisse pip gérer
    )


def _ensure_packaging():
    """
    S'assure que 'packaging' est dispo (Colab l'a généralement).
    """
    try:
        import packaging  # noqa: F401
    except Exception:
        run_cmd([sys.executable, "-m", "pip", "install", "packaging"])


def install_requirements_colab(requirements_url: str):
    """
    Installe uniquement les dépendances manquantes sur Colab, avec
    vérification stricte des versions selon les specifiers PEP 440.
    Gère aussi les markers PEP 508 et les extras (ex: package[accel]).
    """
    print("⚡ Exécution sur Colab : vérification stricte des dépendances…")
    _ensure_packaging()
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet

    with urllib.request.urlopen(requirements_url) as resp:
        requirements = resp.read().decode("utf-8").splitlines()

    to_install = []
    for raw in requirements:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue

        # Lignes "brutes" (URL/VCS/editable/options/-r) -> on les laisse à pip
        if _raw_requirement_line(raw):
            print(f"↪︎ Ajout (spécial) : {raw}")
            to_install.append(raw)
            continue

        line = _strip_inline_comment(raw)
        if not line:
            continue

        # Parse PEP 508
        try:
            req = Requirement(line)
        except Exception:
            # En cas de parse compliqué, on délègue à pip
            print(f"↪︎ Ajout (non parsable proprement) : {raw}")
            to_install.append(raw)
            continue

        # Respect des markers (python_version, platform, etc.)
        if req.marker and not req.marker.evaluate():
            print(f"⏭️  Ignore (marker non satisfait) : {req}")
            continue

        dist_name = req.name  # nom de distribution normalisé
        try:
            installed_ver = ilmd.version(dist_name)
        except PackageNotFoundError:
            print(f"⬇️ Manquant : {raw}")
            to_install.append(raw)
            continue

        # Vérif stricte de la version si specifier présent
        spec_ok = True
        if req.specifier:  # type: SpecifierSet
            spec_ok = req.specifier.contains(installed_ver, prereleases=True)

        if spec_ok:
            print(f"✅ {dist_name} {installed_ver} — OK")
        else:
            print(
                f"🔁 {dist_name} {installed_ver} ne satisfait pas '{req.specifier}' → réinstallation : {raw}"
            )
            to_install.append(raw)

    if to_install:
        print("⬇️ Installation/réininstallation des paquets nécessaires…")
        for pkg in to_install:
            run_cmd([sys.executable, "-m", "pip", "install", pkg])
    else:
        print("✅ Toutes les dépendances satisfont les contraintes.")


# --- Local: création et installation dans le venv .env ---
def setup_local_env(
    env_name: str = ENV_NAME, requirements: str = "requirements.txt"
):
    """
    Crée un venv local (par défaut .env), met pip à jour,
    puis installe requirements.txt si présent.
    """
    if os.path.isdir(env_name):
        print(f"ℹ️ L'environnement '{env_name}' existe déjà, on continue.")
    else:
        print(f"📦 Création de l'environnement virtuel : {env_name}…")
        run_cmd([sys.executable, "-m", "venv", env_name])
    py_path = env_python_path(env_name)
    if not os.path.isfile(py_path):
        sys.exit(f"❌ Python du venv introuvable à : {py_path}")

    pip_cmd = env_pip_cmd(env_name)

    print("⬇️ Mise à jour de pip…")
    run_cmd([*pip_cmd, "install", "--upgrade", "pip"])

    if os.path.isfile(requirements):
        print(f"⬇️ Installation des dépendances depuis {requirements}…")
        run_cmd([*pip_cmd, "install", "-r", requirements])
    else:
        print(f"⚠️ Fichier {requirements} introuvable — étape ignorée.")

    print("\n✅ Environnement prêt ! Pour l'activer :\n")
    if platform.system() == "Windows":
        print(f"   PowerShell : .\\{env_name}\\Scripts\\Activate.ps1")
        print(f"   CMD       : {env_name}\\Scripts\\activate.bat")
    else:
        print(f"   Bash/zsh  : source {env_name}/bin/activate")


def main():
    if is_colab():
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
