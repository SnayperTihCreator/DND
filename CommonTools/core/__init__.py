from .client_data import ClientData
from .socket import Socket
from .image_receiver import ImageReceiver, Image
from .image_sender import ImageSender
from .config import *
from .buffer_manager import BufferManager, ViewFog

classes = {
    "Бард": "bard", "Варвар": "barbarian", "Воин": "fighter", "Волшебник": "wizard",
    "Друид": "druid", "Жрец": "cleric", "Изобретатель": "artificer", "Колдун": "warlock",
    "Монах": "monk", "Паладин": "paladin", "Плут": "rogue", "Следопыт": "ranger",
    "Чародей": "sorcerer"
}