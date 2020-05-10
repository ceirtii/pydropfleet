import pygame
import csv
from enum import Enum, auto

class Ship(pygame.sprite.Sprite):
    shipDB = dict()

    def __init__(self, playarea, loc=(10.0,10.0), name='test', shipclass='test'):
       pygame.sprite.Sprite.__init__(self)
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
        shipfile = open('ships.csv', encoding="utf-8-sig")
        shipreader = csv.reader(shipfile)
        for row in shipreader:
            print(row)
            shipname,faction,scan,sig,thrust,hull,armor,pd,shiptype = row
            stats = {'faction':faction,'scan':int(scan),'sig':int(sig),'thrust':int(thrust),'hull':int(hull),'armor':int(armor),'pd':int(pd),'type':shiptype}
            Ship.shipDB.update({shipname:stats})
        # print(shipDB)
        shipfile.close()
    
    @staticmethod
    def load_shipguns():
        gunfile = open('guns.csv', encoding="utf-8-sig")
        gunreader = csv.reader(gunfile)
    
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