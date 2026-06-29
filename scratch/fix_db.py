import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import auto_migrate
auto_migrate.ejecutar_migraciones()
from app.tools import seed_initial_data
seed_initial_data.main()
