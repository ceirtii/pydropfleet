import csv
import json
from helper import fill_arc, NordColors
import pygame
import math
import random
from game_constants import *

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
        try:
            self.burnthrough = Weapon.gunDB[guntype]['burnthrough']
        except KeyError:
            self.burnthrough = None
        try:
            self.calibre = Weapon.gunDB[guntype]['calibre']
        except KeyError:
            self.calibre = None
        self.ship = ship
        self.rect = pygame.Rect(0,0,0,0)
        # self.active = False
        self.state = GunState.INACTIVE
        try:
            self.close_action = Weapon.gunDB[guntype]['close_action']
        except KeyError:
            self.close_action = False
        self.targetable_ships = None
        try:
            self.flash = Weapon.gunDB[guntype]['flash']
        except KeyError:
            self.flash = False

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
        if self.burnthrough:
            out_str = out_str + f', burn:{self.burnthrough}'
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
        if self.ship.layer is OrbitalLayer.ATMOSPHERE and self.close_action:
            return out
        # source_layer = self.ship.layer
        sectors = self.get_sectors()
        for target in ships:
            x0, y0 = self.ship.loc
            x1, y1 = target.loc
            # dist = math.dist([x0, y1], [])
            dist = math.sqrt(math.pow(x1-x0,2)+math.pow(y1-y0,2))
            # print(f'ship {target.name} at a distance {dist}')
            if self.close_action or self.ship.layer is OrbitalLayer.ATMOSPHERE:
                gun_range = self.ship.scan
            else:
                gun_range = target.active_sig + self.ship.scan
            # print(f'gun range {gun_range}')
            if dist < gun_range:
                angle = math.atan2(y0-y1,x1-x0)
                if angle < 0:
                    angle = 2*math.pi + angle
                # print(f'angle: {angle}')
                for theta0, theta1 in sectors:
                    check_angle = angle
                    # make sure theta values within math.atan2 range (-pi to pi)
                    # print(f't0={theta0}, t1={theta1}')
                    arc_length = abs(theta1 - theta0)
                    # print(f'arc length={math.degrees(arc_length)}')
                    if abs(math.degrees(arc_length) - 90) > 1 and abs(math.degrees(arc_length) - 22.5) > 1:
                        raise Exception
                    theta0 = theta0 % (2*math.pi)
                    theta1 = theta1 % (2*math.pi)
                    # print(f'mod 2pi: t0={theta0}, t1={theta1}')
                    if theta1 < theta0:
                        theta1 = theta1 + 2*math.pi
                        if check_angle < theta0:
                            check_angle = check_angle + 2*math.pi
                        #     print(f'angle adjustment: angle={check_angle}')
                        # print(f'special case adjustment: t0={theta0}, t1={theta1}')
                    if check_angle > theta0 and check_angle < theta0 + arc_length:
                        # print('ship in firing arc')
                        out.append(target)
                        break
        self.targetable_ships = len(out)
        return out
    
    def shoot(self, ship, multiple):
        result = []
        result.append(f'{self.guntype} on {str(self.ship)} -> {str(ship)}')

        source_layer = self.ship.layer
        target_layer = ship.layer
        in_atmosphere = source_layer is OrbitalLayer.ATMOSPHERE or target_layer is OrbitalLayer.ATMOSPHERE
        crossing_layer = source_layer is not target_layer

        hits = 0
        crits = 0
        if self.burnthrough:
            result.append('firing burnthrough weapon')
            burn_rolls = []
            lock = int(self.lock)
            if in_atmosphere:
                result.append('increasing lock to 6 due to firing through atmo')
                lock = 6
            elif crossing_layer:
                result.append('increasing lock by 1 due to firing across orbital layers')
                lock = lock + 1
            damage = int(self.damage)
            for i in range(int(self.attack)):
                while hits + crits < self.burnthrough:
                    roll = random.randint(1,6)
                    burn_rolls.append(roll)
                    if roll >= lock + 2:
                        crits = crits + damage
                    elif roll >= lock:
                        hits = hits + damage
                    else:
                        break
            burn_str = ', '.join(map(str,burn_rolls))
            result.append(f'burn rolls: {burn_str}')
        else:
            if 'd' in self.attack.lower():
                result.append(f'variable attack {self.attack}')
                attack_cond = self.attack.strip('d')
                dice_faces, addition = map(int,attack_cond.split('+'))
                if multiple > 1:
                    result.append(f'pooling CAW attacks x{multiple}')
                attacks = 0
                for i in range(multiple):
                    attacks = attacks + random.randint(1,dice_faces)+addition
                attack_rolls = [random.randint(1,6) for i in range(attacks)]
            else:
                if multiple > 1:
                    result.append(f'pooling CAW attacks x{multiple}')
                attacks = int(self.attack)*self.count*multiple
                attack_rolls = [random.randint(1,6) for i in range(attacks)]
            attack_str = ', '.join(map(str,attack_rolls))
            result.append(f'attack rolls: {attack_str}')
            # index = 0
            # while index < len(attack_rolls):
            #     if attack_rolls[index] < self.lock:
            #         attack_rolls.pop(index)
            #     else:
            #         index = index + 1
            # attack_str = ', '.join(map(str,attack_rolls))
            # result.append(f'successful hits: {attack_str}')
            if 'd' in str(self.lock).lower():
                print('variable lock not implemented')
                raise Exception
            else:
                lock = int(self.lock)
            
            if self.calibre:
                print(f'gun has calibre {self.calibre}, testing ship tonnage')
                if self.calibre in ship.tonnage:
                    print('calibre matches target ship tonnage')
                    lock = lock - 1
                    result.append(f'gun calibre {self.calibre} matches ship tonnage {ship.tonnage}')
            
            if in_atmosphere:
                result.append('increasing lock to 6 due to firing through atmo')
                lock = 6
            elif crossing_layer:
                result.append('increasing lock by 1 due to firing across orbital layers')
                lock = lock + 1

            if 'd' in str(self.damage).lower():
                pass
            else:
                damage = int(self.damage)
            for val in attack_rolls:
                if val >= lock + 2:
                    crits = crits + damage
                elif val >= lock:
                    hits = hits + damage

        if hits > 0 or crits > 0:
            result.append(f'normal hits: {hits}, critical hits: {crits}')
        else:
            result.append(f'no hits')
            return result
            
        ship_results = ship.mitigate(hits, crits, self.close_action, self.flash)
        for line in ship_results:
            result.append(line)
        return result

