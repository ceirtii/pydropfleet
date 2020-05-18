import pygame
import csv
from guns import *
import copy
import json
import random
from game_constants import *

class Ship(pygame.sprite.Sprite):
    shipDB = dict()
    shipgunsDB = dict()
    shiplaunchDB = dict()
    ship_counter = 1
    ship_tonnage = {'light': 1, 'medium': 5, 'heavy': 10, 'super heavy': 15, 'light2': 2}

    def __init__(self, playarea, shipclass, loc=(-1,-1), name=None, imagepath='blueship.png'):
        """
        Initialize Ship object. Reads ship properties from Ship.shipDB and 
        weapon loadout from Ship.shipgunsDB.

        playarea -- reference to PlayArea object for gameplay.
        shipclass -- Ship class for property lookup.
        loc -- Location on playarea as tuple coord.
        name -- name of ship
        imagepath -- path to image used for drawing the ship on the playarea.
        """
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
        self.tonnage = Ship.shipDB[shipclass]['tonnage']

        # special characteristics
        try:
            self.atmospheric = Ship.shipDB[shipclass]['atmospheric']
        except KeyError:
            self.atmospheric = False
        
        self.linked_guns = dict()
        self.player = None
        self.active_sig = self.sig

        self.guns = []
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
                gun_obj.count = int(gun['count'])
            self.guns.append(gun_obj)
        
        self.torpedoes = None
        self.fighters = None
        self.bombers = None
        self.dropships = None
        self.bulk_landers = None
        try:
            Ship.shiplaunchDB[self.shipclass]
        except KeyError:
            print('ship does not have launch assets')
        else:
            for launch in Ship.shiplaunchDB[self.shipclass]:
                if launch['launchtype'] == 'Fighters & Bombers':
                    launch_asset = LaunchAsset(self, self.faction, 'Fighter', launch['count'])
                    self.fighters = launch_asset
                    launch_asset = LaunchAsset(self, self.faction, 'Bomber', launch['count'])
                    self.bombers = launch_asset
                else:
                    launch_asset = LaunchAsset(self, self.faction, launch['launchtype'], launch['count'])

                if launch['launchtype'] == 'Dropships':
                    self.dropships = launch_asset
                elif launch['launchtype'] == 'Torpedo':
                    self.torpedoes = launch_asset
                elif launch['launchtype'] == 'Bulk Lander':
                    self.bulk_landers = launch_asset

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
        # self.minthrust = self.thrust/2
        # self.maxthrust = self.thrust
        self.highlight = False
        self.state = ShipState.SETUP
        self.group = []
        self.battlegroup = None
        self.hover = False
        self.fired_guns = 0
        self.scanner_damage = 0
        if self.hull < 7:
            self.max_cohesion = 3
        else:
            self.max_cohesion = 6
        self.layer = OrbitalLayer.HIGH_ORBIT
        self.can_turn = True
        self.moving_up = False
        self.moving_down = False
        self.active_launch_assets = 0
        
        self.crippled = False
        # crippled effects
        self.fire = False
        self.armor_cracked = False
        self.weapons_offline = False
        self.engines_disabled = False
        self.scanners_offline = False
        self.orbital_decay = False
        self.energy_surge = False

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
        # if self.order is ShipOrder.STANDARD:
        #     self.minthrust = self.thrust/2
        #     self.maxthrust = self.thrust
        if self.state is ShipState.FIRING:
            # print('checking if ship can fire guns')
            # no_target_available = False
            fired_guns = 0
            pending_linked_guns = []
            close_action_fired = False
            if self.order is ShipOrder.STANDARD:
                max_fired_guns = 1
            else:
                max_fired_guns = 1
            for gun in self.guns:
                # print(f'testing gun {gun}')
                # print(f'gun has {gun.targetable_ships} targetable ships')
                # if gun.targetable_ships is not None:
                # no_target_available = no_target_available or 
                if gun.state is GunState.INACTIVE:
                    # don't check, already inactive
                    continue
                elif gun.state is GunState.FIRED:
                    fired_guns = fired_guns + 1
                    # print('fired gun found, check if linked gun is valid')
                    if gun.close_action:
                        # print('close action gun fired')
                        close_action_fired = True
                        fired_guns = fired_guns - 1
                    elif gun.linked_gun:
                        # print('found linked gun')
                        if gun in pending_linked_guns:
                            # print('gun already checked through link')
                            fired_guns = fired_guns - 1
                        else:
                            # print('new group of linked guns')
                            pending_linked_guns.append(gun)
                            pending_linked_guns.append(gun.linked_gun)

                        if gun.linked_gun.state is GunState.FIRED:
                            print('linked gun has fired')
                        elif gun.linked_gun.state is GunState.INACTIVE:
                            print('linked gun has no valid targets')
                        elif gun.linked_gun.state is GunState.TARGETING:
                            print('linked gun is still targeting')
                            fired_guns = fired_guns - 1
                    else:
                        print('not close action, no linked gun')
                        # for gun1 in self.guns:
                        #     if gun1 is not gun.linked_gun and gun1 is not gun:
                        #         print(f'found unlinked gun {gun1}, setting inactive')
                        #         gun1.active = False
                        # all_guns_inactive = False
                        # break
                elif gun.targetable_ships is not None and gun.targetable_ships < 1:
                    print('no targetable ships, disabling')
                    gun.state = GunState.INACTIVE
                    # break
                # elif gun.state is GunState.TARGETING and gun.close_action:
                #     print('close action gun not yet fired and has valid targets')
                    # fired_guns = fired_guns - 1
            # check linked guns
            # print(f'{fired_guns} guns fired, max of {max_fired_guns}')

            fired_linked_gun_groups = int(len(pending_linked_guns)/2)
            if fired_guns + fired_linked_gun_groups >= max_fired_guns:
                print('disabling guns not linked')
                for gun in self.guns:
                    if gun not in pending_linked_guns and not gun.close_action:
                        gun.state = GunState.INACTIVE

            # after each gun checked, see if crossed max fired guns threshold
            if fired_guns == max_fired_guns:
                # print('max regular fired guns reached')
                for gun in self.guns:
                    if not gun.close_action:
                        gun.state = GunState.INACTIVE
                if close_action_fired:
                    self.finish_activation()
                # break
            
            # else:
            all_guns_inactive = True
            for gun in self.guns:
                all_guns_inactive = all_guns_inactive and gun.state in [GunState.FIRED, GunState.INACTIVE]
            if all_guns_inactive:
                # print('all guns inactive')
                self.finish_activation()

                # if no_target_available:
                #     print('no target available, activating all guns')
                #     self.state = ShipState.ACTIVATED
                #     for gun in self.guns:
                #         gun.active = False

                # all guns not active
        else:
            self.fired_guns = 0
    
    def finish_activation(self):
        print('finish ship activation')
        self.state = ShipState.ACTIVATED
        if self.order is ShipOrder.STANDARD:
            if self.active_sig > self.sig:
                print('standard order, removing minor spike')
                self.remove_spike(1)
        elif self.order is ShipOrder.WEAPONSFREE:
            print('weapons free, adding major spike')
            self.apply_spike(2)
    
    def apply_spike(self, amount):
        for i in range(amount):
            self.active_sig = self.active_sig + 6

        if self.active_sig > self.sig + 12:
            self.active_sig = self.sig + 12
    
    def remove_spike(self, amount):
        for i in range(amount):
            self.active_sig = self.active_sig - 6

        if self.active_sig < self.sig:
            self.active_sig = self.sig
    
    def mitigate(self, hits, crits, close_action=False, flash=False):
        out = []
        out.append(f'{str(self)} mitigating damage')

        # check if attacking a ded ship
        if self.hp == 0:
            out.append('ship already dead!')
            return out

        if close_action:
            out.append(f'defending against close action, applying pd {self.pd}')
            pd_rolls = [random.randint(1,6) for i in range(self.pd)]
            pd_str = ', '.join(map(str,pd_rolls))
            out.append(f'pd rolls: {pd_str}')
            
            blocked_by_pd = 0

            for roll in pd_rolls:
                if roll > 4:
                    blocked_by_pd = blocked_by_pd + 1

            mitigated_crits = 0

            while crits > 0 and blocked_by_pd > 1:
                crits = crits - 1
                mitigated_crits = mitigated_crits + 1
                blocked_by_pd = blocked_by_pd - 2

            if mitigated_crits > 0:
                out.append(f'mitigated {mitigated_crits} crits by pd')

            mitigated_hits = 0
            while hits > 0 and blocked_by_pd > 0:
                hits = hits - 1
                mitigated_hits = mitigated_hits + 1
                blocked_by_pd = blocked_by_pd - 1

            if mitigated_hits > 0:
                out.append(f'mitigated {mitigated_hits} hits by pd')

            if crits + hits == 0:
                return out
        
        if hits > 0:
            armor_rolls = [random.randint(1,6) for i in range(hits)]
            armor_str = ', '.join(map(str,armor_rolls))
            out.append(f'armor rolls: {armor_str}')
            mitigated_hits = 0
            if 'd' in str(self.armor):
                pass
            else:
                armor = int(self.armor)
            if self.armor_cracked:
                armor = armor + 2
            for roll in armor_rolls:
                if hits == 0:
                    break
                if roll >= armor:
                    mitigated_hits = mitigated_hits + 1
                    hits = hits - 1
            out.append(f'damage mitigated: {mitigated_hits}')

            # apply flash
            if flash:
                self.apply_spike(1)
            elif hits + crits >= 3:
                self.apply_spike(1)

        self.hp = self.hp - hits - crits
        out.append(f'damage dealt: {hits + crits}')

        # check for crippling damage
        if not self.crippled:
            reactor_overload = True
            while self.hp <= self.hull/2 and reactor_overload:
                reactor_overload = False
                out.append('rolling for crippling damage')
                self.crippled = True
                location = random.choice(['subsystems', 'hull', 'core systems'])
                if location == 'subsystems':
                    damage = random.choice(['flash', 'fire', 'energy surge'])
                    if damage == 'flash':
                        self.apply_spike(1)
                    elif damage == 'fire':
                        self.fire = True
                    else:
                        self.hp = self.hp - 2
                        self.orbital_decay = True
                        self.energy_surge = True
                elif location == 'hull':
                    damage = random.choice(['scanners offline', 'armor cracked', 'hull breach'])
                    if damage == 'scanners offline':
                        self.scanners_offline = True
                        self.scan = 1
                    elif damage == 'armor cracked':
                        self.armor_cracked = True
                        self.hp = self.hp - 2
                    else:
                        self.hp = self.hp - 2
                        self.orbital_decay = True
                else:
                    damage = random.choice(['engines disabled', 'weapons offline', 'reactor overload'])
                    if damage == 'engines disabled':
                        self.hp = self.hp - 2
                        self.engines_disabled = True
                        self.thrust = self.thrust / 2
                        self.orbital_decay = True
                        self.can_turn = False
                    elif damage == 'weapons offline':
                        self.hp = self.hp - 3
                        self.weapons_offline = True
                    else:
                        self.hp = self.hp - 3
                        self.orbital_decay = True
                        reactor_overload = True
                        out.append('rolling again due to reactor overload')
                out.append(f'ship crippled effect: {damage}')
        
        # check ded
        if self.hp < 1 and self.state is not ShipState.DESTROYED:
            destruction_out = self.on_destroy()
            for line in destruction_out:
                out.append(line)
        
        return out
    
    def on_destroy(self, catastrophic_damage=True):
        out = []
        out.append(f'ship destroyed!')
        self.hp = 0
        self.state = ShipState.DESTROYED
        self.battlegroup.update_sr()

        if catastrophic_damage:
            # do catastrophic damage
            if self.hull < 4:
                out.append('ship too small for catastrophic damage')
            else:
                out.append('rolling for catastrophic damage')
                explode_roll = random.randint(1,6)
                
                if self.hull < 7:
                    explode_radius = random.randint(1,3)
                else:
                    explode_radius = random.randint(1,6)

                if self.hull >= 10:
                    explode_roll = explode_roll + 1

                out.append(f'rolled {explode_roll}, radius {explode_radius}')
                cata_damage = self.gamecontroller.do_catastrophic_damage(self, explode_roll, explode_radius)
                for line in cata_damage:
                    out.append(line)
        
        self.loc = (-1000, -1000)
        self.rect = pygame.Rect(0,0,0,0)
        return out

    def draw_cohesion(self, surf):
        for neighbor_ship in self.group:
            if neighbor_ship is self:
                continue
            x0, y0 = self.rect.center
            x1, y1 = neighbor_ship.rect.center
            cohesion = self.playarea.scale_pixel_to_grid(math.dist([x0, y0], [x1, y1]))
            if cohesion < self.max_cohesion:
                line_color = NordColors.aurora3
            else:
                line_color = NordColors.aurora0
            pygame.draw.line(surf, line_color, neighbor_ship.rect.center, self.rect.center)
    
    def draw_tooltip(self, surf, mousepos, font):
        tt_str = f'sca={self.scan}/sig={self.active_sig}/thr={self.thrust}/arm={self.armor}/pd={self.pd}'
        tt_render = font.render(tt_str, True, NordColors.snow0)
        tt_rect = tt_render.get_rect()
        tt_rect.bottomleft = mousepos
        pygame.draw.rect(surf, NordColors.nord1, tt_rect)
        x, y = mousepos
        surf.blit(tt_render, (x, y - tt_rect.height))
    
    def do_damage_control(self):
        if self.state is ShipState.DESTROYED:
            return
        out = []
        if self.fire:
            out.append('Fighting fires')
            result = random.randint(1,6)
            if result == 1:
                out.append('Damage control critical failure')
                self.hp = self.hp - 2
            elif result <= 3:
                out.append('Damage control failed')
                self.hp = self.hp - 1
            else:
                out.append('Fires extinguished')
                self.fire = False

        if self.energy_surge:
            out.append('Controlling energy surges')
            result = random.randint(1,6)
            if result == 1:
                out.append('Damage control critical failure')
                self.hp = self.hp - 1
            elif result <= 3:
                out.append('Damage control failed')
            else:
                out.append('Energy surges stopped')
                self.energy_surge = False

        if self.scanners_offline:
            out.append('Repairing scanners')
            result = random.randint(1,6)
            if result == 1:
                out.append('Damage control critical failure')
                self.hp = self.hp - 1
            elif result <= 3:
                out.append('Damage control failed')
            else:
                out.append('Scanners repaired')
                self.scanners_offline = False
                self.scan = Ship.shipDB[self.shipclass]['scan']

        if self.engines_disabled:
            out.append('Repairing engines')
            result = random.randint(1,6)
            if result == 1:
                out.append('Damage control critical failure')
                self.hp = self.hp - 1
            elif result <= 3:
                out.append('Damage control failed')
            else:
                out.append('Engines repaired')
                self.engines_disabled = False
                self.thrust = Ship.shipDB[self.shipclass]['thrust']
                self.can_turn = True
        
        if self.hp <= 0:
            destruction_out = self.on_destroy()
            for line in destruction_out:
                out.append(line)
        return out
    
    def get_crippling_effects(self):
        out = []
        if not self.crippled:
            return out
        
        if self.fire:
            out.append('On fire')
        if self.armor_cracked:
            out.append('Armor cracked')
        if self.weapons_offline:
            out.append('Weapons offline')
        if self.engines_disabled:
            out.append('Engines disabled')
        if self.scanners_offline:
            out.append('Scanners offline')
        if self.orbital_decay:
            out.append('Orbital decay')
        if self.energy_surge:
            out.append('Energy surge')
        return out
    
    def draw_sig(self, surf):
        x, y = self.rect.center
        sig_color = NordColors.aurora4
        sig = self.playarea.scalegridtopixel(self.active_sig)
        alpha = (64,)
        return pygame.gfxdraw.filled_circle(surf,x,y,sig,sig_color+alpha)
    
    def move_up(self):
        if self.layer is OrbitalLayer.ATMOSPHERE:
            self.layer = OrbitalLayer.LOW_ORBIT

        elif self.layer is OrbitalLayer.LOW_ORBIT:
            self.layer = OrbitalLayer.HIGH_ORBIT
        
        else:
            print('ESCAPE VELOCITY!?!?!?!?!!?')
            raise Exception

        self.moving_up = False
    
    def move_down(self):
        out = ''
        if self.layer is OrbitalLayer.ATMOSPHERE:
            print('Crashed into ground!')
            self.on_destroy(catastrophic_damage=False)
            out = 'Crashed into ground!'

        elif self.layer is OrbitalLayer.LOW_ORBIT:
            if self.atmospheric:
                self.layer = OrbitalLayer.ATMOSPHERE
                out = 'Dropped to atmosphere'
            else:
                print('Crashed into atmosphere!')
                self.on_destroy(catastrophic_damage=False)
                out = 'Crashed into atmosphere!'
        
        elif self.layer is OrbitalLayer.HIGH_ORBIT:
            self.layer = OrbitalLayer.LOW_ORBIT
            out = 'Dropped to low orbit'
        
        else:
            print('how did you get here?')
            raise Exception
        
        self.moving_down = False
        return out
    
    def max_thrust(self):
        # available thrust
        thrust = self.thrust
        if self.layer is OrbitalLayer.ATMOSPHERE:
            thrust = 2
        
        # modify available thrust
        if self.order is ShipOrder.STANDARD:
            # no change to thrust
            pass
        if self.moving_up:
            thrust = thrust - 4
        
        return thrust

    def min_thrust(self):
        # available thrust
        thrust = self.thrust
        if self.layer is OrbitalLayer.ATMOSPHERE:
            thrust = 2
        
        # modify available thrust
        if self.order is ShipOrder.STANDARD:
            thrust = thrust / 2
        if self.moving_up:
            thrust = thrust - 4
        return thrust
    
    def do_orbital_decay(self):
        out = []
        if not self.orbital_decay:
            return out
        decay_roll = random.randint(1,6)
        if decay_roll == 1:
            self.hp = self.hp - 1
            if self.hp <= 0:
                destruction_out = self.on_destroy(catastrophic_damage=False)
                for line in destruction_out:
                    out.append(line)
        if decay_roll <= 3:
            out.append(self.move_down())
        else:
            out.append('Orbital decay repaired')
            self.orbital_decay = False
    
    # def draw_change_layer(self, surf):
    #     if self.moving_down:
    #         print('draw moving down indicator')
    #     elif self.moving_up:
    #         print('draw moving up indicator')
    #     return

    def launch_range(self, ships):
        return

if __name__ == "__main__":
    Ship.load_shipDB()