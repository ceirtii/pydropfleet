from enum import Enum, auto

class WeaponArcs(Enum):
    FRONT = 45
    NARROW = 78.75
    LEFT = 135
    BACK = 225
    RIGHT = 315

class GunState(Enum):
    INACTIVE = auto()
    TARGETING = auto()
    FIRED = auto()
    # DISABLED = auto()

class ShipOrder(Enum):
    STANDARD = auto()
    WEAPONSFREE = auto()
    STATIONKEEPING = auto()
    COURSECHANGE = auto()
    MAXTHRUST = auto()
    SILENTRUNNING = auto()
    ACTIVESCAN = auto()

class ShipState(Enum):
    SETUP = auto()
    MOVING = auto()
    FIRING = auto()
    ACTIVATED = auto()
    NOT_YET_ACTIVATED = auto()
    DESTROYED = auto()
    LAUNCHING = auto()

class OrbitalLayer(Enum):
    HIGH_ORBIT = auto()
    LOW_ORBIT = auto()
    ATMOSPHERE = auto()

class SectorType(Enum):
    COMMERCIAL = auto()
    MILITARY = auto()
    INDUSTRIAL = auto()
    RUINS = auto()
    ORBITAL_DEFENSE = auto()
    POWER_PLANT = auto()
    COMMS_STATION = auto()