class LaunchAsset:
    launchDB = dict()
    def __init__(self, ship, faction, launch_type, count):
        self.ship = ship
        self.faction = faction
        self.launch_type = launch_type
        self.count = count
        # self.launched_count = 0
        # self.launching_count = 0
        self.squadrons = []
        for i in range(count):
            self.squadrons.append(Squadron(ship, faction, launch_type))
            print(f'adding {faction} {launch_type}')
    
    @staticmethod
    def load_launchDB():
        launch_file = open('launch.json')
        launch_reader = json.load(launch_file)
        for row in launch_reader:
            faction = row['faction']
            LaunchAsset.launchDB[faction] = row['launch_assets']
        print(LaunchAsset.launchDB)

class Squadron:
    def __init__(self, ship, faction, launch_type):
        self.ship = ship
        self.faction = faction
        self.launch_type = launch_type
        self.highlight = False
        self.rect = pygame.Rect(0,0,0,0)
        self.launched = False

        if not LaunchAsset.launchDB:
            LaunchAsset.load_launchDB()
        faction_launch_types = LaunchAsset.launchDB[faction]
        # print(faction_launch_types)
        data = None
        for row in faction_launch_types:
            # print(f'checking {row}')
            if row['launch_type'] == launch_type:
                # row.pop('launch_type')
                data = row
                break
        if not data:
            print(f'launch type {launch_type} not found')
            raise Exception

        self.thrust = data['thrust']

        if launch_type == 'Fighter':
            self.pd = data['pd']
            print(f'adding fighter with pd {self.pd}')

        elif launch_type == 'Bomber':
            self.lock = data['lock']
            self.attack = data['attack']
            self.damage = data['damage']
            print(f'adding bomber with lock={self.lock}, attack={self.attack}, damage={self.damage}')

    def draw(self, surf):
        return

    def __str__(self):
        return f'{self.faction} {self.launch_type}'
    
    def get_targets(self, ships):
        out = []
        source_loc = self.ship.loc
        for ship in ships:
            target_loc = ship.loc
            dist = math.dist(source_loc, target_loc)
            if dist < self.thrust:
                # print(f'ship {str(ship)} within thrust range')
                out.append(ship)
            elif dist < self.thrust * 2:
                # print(f'ship {str(ship)} within 2x thrust range')
                out.append(ship)
            else:
                # print(f'ship {str(ship)} outside strike range')
                pass
        return out
    
    def shoot(self, ship, multiple):
        result = []
        attack_rolls = [random.randint(1,6) for i in range(self.attack*multiple)]
        attack_str = ', '.join(map(str,attack_rolls))
        result.append(f'attack rolls: {attack_str}')
        hits = 0
        crits = 0
        for val in attack_rolls:
            if val >= self.lock + 2:
                crits = crits + self.damage
            elif val >= self.lock:
                hits = hits + self.damage
        if hits > 0 or crits > 0:
            result.append(f'normal hits: {hits}, critical hits: {crits}')
        else:
            result.append(f'no hits')
            return result
        ship_results = ship.mitigate(hits, crits, True)
        result = result + ship_results
        return result

if __name__ == "__main__":
    Weapon.load_gunDB()
    LaunchAsset.load_launchDB()