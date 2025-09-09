import importlib

def import_attribute(pkg_path):
    assert isinstance(pkg_path, str)
    pkg, attr = pkg_path.rsplit(".", 1)
    return getattr(importlib.import_module(pkg), attr)