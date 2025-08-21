.PHONY: format lint format-all lint-all ruff docstrings lint-docstrings clean-notebooks

# Formater un seul notebook
# Usage : make format FILE=notebooks/mon_notebook.ipynb
format:
	nbqa isort $(FILE)
	nbqa black $(FILE)
	-nbqa docformatter --in-place $(FILE)

# Vérifier un seul notebook (sans modifier)
# Usage : make lint FILE=notebooks/mon_notebook.ipynb
lint:
	nbqa isort --check-only $(FILE)
	nbqa black --check $(FILE)
	nbqa docformatter --check $(FILE)

# Formater tous les notebooks du projet
format-all:
	nbqa isort .
	nbqa black .
	nbqa docformatter --in-place --recursive .

# Vérifier tous les notebooks du projet
lint-all:
	nbqa isort --check-only .
	nbqa black --check .
	nbqa docformatter --check --recursive .

# Ruff linting et corrections automatiques (rapide et complet)
ruff:
	nbqa ruff check --fix .

# Reformater uniquement les docstrings dans tous les notebooks
docstrings:
	nbqa docformatter --in-place --recursive .

# Vérifier uniquement les docstrings
lint-docstrings:
	nbqa docformatter --check --recursive .
	nbqa ruff check --select D .

# Nettoyer les notebooks (supprimer les sorties avant commit)
clean-notebooks:
	nbstripout --install
	nbstripout --force --recursive .