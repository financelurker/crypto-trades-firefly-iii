import os
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from typing import List

# iterate through the modules in the current package
from backends.exchanges.exchange_interface import AbstractCryptoExchangeClientModule

list_of_impl_meta_class_instances: List[AbstractCryptoExchangeClientModule] = []
list_of_impl_meta_class_names = []


def get_impl_meta_class_instances() -> List[AbstractCryptoExchangeClientModule]:
    return list_of_impl_meta_class_instances


def get_impl_meta_class_names() -> List[AbstractCryptoExchangeClientModule]:
    return list_of_impl_meta_class_names


package_dir = Path(__file__).resolve().parent
package_dir = os.path.join(package_dir, "impls")
for (_, module_name, _) in iter_modules([package_dir]):

    # import the module and iterate through its attributes
    module = import_module(f"{__name__}.impls.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        try:
            if issubclass(attribute, AbstractCryptoExchangeClientModule) and not attribute_name == 'AbstractCryptoExchangeClientModule':
                list_of_impl_meta_class_names.append(attribute)
                list_of_impl_meta_class_instances.append(attribute.get_instance())
        except:
            pass
