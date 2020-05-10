import pygame
import csv
from enum import Enum, auto
from guns import *

class Ship(pygame.sprite.Sprite):
    shipDB = dict()
    shipgunsDB = dict()
    shiplaunchDB = dict()

    def __init__(self, playarea, loc=(10.0,10.0), name='test', shipclass='test'):
        pygame.sprite.Sprite.__init__(self)
        if not Ship.shipDB:
            Ship.load_shipDB()
        self.shipclass = shipclass
        self.faction = Ship.shipDB[shipclass]['faction']
        self.scan = Ship.shipDB[shipclass]['scan']
        self.sig = Ship.shipDB[shipclass]['sig']
        self.thrust = Ship.shipDB[shipclass]['thrust']
        self.hull = Ship.shipDB[shipclass]['hull']
        self.hp = self.hull
        self.armor = Ship.shipDB[shipclass]['armor']
        self.pd = Ship.shipDB[shipclass]['pd']
        self.shiptype = Ship.shipDB[shipclass]['type']

        self.image0 = pygame.image.load('blueship.png').convert_alpha()
        self.scale = .05
        self.bearing = 0
        self.image = pygame.transform.rotozoom(self.image0, self.bearing, self.scale)
        self.rect = self.image.get_rect()
        self.playarea = playarea
        self.loc = loc
        self.rect.center = playarea.gridtopixel(loc)
        self.is_selected = False
        self.selection_loc = None
        self.selection_bearing = None
        self.name = name
        self.order = ShipOrder.STANDARD
        self.minthrust = self.thrust/2
        self.maxthrust = self.thrust
        self.hover = False

    @staticmethod
    def load_shipDB():
        shipfile = open('ships.csv')
        shipreader = csv.reader(shipfile)
        for row in shipreader:
            # print(row)
            shipname,faction,scan,sig,thrust,hull,armor,pd,shiptype = row
            stats = {'faction':faction,'scan':int(scan),'sig':int(sig),'thrust':int(thrust),'hull':int(hull),'armor':int(armor),'pd':int(pd),'type':shiptype}
            Ship.shipDB.update({shipname:stats})
        # print(shipDB)
        shipfile.close()

        shipgunsfile = open('shipguns.csv')
        shipgunreader = csv.reader(shipgunsfile)
        for row in shipgunreader:
            # print(row)
            shipclass = row.pop(0)
            shipguns = []
            shiplaunch = []
            while len(row) > 0 and row[0] != '':
                # print(row)
                guntype = row.pop(0)
                # print(f'gun type {guntype}')
                if guntype == 'launch':
                    launchtype = row.pop(0)
                    launchnumber = row.pop(0)
                    shiplaunch.append([launchtype,launchnumber])
                    # print(f'adding launch asset {launchnumber} {launchtype}')
                    continue
                gunarc = row.pop(0)
                if 'count' in gunarc:
                    count = gunarc[-1]
                    gunarc = row.pop(0)
                else:
                    count = 1
                if 'Linked' in gunarc:
                    # print('linked gun')
                    linking = gunarc[-1]
                    gunarc = row.pop(0)
                else:
                    linking = 0
                    # print(f'adding weapon {guntype}, firing {gunarc}, linked-{linking}')
                shipguns.append(Weapon(guntype,gunarc,linked=linking,count=count))
                # print(f'adding weapon {guntype}, firing {gunarc}')
            Ship.shipgunsDB.update({shipclass:shipguns})
            Ship.shiplaunchDB.update({shipclass:shiplaunch})
    
    def zoom(self, zoom_increment):
        self.rect.center = self.playarea.gridtopixel(self.loc)
        pass

    def draw_firingarcs(self, surf):
        pass
        # surf.draw
    
    def update_loc(self):
        if self.is_selected:
            self.selection_loc = self.playarea.pixeltogrid(self.rect.center)
            self.selection_bearing = self.bearing
        else:
            self.selection_loc = None
            self.loc = self.playarea.pixeltogrid(self.rect.center)
            self.selection_bearing = None
        # print(f'new location {self.loc}')
    
    def __str__(self):
        out_str = f'{self.shipclass}-class {self.faction} {self.name}'
        return out_str

class ShipOrder(Enum):
    STANDARD = auto()
    WEAPONSFREE = auto()
    STATIONKEEPING = auto()
    COURSECHANGE = auto()
    MAXTHRUST = auto()
    SILENTRUNNING = auto()
    ACTIVESCAN = auto()