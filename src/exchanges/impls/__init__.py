from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from typing import List

# iterate through the modules in the current package
from src.exchanges.exchange_interface import CryptoExchangeModuleMetaClass

list_of_impl_meta_class_instances: List[CryptoExchangeModuleMetaClass] = []
list_of_impl_meta_class_names = []


def get_impl_meta_class_instances() -> List[CryptoExchangeModuleMetaClass]:
    return list_of_impl_meta_class_instances


def get_impl_meta_class_names() -> List[CryptoExchangeModuleMetaClass]:
    return list_of_impl_meta_class_names


package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([package_dir]):

    # import the module and iterate through its attributes
    module = import_module(f"{__name__}.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        try:
            if issubclass(attribute, CryptoExchangeModuleMetaClass) and not attribute_name == 'CryptoExchangeModuleMetaClass':
                list_of_impl_meta_class_names.append(attribute)
                list_of_impl_meta_class_instances.append(attribute.get_instance())
        except:
            pass
