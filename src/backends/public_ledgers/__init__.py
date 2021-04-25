import os
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from typing import List

from backends.public_ledgers.api import SupportedBlockchainExplorer, SupportedBlockchainModule

available_explorer: List[SupportedBlockchainModule] = []

package_dir = Path(__file__).resolve().parent
package_dir = os.path.join(package_dir, "impls")
for (_, module_name, _) in iter_modules([package_dir]):

    # import the module and iterate through its attributes
    module = import_module(f"{__name__}.impls.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        try:
            if issubclass(attribute, SupportedBlockchainModule) and not attribute_name == 'SupportedBlockchainModule':
                ledger_module = attribute()
                if ledger_module.is_enabled():
                        available_explorer.append(attribute.get_instance())
        except:
            pass
pass
