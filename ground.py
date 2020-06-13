from game_constants import SectorType
import pygame
from helper import NordColors

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

class Cluster(pygame.sprite.Sprite):
    sector_locs = {
        2:[(.25, .5), (.75, .5)],
        3:[(.25, .25), (.75, .25), (.5, .75)],
        4:[(.25, .25), (.75, .25), (.75, .75), (.25, .75)]
    }
    def __init__(self, loc, sectors, playarea):
        '''
        sectors -- list of sector types going CCW, starting in topleft-most corner
        '''
        pygame.sprite.Sprite.__init__(self)
        self.loc = loc
        self.in_width = 4
        self.playarea = playarea

        img_path = f'cluster_{len(sectors)}.png'
        self.image0 = pygame.image.load(img_path).convert_alpha()
        self.scale = self.playarea.scalegridtopixel(self.in_width)/self.image0.get_rect().width
        self.image = pygame.transform.rotozoom(self.image0, 0, self.scale)
        self.rect = self.image.get_rect()
        self.rect.center = playarea.gridtopixel(self.loc)
        
        self.sectors = []
        cluster_sector_locs = Cluster.sector_locs[len(sectors)]
        for index, sector in enumerate(sectors):
            self.sectors.append(Sector(sector, self, cluster_sector_locs[index], playarea))
        # # top left
        # x = int(self.rect.width / 4 - self.sectors[0].rect.width / 2)
        # y = int(self.rect.height / 4 - self.sectors[0].rect.height / 2)
        # self.image0.blit(self.sectors[0].image0, (x, y))
        # # top right
        # x = int(self.rect.width * 3 / 4 - self.sectors[1].rect.width / 2)
        # y = int(self.rect.height / 4 - self.sectors[1].rect.height / 2)
        # self.image0.blit(self.sectors[1].image0, (x, y))

    def draw(self, surf):
        print('using custom draw')
        surf.blit(self.image, self.rect.topleft)
        if self.selected:
            pygame.draw.rect(surf, NordColors.frost0, self.rect, 2)
        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(surf, NordColors.frost2, self.rect, 2)
        for sector in self.sectors:
            sector.draw(surf)
    
    def zoom(self, zoom_increment):
        self.scale = self.playarea.scalegridtopixel(self.in_width)/self.image0.get_rect().width
        self.image = pygame.transform.rotozoom(self.image0, 0, self.scale)
        self.rect = self.image.get_rect()
        self.rect.center = self.playarea.gridtopixel(self.loc)
        for sector in self.sectors:
            sector.zoom(zoom_increment)

class Sector(pygame.sprite.Sprite):
    sector_stats = {
        SectorType.COMMERCIAL:{
            'hull':8, 'armor':4, 'value':1, 'img_path':'sector_commercial.png'
        },
        SectorType.MILITARY:{
            'hull':6, 'armor':3, 'value':1, 'defense weapons':True, 'img_path':'sector_military.png'
        },
        SectorType.INDUSTRIAL:{
            'hull':4, 'armor':4, 'value':2, 'img_path':'sector_industrial.png'
        },
        SectorType.RUINS:{
            'hull':-1, 'armor':6, 'value':0, 'img_path':'sector_commercial.png'
        },
        SectorType.ORBITAL_DEFENSE:{
            'hull':6, 'armor':3, 'value':1, 'orbital gun':True, 'img_path':'sector_orbitaldefense.png'
        },
        SectorType.POWER_PLANT:{
            'hull':6, 'armor':4, 'value':4, 'volatile':True, 'img_path':'sector_powerplant.png'
        },
        SectorType.COMMS_STATION:{
            'hull':4, 'armor':5, 'value':1, 'scanner uplink':True, 'img_path':'sector_commstation.png'
        }
    }
    def __init__(self, sector_type, cluster, loc_frac, playarea):
        '''
        loc_frac -- tuple containing position of sector using fraction of cluster width by height 
        '''
        pygame.sprite.Sprite.__init__(self)
        self.p1_assets = []
        self.p2_assets = []
        self.cluster = cluster
        self.playarea = playarea

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
        
        img_path = Sector.sector_stats[sector_type]['img_path']
        self.image0 = pygame.image.load(img_path).convert_alpha()
        self.in_width = .8
        self.scale = self.playarea.scalegridtopixel(self.in_width)/self.image0.get_rect().width
        self.image = pygame.transform.rotozoom(self.image0, 0, self.scale)
        self.rect = self.image.get_rect()
        # self.cluster_index = cluster_index
        self.rect.center = self.cluster.rect.topleft
        self.rect.x = self.rect.x + int(loc_frac[0] * self.cluster.rect.width)
        self.rect.y = self.rect.y + int(loc_frac[1] * self.cluster.rect.height)
        self.loc = self.playarea.pixeltogrid(self.rect.center)
    
    def zoom(self, zoom_increment):
        # print(f'old dims: {self.rect.size}')
        # print(f'old scale: {self.scale}')
        self.scale = self.playarea.scalegridtopixel(self.in_width)/self.image0.get_rect().width
        self.image = pygame.transform.rotozoom(self.image0, 0, self.scale)
        self.rect = self.image.get_rect()
        self.rect.center = self.playarea.gridtopixel(self.loc)
        # print(f'new dims: {self.rect.size}')
        # print(f'new scale: {self.scale}')

    def resolve(self):
        return
    
    def draw(self, surf):
        print('using custom draw')
        surf.blit(self.image, self.rect.topleft)