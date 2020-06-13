from game_constants import SectorType

class GroundAsset:
    ground_unit_stats = {
        'infantry':{
            'combat armor':5, 'bombardment armor':3, 'attack':1, 'immobile':False
        },
        'armor':{
            'combat armor':3, 'bombardment armor':5, 'attack':1, 'immobile':False
        },
        'defense battery':{
            'combat armor':3, 'bombardment armor':3, 'attack':1, 'immobile':False
        }
    }
    def __init__(self, unit_type):
        self.combat_armor = GroundAsset.ground_unit_stats[unit_type]['combat armor']
        self.bombardment_armor = GroundAsset.ground_unit_stats[unit_type]['bombardment armor']
        self.attack = GroundAsset.ground_unit_stats[unit_type]['attack']
        self.immobile = GroundAsset.ground_unit_stats[unit_type]['immobile']

class Cluster:
    def __init__(self, loc):
        self.loc = loc
        self.sectors = []
    
    def draw(self, surf):
        pass

class Sector:
    sector_stats = {
        SectorType.COMMERCIAL:{
            'hull':8, 'armor':4, 'value':1
        },
        SectorType.MILITARY:{
            'hull':6, 'armor':3, 'value':1, 'defense weapons':True
        },
        SectorType.INDUSTRIAL:{
            'hull':4, 'armor':4, 'value':2
        },
        SectorType.RUINS:{
            'hull':-1, 'armor':6, 'value':0
        },
        SectorType.ORBITAL_DEFENSE:{
            'hull':6, 'armor':3, 'value':1, 'orbital gun':True
        },
        SectorType.POWER_PLANT:{
            'hull':6, 'armor':4, 'value':4, 'volatile':True
        },
        SectorType.COMMS_STATION:{
            'hull':4, 'armor':5, 'value':1, 'scanner uplink':True
        }
    }
    def __init__(self, sector_type):
        self.p1_assets = []
        self.p2_assets = []
        self.cluster = None

        self.sector_type = sector_type
        self.hull = Sector.sector_stats[sector_type]['hull']
        self.hp = self.hull
        self.armor = Sector.sector_stats[sector_type]['armor']
        self.value = Sector.sector_stats[sector_type]['value']

        try:
            self.defense_weapons = Sector.sector_stats[sector_type]['defense weapons']
        except KeyError:
            self.defense_weapons = False
        try:
            self.orbital_gun = Sector.sector_stats[sector_type]['orbital gun']
        except KeyError:
            self.orbital_gun = False
        try:
            self.volatile = Sector.sector_stats[sector_type]['volatile']
        except KeyError:
            self.volatile = False
        try:
            self.scanner_uplink = Sector.sector_stats[sector_type]['scanner uplink']
        except KeyError:
            self.scanner_uplink = False
        
        self.image0 = 
    
    def resolve(self):
        return
    
    def draw(self, surf):
        pass