from decimal import Decimal
import importlib

def import_attribute(pkg_path):
    assert isinstance(pkg_path, str)
    pkg, attr = pkg_path.rsplit(".", 1)
    return getattr(importlib.import_module(pkg), attr)

def convert_oz_price_gm(oz_price):
    GRAMS_PER_TROY_OUNCE = Decimal(31.1035)
    return oz_price / GRAMS_PER_TROY_OUNCE