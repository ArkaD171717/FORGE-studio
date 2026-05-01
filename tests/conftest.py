import sys
from types import ModuleType
from unittest.mock import MagicMock

forge_mock = ModuleType("forge")
forge_mock.ForgeEngine = MagicMock
sys.modules["forge"] = forge_mock
