import csv
import json
from helper import fill_arc, NordColors
import pygame
import math
from enum import Enum
import random

class WeaponArcs(Enum):
    FRONT = 45
    NARROW = 78.75
    LEFT = 135
    BACK = 225
    RIGHT = 315

class Weapon:
    gunDB = dict()

    def __init__(self, ship, guntype, arc, linked=0, count=1):
        self.guntype = guntype
        self.arc_str = arc
        self.arc = []
        for sector in arc.split('/'):
            if sector == 'F':
                self.arc.append(WeaponArcs.FRONT)
            elif sector == 'F(N)':
                self.arc.append(WeaponArcs.NARROW)
            elif sector == 'S':
                self.arc.append(WeaponArcs.LEFT)
                self.arc.append(WeaponArcs.RIGHT)
            elif sector == 'R':
                self.arc.append(WeaponArcs.BACK)
            elif 'L' in sector:
                self.arc.append(WeaponArcs.LEFT)
            elif 'R' in sector:
                self.arc.append(WeaponArcs.RIGHT)
            else:
                raise Exception('invalid weapon arc')
        self.linked = linked
        self.linked_gun = None
        if not Weapon.gunDB:
            Weapon.load_gunDB()
        self.lock = Weapon.gunDB[guntype]['lock']
        self.count = count
        self.attack = Weapon.gunDB[guntype]['attack']
        self.damage = Weapon.gunDB[guntype]['damage']
        self.ship = ship
        self.rect = pygame.Rect(0,0,0,0)
        self.active = False
        try:
            self.close_action = Weapon.gunDB[guntype]['close_action']
        except KeyError:
            self.close_action = False
        

    @staticmethod
    def load_gunDB():
        gunfile = open('guns.json')
        gunreader = json.load(gunfile)
        for row in gunreader:
            guntype = row['guntype']
            row.pop('guntype')
            Weapon.gunDB[guntype] = row

    @staticmethod
    def load_gunDB_csv():
        gunfile = open('guns.csv')
        gunreader = csv.reader(gunfile)
        for row in gunreader:
            guntype = row.pop(0)
            gunstats = dict()
            gunstats.update({'lock':row.pop(0)})
            gunstats.update({'attack':row.pop(0)})
            gunstats.update({'damage':row.pop(0)})
            Weapon.gunDB.update({guntype:gunstats})
        
    def __str__(self):
        out_str = f'{self.guntype}'
        if self.linked != 0:
            out_str = out_str + f'({self.linked})'
        out_str = out_str + f' lock:{self.lock}, att:{self.attack}, dam:{self.damage} arc:{self.arc_str}'
        return out_str
    
    def to_dict(self):
        out = {'guntype':self.guntype, 'arc':self.arc, 'linked':self.linked, 'count':self.count}
        return out
    
    def draw(self, surf, playarea, linked=False):
        if linked:
            # print('drawing linked arc')
            color = NordColors.frost2
        else:
            color = NordColors.frost0
        alpha = (128,)
        for sector in self.get_sectors():
            # if sector is WeaponArcs.NARROW:
            #     arc_length = 22.5
            # else:
            #     arc_length = 90
            # sector_angle = sector.value
            # theta0 = math.radians(self.ship.bearing + sector_angle)
            # theta1 = math.radians(self.ship.bearing + sector_angle + arc_length)
            theta0, theta1 = sector
            pixel_scan = playarea.scalegridtopixel(self.ship.scan)
            fill_arc(surf,self.ship.rect.center,pixel_scan,theta0,theta1,color+alpha)
    
    def get_sectors(self):
        out = []
        for sector in self.arc:
            if sector is WeaponArcs.NARROW:
                arc_length = 22.5
            else:
                arc_length = 90
            sector_angle = sector.value
            theta0 = math.radians(self.ship.bearing + sector_angle)
            theta1 = math.radians(self.ship.bearing + sector_angle + arc_length)
            out.append([theta0,theta1])
        return out
    
    def get_targetable_ships(self, ships, playarea):
        out = []
        sectors = self.get_sectors()
        for target in ships:
            x0, y0 = self.ship.loc
            x1, y1 = target.loc
            dist = math.sqrt(math.pow(x1-x0,2)+math.pow(y1-y0,2))
            print(f'ship {target.name} at a distance {dist}')
            if self.close_action:
                gun_range = self.ship.scan
            else:
                gun_range = target.active_sig + self.ship.scan
            print(f'gun range {gun_range}')
            if dist < gun_range:
                angle = math.atan2(y0-y1,x1-x0)
                if angle < 0:
                    angle = 2*math.pi + angle
                # angle = angle % (2*math.pi)
                
                # if len(sectors) == 4:
                #     out.append(target)
                #     continue
                print(f'angle: {angle}')
                for theta0, theta1 in sectors:
                    check_angle = angle
                    # make sure theta values within math.atan2 range (-pi to pi)
                    print(f't0={theta0}, t1={theta1}')
                    arc_length = abs(theta1 - theta0)
                    print(f'arc length={math.degrees(arc_length)}')
                    if abs(math.degrees(arc_length) - 90) > 1 and abs(math.degrees(arc_length) - 22.5) > 1:
                        raise Exception
                    theta0 = theta0 % (2*math.pi)
                    theta1 = theta1 % (2*math.pi)
                    print(f'mod 2pi: t0={theta0}, t1={theta1}')
                    # if theta0 > math.pi:
                    #     theta0 = -(2*math.pi - theta0)
                    # elif theta0 < -1*math.pi:
                    #     theta0 = -(2*math.pi + theta0)
                    # if theta1 > math.pi:
                    #     theta1 = -(2*math.pi - theta1)
                    # elif theta1 < -1*math.pi:
                    #     theta1 = -(2*math.pi + theta1)
                    if theta1 < theta0:
                        theta1 = theta1 + 2*math.pi
                        if check_angle < theta0:
                            check_angle = check_angle + 2*math.pi
                            print(f'angle adjustment: angle={check_angle}')
                        print(f'special case adjustment: t0={theta0}, t1={theta1}')
                    print()
                    if check_angle > theta0 and check_angle < theta0 + arc_length:
                        print('ship in firing arc')
                        out.append(target)
                        break
                    # different approach:
        return out
    
    def shoot(self, ship):
        attack_rolls = [random.randint(1,6) for i in range(int(self.attack))]


class LaunchAsset():
    def __init__(self, faction, count):
        self.faction = faction
        self.count = count

if __name__ == "__main__":
    Weapon.load_gunDB()