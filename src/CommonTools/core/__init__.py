from .client_data import ClientData
from .config import *
from .buffer_manager import BufferManager, ViewFog
from .network_discovery import MasterBeacon, ServerScanner
from .socket_adapter import *

classes = {
    "Бард": "bard", "Варвар": "barbarian", "Воин": "fighter", "Волшебник": "wizard",
    "Друид": "druid", "Жрец": "cleric", "Изобретатель": "artificer", "Колдун": "warlock",
    "Монах": "monk", "Паладин": "paladin", "Плут": "rogue", "Следопыт": "ranger",
    "Чародей": "sorcerer"
}