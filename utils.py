# Fonctions communes à l'ensemble du projet
from pathlib import Path
import sqlite3

##### CONNEXION A LA BDD ########

# Constante
DB_PATH = Path(__file__).parent / "bdd.db" # remonte de pages à app_senat
print(DB_PATH)

# Connection à la BDD
def get_conn():
    return sqlite3.connect(DB_PATH, timeout=30)