import pygame
import csv
from enum import Enum, auto
from guns import Weapon
import copy
import json
import random

class Ship(pygame.sprite.Sprite):
    shipDB = dict()
    shipgunsDB = dict()
    shiplaunchDB = dict()
    ship_counter = 1

    def __init__(self, playarea, shipclass, loc=(-1,-1), name=None, imagepath='blueship.png'):
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
        self.shiptype = Ship.shipDB[shipclass]['shiptype']
        self.guns = []
        self.linked_guns = dict()
        self.player = None
        self.active_sig = self.sig
        for gun in Ship.shipgunsDB[self.shipclass]:
            # print(gun)
            gun_obj = Weapon(self, gun['guntype'], gun['arc'])
            if 'linking' in gun:
                link_index = int(gun['linking'])
                if link_index in self.linked_guns:
                    for linked_gun in self.linked_guns[link_index]:
                        linked_gun.linked_gun = gun_obj
                        gun_obj.linked_gun = linked_gun
                    self.linked_guns[link_index].append(gun_obj)
                else:
                    self.linked_guns[link_index] = [gun_obj]
                    # print(f'linking {gun_obj.linked_gun}')
                    # print(f'with {linking_guns[link_index].linked_gun}')
                gun_obj.linked = link_index
                # print('linked guns')
            if 'count' in gun:
                gun_obj.count = gun['count']
            self.guns.append(gun_obj)

        self.image0 = pygame.image.load(imagepath).convert_alpha()
        self.scale = .05
        # self.bearing = random.random()*360
        self.bearing = 0
        self.image = pygame.transform.rotozoom(self.image0, self.bearing, self.scale)
        self.rect = self.image.get_rect()
        self.panel_rect = pygame.Rect(0,0,0,0)
        self.playarea = playarea
        if loc == (-1,-1):
            loc = (random.random()*48,random.random()*48)
        self.loc = loc
        self.rect.center = playarea.gridtopixel(loc)
        self.is_selected = False
        self.selection_loc = None
        self.selection_bearing = None
        if not name:
            self.name = f'test{Ship.ship_counter}'
            Ship.ship_counter = Ship.ship_counter + 1
        else:
            self.name = name
        self.order = ShipOrder.STANDARD
        self.minthrust = self.thrust/2
        self.maxthrust = self.thrust
        self.highlight = False
        self.state = ShipState.SETUP
        self.group = None
        self.hover = False

    @staticmethod
    def load_shipDB():
        shipfile = open('ships.json')
        shipreader = json.load(shipfile)
        for row in shipreader:
            shipclass = row['shipclass']
            row.pop('shipclass')
            Ship.shipDB[shipclass] = row
        
        shipgunsfile = open('shipguns.json')
        shipgunreader = json.load(shipgunsfile)
        for row in shipgunreader:
            shipclass = row['shipclass']
            row.pop('shipclass')
            weapons = row['weapons']
            if weapons:
                Ship.shipgunsDB[shipclass] = weapons
            launches = row['launch']
            if launches:
                Ship.shiplaunchDB[shipclass] = launches
        # print(Ship.shipgunsDB)
        # print(Ship.shiplaunchDB)

    @staticmethod
    def load_shipDB_csv():
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
        print('[')
        for row in shipgunreader:
            # print(row)
            shipclass = row.pop(0)
            print('{\"shipname\":\"'+shipclass+'\",')
            shipguns = []
            shiplaunch = []
            temp_shipguns = []
            temp_shiplaunch = []
            while len(row) > 0 and row[0] != '':
                temp = {}
                # print(row)
                guntype = row.pop(0)
                # print(f'gun type {guntype}')
                if guntype == 'launch':
                    launchtype = row.pop(0)
                    launchnumber = row.pop(0)
                    shiplaunch.append([launchtype,launchnumber])
                    temp_shiplaunch.append({'launchtype':launchtype,'count':launchnumber})
                    # print(f'adding launch asset {launchnumber} {launchtype}')
                    continue
                gunarc = row.pop(0)
                if 'count' in gunarc:
                    count = gunarc[-1]
                    gunarc = row.pop(0)
                    temp['count'] = count
                else:
                    count = 1
                if 'Linked' in gunarc:
                    # print('linked gun')
                    linking = gunarc[-1]
                    gunarc = row.pop(0)
                    temp['linking'] = linking
                else:
                    linking = 0
                    # print(f'adding weapon {guntype}, firing {gunarc}, linked-{linking}')
                shipguns.append(Weapon(guntype,gunarc,linked=linking,count=count))
                temp['guntype'] = guntype
                temp['arc'] = gunarc
                temp_shipguns.append(temp)
                # print(f'adding weapon {guntype}, firing {gunarc}')
            print('\"weapons\":'+str(temp_shipguns)+',')
            print('\"launch\":'+str(temp_shiplaunch))
            print('},')
            Ship.shipgunsDB.update({shipclass:shipguns})
            Ship.shiplaunchDB.update({shipclass:shiplaunch})
        print(']')
    
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
    
    def update(self):
        if self.state is ShipState.FIRING:
            if self.order is ShipOrder.STANDARD:
                for gun in self.guns:
                    if not gun.active:
                        if not gun.linked_gun or not gun.linked_gun.active:
                            self.state = ShipState.ACTIVATED
                            for gun1 in self.guns:
                                gun1.active = False
                            return
                        else:
                            for gun1 in self.guns:
                                if gun1 is not gun.linked_gun:
                                    gun1.active = False
                            return

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

if __name__ == "__main__":
    Ship.load_shipDB()