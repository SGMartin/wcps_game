import pkgutil
import importlib
import os

def import_submodules(package_name):
    package = importlib.import_module(package_name)
    package_path = package.__path__

    for _, module_name, is_pkg in pkgutil.walk_packages(package_path):
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)
        if is_pkg:
            import_submodules(full_module_name)

# Import all submodules in the handlers package
import_submodules('wcps_game.handlers')