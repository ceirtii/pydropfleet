import pygame
from pygame.locals import *
from helper import *
from ship import *
from game_constants import *
from ground import *
import random
from queue import Queue

class PlayArea(pygame.sprite.Sprite):
    def __init__(self):
       pygame.sprite.Sprite.__init__(self)
       self.image0 = pygame.image.load('Mixed Map reduced.png').convert()
       self.image = self.image0
       self.rect = self.image.get_rect()
       self.scale = 1
       self.dim = (48.0,48.0)
    
    def zoom(self, zoom_increment):
        center = self.rect.center
        desired_dim = self.rect.width * (1 + zoom_increment)
        original_dim = self.image0.get_rect().width
        self.scale = desired_dim / original_dim
        self.image = pygame.transform.rotozoom(self.image0, 0, self.scale)
        self.rect = self.image.get_rect()
        self.rect.center = center
    
    def gridtopixel(self, loc):
        x_pixel = int(self.rect.x + loc[0]/self.dim[0]*self.rect.width)
        y_pixel = int(self.rect.y + loc[1]/self.dim[1]*self.rect.height)
        return (x_pixel, y_pixel)
    
    def pixeltogrid(self, ploc, checkBounds=True):
        (x_pixel, y_pixel) = ploc
        x = (x_pixel - self.rect.x)*self.dim[0]/self.rect.width
        y = (y_pixel - self.rect.y)*self.dim[1]/self.rect.height
        if checkBounds:
            if x < 0: x = 0
            if x > self.dim[0]: x = self.dim[0]
            if y < 0: y = 0
            if y > self.dim[1]: y = self.dim[1]
        return (x, y)
    
    def scalegridtopixel(self, dist):
        return int(dist/self.dim[0]*self.rect.width)
    
    def scale_pixel_to_grid(self, dist):
        return dist/self.rect.width*self.dim[0]

class CombatLog:
    def __init__(self, font_obj, width_frac=.3):
        self.log = []
        self.width = 0
        self.height = 0
        self.rect = None
        self.color = NordColors.nord1
        self.line_font = font_obj
        self.font_color = NordColors.snow0
        self.currentline = 0
        # self.width_frac = width_frac
        self.needs_update = True
        # self.surf = pygame.Surface((0,0))
    
    def draw(self, surf):
        self.width = int(surf.get_width()*.5-350)
        self.height = int(surf.get_height()*.2)
        # self.surf = pygame.Surface((self.width, self.height))
        x = surf.get_width()/2-self.width
        y = surf.get_height()-self.height
        if not self.rect:
            self.rect = pygame.Rect(x,y,self.width,self.height)
        else:
            self.rect.topleft = (x, y)
            self.rect.size = (self.width, self.height)
        pygame.draw.rect(surf, self.color, self.rect)
        
        printloglines = self.log.copy()
        printloglines.reverse()
        # line_font = pygame.font.Font('kooten.ttf', 20)
        line_height = self.line_font.size('')[1]
        lines = int(self.height/line_height) - 1
        if lines < len(printloglines):
            printloglines = printloglines[self.currentline:lines+self.currentline]
        printloglines.reverse()

        line_pixel = 0
        for line in printloglines:
            if 'destroyed' in line or 'damage' in line:
                color = NordColors.aurora0
            elif '->' in line:
                color = NordColors.frost0
            else:
                color = self.font_color
            line_font_surface = self.line_font.render(str(line), True, color)
            surf.blit(line_font_surface,(self.rect.x + line_height/2, self.rect.y + line_pixel + line_height/2))
            line_pixel += line_height
    
    def scroll(self, dir):
        line_height = self.line_font.size('')[1]
        if len(self.log)*line_height < self.height:
            return
        if self.currentline + dir < 0:
            return
        if self.currentline + dir + self.height/line_height - 1 >= len(self.log):
            return
        self.currentline += dir
    
    def append(self, line):
        self.log.append(line)

class FleetPanel:
    def __init__(self, side, major_font, minor_font, width_frac=.2):
        self.battlegroups = []
        self.battlegroups_originalorder = []
        self.width = 350
        self.height = 0
        self.rect = pygame.Rect(0,0,self.width,self.height)
        self.color = NordColors.nord0
        self.line_font = major_font
        self.minor_font = minor_font
        self.side = side
        self.width_frac = width_frac
        self.surf = None
        self.content_height = 0
        self.needs_update = True
        # self.orbital_layer_mask = pygame.image.load('light hatch cropped.png').convert_alpha()
        # self.buffer = 10
    
    def resize(self, surf):
        self.height = surf.get_height()
        self.rect.width = self.width
        self.rect.height = surf.get_height()*4
        self.surf = pygame.Surface((self.width, self.height*4),pygame.SRCALPHA)
        if self.side == 'right':
            self.rect.right = surf.get_width()
    
    def draw(self, surf):
        # self.width = int(surf.get_width()*self.width_frac)
        self.surf.fill(self.color)
        # pygame.gfxdraw.box(surf, self.rect, self.color)

        # line_font = pygame.font.Font('kooten.ttf', 18)
        # minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = self.line_font.size('')[1]
        minor_height = self.minor_font.size('')[1]
        buffer = line_height/2
        y = self.rect.top + buffer
        for bg in self.battlegroups_originalorder:
            bg_top = y
            if bg.state is BattlegroupState.ACTIVATED:
                bg_color = NordColors.nord3
            elif bg.state is BattlegroupState.ACTIVE:
                bg_color = NordColors.frost0
            elif bg.state is BattlegroupState.PENDING_ACTIVATION:
                bg_color = NordColors.frost2
            elif bg.state is BattlegroupState.NOT_YET_ACTIVE:
                bg_color = NordColors.snow0
            elif bg.state is BattlegroupState.DESTROYED:
                bg_color = NordColors.aurora0
            else:
                raise Exception
            font_render = self.line_font.render(str(bg),True,bg_color)
            bg.rect = font_render.get_rect()
            bg.rect.topleft = (self.rect.left+buffer, y)
            self.surf.blit(font_render,(buffer, y))
            y = y + line_height + buffer
            for group in bg.groups:

                group_top = y - buffer/2

                for ship in group.ships:
                    if ship.state in [ShipState.FIRING, ShipState.MOVING]:
                        ship_font_color = NordColors.frost0
                    elif ship.state is ShipState.DESTROYED:
                        ship_font_color = NordColors.aurora0
                    elif ship.state in [ShipState.ACTIVATED, ShipState.LAUNCHED]:
                        ship_font_color = NordColors.frost3
                    else:
                        ship_font_color = NordColors.snow0

                    font_render = self.line_font.render(f'{ship.faction} {ship.name}', True, ship_font_color)
                    class_render = self.minor_font.render(f'{ship.shipclass}-class {ship.shiptype}', 
                            True, 
                            ship_font_color)

                    if ship.layer is OrbitalLayer.HIGH_ORBIT:
                        layer_str = 'HIGH'
                        if ship.moving_down:
                            layer_str = layer_str + ' -> LOW'
                    elif ship.layer is OrbitalLayer.LOW_ORBIT:
                        layer_str = 'LOW'
                        if ship.moving_down:
                            layer_str = layer_str + ' -> ATMO'
                        elif ship.moving_up:
                            layer_str = layer_str + ' -> HIGH'
                    else:
                        layer_str = 'ATMO'
                        if ship.moving_up:
                            layer_str = layer_str + ' -> LOW'
                    
                    if 'ATMO' in layer_str and not ship.atmospheric:
                        layer_color = NordColors.aurora0
                    else:
                        layer_color = NordColors.snow0

                    layer_str_width = self.minor_font.size(layer_str)[0]
                    layer_render = self.minor_font.render(layer_str, True, layer_color)
                    box_height = line_height+2*minor_height+buffer
                    
                    ship.panel_rect.left = 1.5*buffer
                    ship.panel_rect.top = y-buffer/2
                    ship.panel_rect.width = self.width-3*buffer
                    ship.panel_rect.height = box_height

                    pygame.draw.rect(self.surf, NordColors.nord2, ship.panel_rect)
                    # hatch_surf = pygame.Surface((ship.panel_rect.width, ship.panel_rect.height))
                    # hatch_surf.blit(self.orbital_layer_mask, (0,0))
                    # self.surf.blit(pygame.transform.scale(self.orbital_layer_mask, (ship.panel_rect.width, ship.panel_rect.height)), ship.panel_rect.topleft)

                    hull_string = f'{ship.hp}/{ship.hull}'
                    hull_string_width = self.line_font.size(hull_string)[0]
                    hull_render = self.line_font.render(hull_string, True, NordColors.snow1)
                    self.surf.blit(hull_render, (self.rect.width-2*buffer-hull_string_width, y))

                    if ship.highlight:
                        pygame.draw.rect(self.surf, NordColors.frost0, ship.panel_rect, 2)
                    elif ship.hover:
                        pygame.draw.rect(self.surf, NordColors.frost2, ship.panel_rect, 2)
                    self.surf.blit(font_render, (2 * buffer, y))
                    y = y + line_height
                    self.surf.blit(class_render, (2 * buffer, y))
                    self.surf.blit(layer_render, ((self.rect.width-2*buffer-layer_str_width, y)))
                    y = y + minor_height + buffer

                    hull_bar_length = ship.panel_rect.width-2*buffer
                    hp_start = ship.panel_rect.left+buffer
                    hp_end = ship.panel_rect.left+buffer+hull_bar_length*ship.hp/ship.hull
                    hull_end = hp_start+hull_bar_length

                    if ship.hp != 0:
                        pygame.draw.line(self.surf,NordColors.aurora3,(hp_start,y),(hp_end,y),4)
                    
                    if hp_end < hull_end:
                        pygame.draw.line(self.surf,NordColors.aurora0,(hp_end,y),(hull_end,y),4)

                    ship.panel_rect.left = 1.5*buffer + self.rect.left
                    ship.panel_rect.top = ship.panel_rect.top + self.rect.top + buffer/2

                    y = y + 2*buffer   
                
                group.rect.top = group_top
                group.rect.height = y-buffer-group_top
                group.rect.left = self.rect.left
                group.rect.width = 1.5*buffer
                # pygame.draw.rect(surf, NordColors.frost0, group.rect)
                if group.is_selected:
                    group_color = NordColors.frost0
                else:
                    group_color = NordColors.frost2
                pygame.draw.line(self.surf,group_color,(buffer,group_top),(buffer,y-buffer),4)
                y = y + buffer

            bg_boundary = pygame.Rect(.5*buffer, bg_top-.5*buffer, self.width-buffer, y-bg_top-.5*buffer)
            if bg.state is BattlegroupState.ACTIVE or bg.hovered:
                pygame.draw.rect(self.surf, NordColors.frost0, bg_boundary, 2)
            elif bg.state is BattlegroupState.PENDING_ACTIVATION:
                pygame.draw.rect(self.surf, NordColors.frost2, bg_boundary, 2)

        self.content_height = y
        surf.blit(self.surf,self.rect.topleft)

    def scroll(self, dir):
        scrollspeed = 20
        if self.rect.y == 0 and dir > 0:
            return
        if self.content_height <= self.height - self.rect.y and dir < 0:
            return
        self.rect.y = self.rect.y + dir*scrollspeed

class InfoPanel:
    def __init__(self, major_font, minor_font, height_frac=.2, width_frac=.3):
        self.selectedship = None
        self.rect = None
        self.height_frac = height_frac
        # self.width_frac = width_frac
        self.color = NordColors.nord2
        self.buffer = 10
        self.line_font = major_font
        self.minor_font = minor_font
        self.hovered_gun = None
        self.selected_gun = None
        self.needs_update = True
        self.targetpanel = None
    
    def change_selected_obj(self, obj):
        if self.selectedship:
            self.selectedship.is_selected = False
            try:
                if self.selectedship.highlight:
                    self.selectedship.highlight = False
            except AttributeError:
                print('no highlight attribute')

        if obj is None or self.selectedship is obj:
            self.selectedship = None
        else:
            self.selectedship = obj
            obj.is_selected = True
            try:
                obj.highlight = True
            except AttributeError:
                print('no highlight attribute')
        return obj

    def draw(self, surf):
        self.hovered_gun = None
        self.rect = pygame.Rect(surf.get_width()/2,
                surf.get_height()*(1-self.height_frac),
                surf.get_width()*.5-350,
                surf.get_height()*self.height_frac)
        pygame.draw.rect(surf, self.color, self.rect)
        
        # line_font = pygame.font.Font('kooten.ttf', 18)
        # minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = self.line_font.size('')[1]
        minor_height = self.minor_font.size('')[1]

        y = self.rect.top + self.buffer
        if self.selectedship:
            header_str = f'{self.selectedship.__class__.__name__} Info'
        else:
            header_str = 'Info'
        header_render = self.line_font.render(header_str,True,NordColors.snow0)
        surf.blit(header_render, (self.rect.left+self.buffer,y))
        y = y + line_height# + self.buffer

        # print(f'selected ship {self.selectedship}')
        if not self.selectedship:
            return

        elif isinstance(self.selectedship, Ship):
            shipname_render = self.line_font.render(f'{self.selectedship.name}, {self.selectedship.shipclass}-class {self.selectedship.shiptype}', True, NordColors.snow0)
            surf.blit(shipname_render, (self.rect.left+self.buffer,y))
            y = y + line_height
            for gun in self.selectedship.guns:
                if gun.state is GunState.TARGETING:
                    gun_text_color = NordColors.frost0
                else:
                    gun_text_color = NordColors.frost3
                gun_render = self.minor_font.render(str(gun), True, gun_text_color)
                gunpos = (self.rect.left+self.buffer,y)
                gun.rect = gun_render.get_rect()
                gun.rect.topleft = gunpos
                surf.blit(gun_render, gunpos)
                if gun is self.selected_gun:
                    pygame.draw.rect(surf, NordColors.frost1, gun.rect, 1)
                elif gun.rect.collidepoint(pygame.mouse.get_pos()):
                    self.hovered_gun = gun
                    pygame.draw.rect(surf, NordColors.frost1, gun.rect, 1)
                    # print(f'{gun.guntype} hovered')
                y = y + minor_height
            y = y + minor_height/2

            shiporder_str = f'Orders: {self.selectedship.order.name}'
            shiporder_render = self.minor_font.render(shiporder_str, True, NordColors.frost0)
            surf.blit(shiporder_render, (self.rect.left+self.buffer,y))
            y = y + minor_height

            sig_str = f'Signature: {self.selectedship.sig}\"'
            if self.selectedship.active_sig != self.selectedship.sig:
                sig_str = sig_str + f' ({self.selectedship.active_sig}\" eff.)'
            sig_render = self.minor_font.render(sig_str, True, NordColors.snow0)
            surf.blit(sig_render, (self.rect.left+self.buffer,y))
            y = y + minor_height

            launch_str = 'Launch: '
            if self.selectedship.fighters:
                launch_str = launch_str + f'Fighters and Bombers ({len(self.selectedship.fighters.squadrons)})'
            if self.selectedship.dropships:
                launch_str = launch_str + f'Dropships ({len(self.selectedship.dropships.squadrons)})'
            if self.selectedship.bulk_landers:
                launch_str = launch_str + f'Bulk Landers ({len(self.selectedship.bulk_landers.squadrons)})'

            if launch_str != 'Launch: ':
                launch_render = self.minor_font.render(launch_str, True, NordColors.snow0)
                surf.blit(launch_render, (self.rect.left+self.buffer,y))
                y = y + minor_height

            ailments = self.selectedship.get_crippling_effects()
            if ailments:
                ailments = ', '.join(ailments)
                ailments_render = self.minor_font.render(ailments, True, NordColors.snow0)
                surf.blit(ailments_render, (self.rect.left+self.buffer,y))
        
        elif isinstance(self.selectedship, Battlegroup):
            bgname_render = self.line_font.render(str(self.selectedship), True, NordColors.snow0)
            surf.blit(bgname_render, (self.rect.left+self.buffer,y))

        elif isinstance(self.selectedship, ShipGroup):
            groupname_render = self.line_font.render(str(self.selectedship), True, NordColors.snow0)
            surf.blit(groupname_render, (self.rect.left+self.buffer,y))

    def scroll(self, dir):
        pass

    def update(self):
        if self.selected_gun and self.selected_gun.state is not GunState.TARGETING:
            self.selected_gun = None

class BattlegroupState(Enum):
    NOT_YET_ACTIVE = auto()
    ACTIVE = auto()
    ACTIVATED = auto()
    PENDING_ACTIVATION = auto()
    DESTROYED = auto()

class Battlegroup:
    def __init__(self, size, points):
        self.size = size
        # self.sr = int(sr)
        self.points = points
        self.groups = []
        self.state = BattlegroupState.NOT_YET_ACTIVE
        self.hovered = False
        self.up_arrow_rect = None
        self.down_arrow_rect = None
        self.player = None
        self.is_selected = False

        # self.line_font = None
        # self.minor_font = None
        # self.surf = None
        self.rect = pygame.Rect(0,0,0,0)
        # self.update_sr()

    def __str__(self):
        out_str = f'SR{self.sr} {self.size} {self.points} pts'
        # for group in self.groups:
        #     out_str += f'\n{len(group)} {group[0].shipclass}'
        return out_str
    
    def __iter__(self):
        return iter(self.groups)
    
    def printships(self):
        groups  = [str(group) for group in self.groups]
        out_str = ', '.join(groups)
        return out_str
    
    def update(self):
        if self.state is BattlegroupState.ACTIVE:
            for ship in self.get_ships():
                if ship.state is ShipState.MOVING or ship.state is ShipState.FIRING:
                    # print('ships left to activate')
                    return
            print('all ships activated, make battlegroup activated')
            self.state = BattlegroupState.ACTIVATED
    
    def activate(self):
        self.state = BattlegroupState.ACTIVE
        for ship in self.get_ships():
            if ship.state is not ShipState.DESTROYED:
                ship.has_launched = False
                ship.set_state(ShipState.MOVING)
                for gun in ship.guns:
                    gun.state = GunState.TARGETING
    
    def update_sr(self):
        sr = 0
        for ship in self.get_ships():
            if ship.state is not ShipState.DESTROYED:
                tonnage = Ship.ship_tonnage[ship.tonnage]
                sr = sr + tonnage
        self.sr = sr
        return sr
    
    def check_destroyed(self):
        if self.state is BattlegroupState.DESTROYED:
            return True
        all_ships_destroyed = True
        for ship in self.get_ships():
            all_ships_destroyed = ship.state is ShipState.DESTROYED and all_ships_destroyed
        if all_ships_destroyed:
            # if bg in self.p1_bg_queue:
            #     self.p1_bg_queue.remove(bg)
            # if bg in self.p2_bg_queue:
            #     self.p2_bg_queue.remove(bg)
            print(f'all ships destroyed in {self}, setting as destroyed')
            self.state = BattlegroupState.DESTROYED
        return all_ships_destroyed
    
    def get_ships(self):
        out = []
        for group in self.groups:
            out = out + group.ships
        return out
    
    def check_shipstate(self, state):
        out = []
        for group in self.groups:
            out = out + group.check_shipstate(state)
        return out
    
    def resize(self, surf):
        # line_height = self.line_font.size('')[1]
        # minor_height = self.minor_font.size('')[1]
        # buffer = line_height/2
        # height = 1.5*buffer+line_height
        
        return

    def draw(self, surf):
        return# self.surf
    
class ShipGroup:
    def __init__(self):
        self.ships = []
        self.rect = pygame.Rect(0,0,0,0)
        self.is_selected = False
        self.destroyed = False
    
    def __str__(self):
        return f'{len(self.ships)} {self.ships[0].shipclass}'
    
    def __iter__(self):
        return iter(self.ships)
    
    def check_shipstate(self, state):
        out = []
        for ship in self.ships:
            if ship.state is state:
                out.append(ship)
        return out
    
    def can_launch(self, launch_type):
        if self.destroyed:
            return False
        else:
            out = False
            for ship in self.ships:
                out = out or ship.can_launch(launch_type)
            return out

class BattlegroupPlanner:
    def __init__(self, battlegroups, major_font, minor_font):
        self.bgs = battlegroups
        self.width = 300
        self.rect = pygame.Rect(0,0,0,0)
        self.major_font = major_font
        self.minor_font = minor_font
        self.needs_update = False
    
    def draw(self, surf):
        x = (surf.get_width()-self.width)/2
        y = 200
        major_font_height = self.major_font.size('')[1]
        minor_font_height = self.minor_font.size('')[1]
        buffer = major_font_height/2
        height = len(self.bgs)*(2*major_font_height+buffer)+buffer
        pygame.draw.rect(surf,NordColors.nord1,pygame.Rect(x-buffer,y-buffer,self.width+2*buffer,height))
        arrow_offset = 20
        # print(f'in draw {self.bgs}')
        for index, bg in enumerate(self.bgs):
            bg_y = y
            mousepos = pygame.mouse.get_pos()
            bg_render = self.major_font.render(f'{str(bg)}', True, NordColors.snow0)
            surf.blit(bg_render, (x+arrow_offset,y))
            pos_render = self.major_font.render(str(index+1), True, NordColors.snow1)
            surf.blit(pos_render, (x+self.width-buffer,y))
            if index != 0:
                up_arrow_color = NordColors.snow0
            else:
                up_arrow_color = NordColors.nord1
            up_arrow_render = self.major_font.render('/\\', True, up_arrow_color)
            bg.up_arrow_rect = up_arrow_render.get_rect()
            bg.up_arrow_rect.topleft = (x,y)
            surf.blit(up_arrow_render, (x,y))
            y = y + major_font_height
            bg_ships_render = self.minor_font.render(bg.printships(), True, NordColors.frost0)
            surf.blit(bg_ships_render, (x+arrow_offset,y))
            if index != len(self.bgs)-1:
                down_arrow_color = NordColors.snow0
            else:
                down_arrow_color = NordColors.nord1
            down_arrow_render = self.major_font.render('\\/', True, down_arrow_color)                
            bg.down_arrow_rect = down_arrow_render.get_rect()
            bg.down_arrow_rect.topleft = (x,y)
            # print(bg.down_arrow_rect)
            # print(f'setting bg down arrow rect at {(x,y)}')
            surf.blit(down_arrow_render, (x,y))
            y = y + major_font_height + buffer
            select_box = pygame.Rect(x,bg_y,self.width,y-bg_y)
            bg.hovered = select_box.collidepoint(mousepos)

class PlayerPhase(Enum):
    MOVING = auto()
    FIRING = auto()

class GameController:
    def __init__(self, title_font, major_font, minor_font):
        self.current_state = 'Setup'
        self.title_font = title_font
        self.rect = pygame.Rect(0,0,0,0)
        self.major_font = major_font
        self.minor_font = minor_font
        self.p1_battlegroups = []
        self.p2_battlegroups = []
        self.p1_bg_queue = []
        self.p2_bg_queue = []
        self.active_player = None
        self.bg_plan_screen = None
        self.round = 1
        self.firstplayer = 0
        self.p1_button = None
        self.p2_button = None
        self.active_bg = None
        self.combatlog = None
        self.target_queue = None
        self.launch_queue = None
        self.turn = 1
        self.resolve_attacks = False
        self.resolve_launch = False
        self.player1 = None
        self.player2 = None
        # self.needs_update = True
        # self.activation_queue = Queue()
        self.display_launching_ship = None
        # self.display_launch_asset = None
        self.active_group = None
        self.launchsel_panel = LaunchGroupSelectionPanel(major_font, minor_font)
        self.launchresolve_panel = LaunchAssetResolvePanel(major_font, minor_font)
        self.launch_done = False
        self.passed_turn = False
        self.dropships_resolved = False
    
    def draw(self, surf):
        self.launchsel_panel.draw(surf)
        self.launchresolve_panel.draw(surf)
        state_text = f'{self.current_state}'
        gamephase_render = self.title_font.render(state_text, True, NordColors.snow0)
        gamephase_render_size = self.title_font.size(state_text)
        surf.blit(gamephase_render, ((surf.get_width()-gamephase_render_size[0])/2,0))

        if ('Activate' in self.current_state and not self.resolve_attacks) or 'Select' in self.current_state:
            # don't draw end turn button
            self.rect = pygame.Rect(0,0,0,0)
        else:
            if self.resolve_attacks:
                endturn = 'Resolve Attack'
            elif self.resolve_launch:
                endturn = 'Resolve Launch'
            elif 'Launch' in self.current_state and 'Resolve' not in self.current_state:
                if self.launch_queue.is_empty():
                    endturn = 'Next Phase'
                else:
                    endturn = 'Finish Launching'
            else:
                endturn = 'Next Phase'
            endturnbutton_render = self.major_font.render(endturn, True, NordColors.snow0)
            endturnbutton_render_width = self.major_font.size(endturn)
            self.rect.left = (surf.get_width()-endturnbutton_render_width[0])/2
            self.rect.top = gamephase_render_size[1]
            self.rect.size = endturnbutton_render_width
            pygame.draw.rect(surf, NordColors.nord3, self.rect)
            surf.blit(endturnbutton_render, (self.rect.left,self.rect.top))
        
        # if self.display_launching_ship:
        #     ship = self.display_launching_ship
        #     panel_width = 400
        #     x = (surf.get_width()-panel_width)/2
        #     y = 200
        #     major_font_size = self.major_font.size('P2')
        #     buffer = major_font_size[1]/2
        #     height = major_font_size[1]*3+3*buffer
        #     launch_ship_rect = pygame.Rect(x-buffer,y-buffer,panel_width+2*buffer,height)
        #     pygame.draw.rect(surf, NordColors.nord1, launch_ship_rect)

        #     ship_render = self.major_font.render(str(ship), True, NordColors.snow0)
        #     surf.blit(ship_render, (x, y))
        #     y = y + major_font_size[1]
            
        #     if 'Bomber' in self.current_state:
        #         for launch in ship.launch:
        #             if launch.launch_type == 'Fighters & Bombers':
        #                 bombers = launch
        #         bomber_render = self.major_font.render('Launching Bombers:', True, NordColors.snow0)
        #         surf.blit(bomber_render, (x, y))
        #         y = y + major_font_size[1]

        #         count_str = f'{bombers.launching_count}/{bombers.count - bombers.launched_count} available'
        #         count_render = self.major_font.render(count_str, True, NordColors.snow0)
        #         surf.blit(bomber_render, (x, y))
        #         y = y + major_font_size[1]

        if 'Planning' in self.current_state:
            self.bg_plan_screen.draw(surf)
        
        if 'Select Player Order' in self.current_state:
            panel_width = 400
            x = (surf.get_width()-panel_width)/2
            y = 200
            title_font_size = self.title_font.size('P2')
            buffer = title_font_size[1]/2
            height = title_font_size[1]*2+3*buffer
            pygame.draw.rect(surf, NordColors.nord1, pygame.Rect(x-buffer,y-buffer,panel_width+2*buffer,height))
            panel_title = f'Player {self.firstplayer}, select who goes first:'
            panel_title_render = self.title_font.render(panel_title, True, NordColors.snow0)
            surf.blit(panel_title_render,(x,y))
            y = y + title_font_size[1] + buffer

            p1_button_render = self.title_font.render('P1', True, NordColors.snow1)
            p1_button_loc = (x,y)
            self.p1_button = p1_button_render.get_rect()
            self.p1_button.topleft = p1_button_loc
            surf.blit(p1_button_render,p1_button_loc)

            p2_button_render = self.title_font.render('P2', True, NordColors.snow1)
            p2_button_loc = (x+panel_width-title_font_size[0],y)
            self.p2_button = p2_button_render.get_rect()
            self.p2_button.topleft = p2_button_loc
            surf.blit(p2_button_render,p2_button_loc)
    
    def next_phase(self, next_player=None):
        p1_str = ', '.join([str(bg) for bg in self.p1_bg_queue])
        p2_str = ', '.join([str(bg) for bg in self.p2_bg_queue])
        print(f'p1 bg queue: {p1_str}')
        print(f'p2 bg queue: {p2_str}')

        # if self.resolve_attacks:
        #     while not self.target_queue.is_empty():
        #         print('useless code?')
        #         gun, target = self.target_queue.pop()
        #         result = gun.shoot(target)
        #         print(result)
        #         for line in result:
        #             self.combatlog.append(line)
        #     return
        # if 'Cleanup' in self.current_state:
        #     print('Battlegroup activations complete, perform turn cleanup')

        if 'Setup' in self.current_state:# or 'Roundup' in self.current_state:
            print(f'{self.current_state} phase complete, plan battlegroup activation order')
            self.current_state = 'Planning (P1)'
            for fleetlist in [self.p1_battlegroups, self.p2_battlegroups]:
                print(f'resetting ships for {fleetlist}')
                index = 0
                while index < len(fleetlist):
                    print(f'checking battlegroup at index {index}')
                    bg = fleetlist[index]
                    if bg.state is BattlegroupState.DESTROYED:
                        print('removing destroyed battlegroup')
                        fleetlist.remove(bg)
                    else:
                        bg.state = BattlegroupState.NOT_YET_ACTIVE
                        for ship in bg.get_ships():
                            if ship.state is ShipState.DESTROYED:
                                continue
                            ship.state = ShipState.NOT_YET_ACTIVATED
                        index = index + 1
            for bg in self.p1_battlegroups:
                self.p1_bg_queue.append(bg)
            self.bg_plan_screen = BattlegroupPlanner(self.p1_bg_queue, self.major_font, self.minor_font)

        elif self.current_state == 'Planning (P1)':
            print(f'player 1 finished planning, player 2 plan battlegroup activation order')
            for bg in self.p2_battlegroups:
                self.p2_bg_queue.append(bg)
            self.bg_plan_screen.bgs = self.p2_bg_queue
            self.current_state = 'Planning (P2)'

        elif self.current_state == 'Planning (P2)' or 'Activate Battlegroup' in self.current_state:
            print(f'activate first battlegroup in round {self.round}')
            self.current_state = f'Turn {self.turn}: Select Player Order'
            # index = self.round-1
            # print(f'checking battlegroups at index {index}')
            print(f'player 1 battlegroups contains {len(self.p1_battlegroups)} bgs')
            print(f'player 2 battlegroups contains {len(self.p2_battlegroups)} bgs')

            if not self.p1_bg_queue and not self.p2_bg_queue:
                print('all battlegroups activated, turn roundup')

                print('removing destroyed battlegroups')
                self.combatlog.append('removing destroyed battlegroups')
                for bg in self.p1_battlegroups + self.p2_battlegroups:
                    bg_destroyed = bg.check_destroyed()
                    if bg_destroyed:
                        print(f'battlegroup {bg} destroyed!')
                        self.combatlog.append(f'battlegroup {bg} destroyed!')
                
                self.combatlog.append('all battlegroups activated, turn roundup')

                print('determine initiative for ground combat and launch assets')
                p1_init = random.randint(1,6)
                p2_init = random.randint(1,6)

                while p1_init == p2_init:
                    p1_init = random.randint(1,6)
                    p2_init = random.randint(1,6)
                
                self.combatlog.append(f'player 1 rolled {p1_init}')
                self.combatlog.append(f'player 2 rolled {p2_init}')
                if p1_init < p2_init:
                    self.player_initiative = self.player2
                    self.active_player = self.player2
                    self.combatlog.append(f'player 2 wins initiative')
                else:
                    self.player_initiative = self.player1
                    self.active_player = self.player1
                    self.combatlog.append(f'player 1 wins initiative')
                
                self.current_state = f'Turn {self.turn}: Roundup (Ground Combat)'
                self.round = 1

            elif self.p1_bg_queue and self.p2_bg_queue:
                print('battlegroups left to activate')
                p1_sr = self.p1_bg_queue[0].sr
                self.p1_bg_queue[0].state = BattlegroupState.ACTIVE

                p2_sr = self.p2_bg_queue[0].sr
                self.p2_bg_queue[0].state = BattlegroupState.ACTIVE

                if p1_sr == p2_sr:
                    self.firstplayer = random.choice([1,2])
                    self.combatlog.append(f'Battlegroups have same strategy rating, player {self.firstplayer} picks')
                else:
                    if p1_sr < p2_sr:
                        self.firstplayer = 1
                    else:
                        self.firstplayer = 2
                    self.combatlog.append(f'Player {self.firstplayer} picks, has lower strategy rating {min(p1_sr, p2_sr)}')

            elif self.p2_bg_queue:
                print(f'p1 battlegroups all activated, continue activating player 2 battlegroups')
                self.active_bg = self.p2_bg_queue[0]
                self.active_bg.activate()
                # for bg in self.p2_bg_queue:
                #     bg.state = BattlegroupState.PENDING_ACTIVATION
                self.current_state = f'Turn {self.turn}: P2 Activate Battlegroup'

            elif self.p1_bg_queue:
                print(f'p2 battlegroups all activated, continue activating player 1 battlegroups')
                self.active_bg = self.p1_bg_queue[0]
                self.active_bg.activate()
                # for bg in self.p1_bg_queue:
                #     bg.state = BattlegroupState.PENDING_ACTIVATION
                self.current_state = f'Turn {self.turn}: P2 Activate Battlegroup'
            else:
                print('how did you get here?')
                raise Exception
        
        elif 'Ground Combat' in self.current_state:
            print('resolve ground combat')
            print('resolve launch assets')
            self.player1.add_launch_assets()
            self.player2.add_launch_assets()
            self.active_player = self.player_initiative
            # if self.player_initiative is self.player1:
            #     self.active_player = self.player1
            #     for ship in self.player1.bomber_launch:
            #         ship.state = ShipState.LAUNCHING

            # elif self.player_initiative is self.player2:
            #     self.active_player = self.player2
            #     for ship in self.player2.bomber_launch:
            #         ship.state = ShipState.LAUNCHING
            self.launchsel_panel.set_launch_list(self.active_player.bomber_launch, 'Bomber')
            self.launchsel_panel.active = True
            self.current_state = f'Turn {self.turn}: Roundup (Launch Bombers)'
        
        elif 'Launch Bombers' in self.current_state:
            if self.launchsel_panel.active_group:
                for ship in self.launchsel_panel.active_group:
                    ship.set_state(ShipState.LAUNCHED)
                self.active_player.bomber_launch = [
                        ship for ship in self.active_player.bomber_launch 
                        if ship not in self.launchsel_panel.active_group
                        ]
                self.launchsel_panel.active_group = None
            else:
                print('passed turn without activating group')
                if self.passed_turn:
                    print('turn passed twice, moving to next phase')
                    self.launch_done = True
                    self.passed_turn = False
                else:
                    self.passed_turn = True
            no_bombers = not self.player1.bomber_launch and not self.player2.bomber_launch
            if self.launch_done or no_bombers:
                print('bomber launch done, next phase')
                self.active_player = self.player_initiative
                self.launchsel_panel.set_launch_list(self.active_player.fighter_launch, 'Fighter')
                self.launchsel_panel.active = True
                self.current_state = f'Turn {self.turn}: Roundup (Launch Fighters)'
                self.launch_done = False
            else:
                if self.active_player is self.player1:
                    print('player 1 finished')
                    if self.player2.bomber_launch:
                        print('player 2 has bombers that can launch')
                        self.active_player = self.player2
                    else:
                        print('player 1 does not have bombers to launch')
                elif self.active_player is self.player2:
                    if self.player1.bomber_launch:
                        self.active_player = self.player1
                self.launchsel_panel.set_launch_list(self.active_player.bomber_launch, 'Bomber')
                self.launchsel_panel.active = True
        
        elif 'Launch Fighters' in self.current_state:
            if self.launchsel_panel.active_group:
                for ship in self.launchsel_panel.active_group:
                    ship.set_state(ShipState.LAUNCHED)
                self.active_player.fighter_launch = [
                        ship for ship in self.active_player.fighter_launch 
                        if ship not in self.launchsel_panel.active_group
                        ]
                self.launchsel_panel.active_group = None
            else:
                print('passed turn without activating group')
                if self.passed_turn:
                    print('turn passed twice, moving to next phase')
                    self.launch_done = True
                    self.passed_turn = False
                else:
                    self.passed_turn = True
            no_fighters = not self.player1.fighter_launch and not self.player2.fighter_launch
            if self.launch_done or no_fighters:
                print('fighter launch done, next phase')
                self.active_player = self.player_initiative
                drop_launch = self.active_player.dropship_launch + self.active_player.bulklander_launch
                self.launchsel_panel.set_launch_list(drop_launch, 'Drop')
                self.launchsel_panel.active = True
                self.current_state = f'Turn {self.turn}: Roundup (Launch Dropships and Bulk Landers)'
                self.launch_done = False
            else:
                if self.active_player is self.player1:
                    print('player 1 finished')
                    if self.player2.fighter_launch:
                        print('player 2 has fighters that can launch')
                        self.active_player = self.player2
                    else:
                        print('player 1 does not have fighters to launch')
                elif self.active_player is self.player2:
                    if self.player1.fighter_launch:
                        self.active_player = self.player1
                self.launchsel_panel.set_launch_list(self.active_player.fighter_launch, 'Fighter')
                self.launchsel_panel.active = True
        
        elif 'Launch Dropships and Bulk Landers' in self.current_state:
            self.display_launching_ship = None
            # self.display_launch_asset = None
            self.current_state = f'Turn {self.turn}: Roundup (Resolve Launch Assets)'
            self.resolve_launch = True
        
        elif 'Resolve Launch Assets' in self.current_state:
            if not self.launch_queue.is_empty():
                print('resolve launch')
                if self.launchresolve_panel.active_player is None:
                    self.launchresolve_panel.active_player = self.player_initiative
                if self.launchresolve_panel.launch_queue is None:
                    self.launchresolve_panel.launch_queue = self.launch_queue
                if not self.dropships_resolved:
                    print('resolve dropships and bulk landers')
                    self.combatlog.append('resolve dropships and bulk landers')
                    for (item, launch_assets) in self.launch_queue:
                        # print(item)
                        if isinstance(item, Sector):
                            print(f'resolving drops in {str(item)}')
                    self.dropships_resolved = True
                else:
                    self.launchresolve_panel.active = True
            else:
                print('resolve damage control')
                self.resolve_launch = False
                self.dropships_resolved = False
                self.launchresolve_panel.active_player = None
                bgs = self.p1_battlegroups + self.p2_battlegroups
                for bg in bgs:
                    for ship in bg.get_ships():
                        dc_results = ship.do_damage_control()
                        if dc_results:
                            self.combatlog.append(f'{ship} doing damage control')
                            for line in dc_results:
                                self.combatlog.append(line)
                self.current_state = f'Turn {self.turn}: Roundup (Damage Control)'

        elif 'Damage Control' in self.current_state:
            print('resolve orbital decay')
            bgs = self.p1_battlegroups + self.p2_battlegroups
            for bg in bgs:
                for ship in bg.get_ships():
                    dc_results = ship.do_orbital_decay()
                    if dc_results:
                        self.combatlog.append(f'{ship} doing damage control')
                        for line in dc_results:
                            self.combatlog.append(line)
            self.current_state = f'Turn {self.turn}: Roundup (Orbital Decay)'

        elif 'Orbital Decay' in self.current_state:
            print('distribute victory points')
            self.turn = self.turn + 1
            self.current_state = 'Setup'
            self.next_phase()

        elif 'Select Player Order' in self.current_state:
            self.current_state = f'Turn {self.turn}: P{next_player} Activate Battlegroup'
            if next_player == 1:
                self.p2_bg_queue[0].state = BattlegroupState.PENDING_ACTIVATION
                self.active_bg = self.p1_bg_queue[0]
            elif next_player == 2:
                self.p1_bg_queue[0].state = BattlegroupState.PENDING_ACTIVATION
                self.active_bg = self.p2_bg_queue[0]
            else:
                print('how did you get here?')
                raise Exception
            self.active_bg.activate()
            self.combatlog.append(f'activating {self.active_bg}')
        return self.current_state
        # print(f'now on phase {self.current_state}')
    
    def update(self):
        # for bg in self.p1_battlegroups + self.p2_battlegroups:
            # print(f'checking battlegroup {bg}')
                # try:
                #     self.p1_battlegroups.remove(bg)
                # except Exception:
                #     pass
                # try:
                #     self.p2_battlegroups.remove(bg)
                # except Exception:
                #     pass
                
        if 'Activate' in self.current_state:
            self.active_bg.update()
            if self.active_bg.state is BattlegroupState.ACTIVATED:
                # print('active battlegroup done, resolve queued attacks')
                if not self.target_queue.is_empty():
                    self.resolve_attacks = True
                    return
                self.resolve_attacks = False
                
                # try:
                    # while self.p1_battlegroups[self.round-1].state is BattlegroupState.DESTROYED:# and self.p1_battlegroups[self.round]:
                    #     print(f'removing destroyed battlegroup {self.p1_battlegroups[self.round-1]}')
                    #     self.p1_battlegroups.pop(self.round-1)
                        # self.p1_battlegroups[self.round-1].state = BattlegroupState.PENDING_ACTIVATION
                # except IndexError:
                #     p1_activated = True

                # try:
                    # while self.p2_battlegroups[self.round-1].state is BattlegroupState.DESTROYED:# and self.p2_battlegroups[self.round]:
                    #     print(f'removing destroyed battlegroup {self.p2_battlegroups[self.round-1]}')
                    #     self.p2_battlegroups.pop(self.round-1)
                        # self.p2_battlegroups[self.round-1].state = BattlegroupState.PENDING_ACTIVATION
                # except IndexError:
                #     p2_activated = True

                print('remove all destroyed battlegroups')
                print('checking player 1')
                index = 0
                while index < len(self.p1_bg_queue):
                    bg = self.p1_bg_queue[index]
                    if bg.state is BattlegroupState.PENDING_ACTIVATION:
                        if bg.check_destroyed():
                            print('battlegroup pending activation has been destroyed! removing this battlegroup and activating next available battlegroup')
                            self.p1_bg_queue.pop(index)
                            try:
                                next_bg = self.p1_bg_queue[index]
                                print('make sure next battlegroup can be activated')
                                if next_bg.state is BattlegroupState.NOT_YET_ACTIVE:
                                    next_bg.state = BattlegroupState.PENDING_ACTIVATION
                            except IndexError:
                                print('no next battlegroup to activate')
                                break
                        else:
                            print('battlegroup pending activation not destroyed')
                            index = index + 1
                    elif bg.check_destroyed():
                            print('battlegroup destroyed! removing from activation queue')
                            self.p1_bg_queue.pop(index)
                    else:
                        print('battlegroup not destroyed')
                        index = index + 1

                print('checking player 2')
                index = 0
                while index < len(self.p2_bg_queue):
                    bg = self.p2_bg_queue[index]
                    print(f'checking {bg}')
                    if bg.state is BattlegroupState.PENDING_ACTIVATION:
                        print(f'battlegroup pending activation')
                        if bg.check_destroyed():
                            print('battlegroup pending activation has been destroyed! removing this battlegroup and activating next available battlegroup')
                            self.p2_bg_queue.pop(index)
                            try:
                                next_bg = self.p2_bg_queue[index]
                                print('make sure next battlegroup can be activated')
                                if next_bg.state is BattlegroupState.NOT_YET_ACTIVE:
                                    next_bg.state = BattlegroupState.PENDING_ACTIVATION
                            except IndexError:
                                print('no next battlegroup to activate')
                                break
                        else:
                            print('battlegroup pending activation not destroyed')
                            index = index + 1
                    elif bg.check_destroyed():
                            print('battlegroup destroyed! removing from activation queue')
                            self.p2_bg_queue.pop(index)
                    else:
                        print('battlegroup not destroyed')
                        index = index + 1

                print('check if opposing battlegroup exists')
                if self.active_bg.player is self.player1:
                    if not self.p2_bg_queue:
                        print('player 2 queue empty, continuing player 1 activations')
                        self.p1_bg_queue.pop(0)
                        self.round = self.round + 1
                        self.next_phase()
                        return

                elif self.active_bg.player is self.player2:
                    if not self.p1_bg_queue:
                        print('player 1 queue empty, continuing player 2 activations')
                        self.p2_bg_queue.pop(0)
                        self.round = self.round + 1
                        self.next_phase()
                        return
                
                else:
                    print('how did you get here?')
                    raise Exception

                print('opposing battlegroup exists, check if opposing battlegroup also activated')
                if self.active_bg.player is self.player1:
                    other_activated = self.p2_bg_queue[0].state is BattlegroupState.ACTIVATED

                elif self.active_bg.player is self.player2:
                    other_activated = self.p1_bg_queue[0].state is BattlegroupState.ACTIVATED
                
                else:
                    print('how did you get here?')
                    raise Exception

                if other_activated:
                    print('both active battlegroups activated, do next round')
                    self.p1_bg_queue.pop(0)
                    self.p2_bg_queue.pop(0)
                    self.round = self.round + 1
                    self.next_phase()
                    return

                print('opposing battlegroup exists but is not activated, activate next pending battlegroup')
                if self.active_bg.player is self.player1:
                    next_player = 2
                    self.active_bg = self.p2_bg_queue[0]

                elif self.active_bg.player is self.player2:
                    next_player = 1
                    self.active_bg = self.p1_bg_queue[0]
                
                else:
                    print('how did you get here?')
                    raise Exception

                self.current_state = f'Turn {self.turn}: P{next_player} Activate Battlegroup'
                self.active_bg.activate()
                self.combatlog.append(f'activating {self.active_bg}')
    
                # try:
                #     while self.p1_bg_queue[0].state is BattlegroupState.DESTROYED:
                #         print(f'removing destroyed battlegroup {self.p1_bg_queue[0]}')
                #         self.p1_bg_queue.pop(0)
                #         # self.p1_battlegroups[self.round-1].state = BattlegroupState.PENDING_ACTIVATION
                #     p1_pending = self.p1_battlegroups[self.round-1].state is BattlegroupState.PENDING_ACTIVATION
                #     p1_pending = p1_pending or self.p1_battlegroups[self.round-1].state is BattlegroupState.NOT_YET_ACTIVE
                # except IndexError:
                #     p1_pending = False
                # try:
                #     while self.p2_battlegroups[self.round-1].state is BattlegroupState.DESTROYED:
                #         print(f'removing destroyed battlegroup {self.p2_battlegroups[self.round-1]}')
                #         self.p2_battlegroups.pop(self.round-1)
                #         # self.p2_battlegroups[self.round-1].state = BattlegroupState.PENDING_ACTIVATION
                #     p2_pending = self.p2_battlegroups[self.round-1].state is BattlegroupState.PENDING_ACTIVATION
                #     p2_pending = p2_pending or self.p2_battlegroups[self.round-1].state is BattlegroupState.NOT_YET_ACTIVE
                # except IndexError:
                #     p2_pending = False

                # print(f'p1_pending={p1_pending}, p2_pending={p2_pending}')
                # if p1_pending:
                #     print(f'player 1 has pending battlegroup {self.p1_battlegroups[self.round-1]}')
                #     self.active_bg = self.p1_battlegroups[self.round-1]
                #     next_player = 1
                # elif p2_pending:
                #     print(f'player 2 has pending battlegroup {self.p2_battlegroups[self.round-1]}')
                #     self.active_bg = self.p2_battlegroups[self.round-1]
                #     next_player = 2
                # else:
                #     print("no pending battlegroups, do next round")
                #     self.round = self.round + 1
                #     self.next_phase()
                #     return

    def ship_selectable(self):
        out = self.current_state == 'Setup' 
        out = out or 'Activate' in self.current_state
        out = out or 'Launch' in self.current_state
        return out
    
    def firingphase(self):
        for group in self.active_bg.groups:
            for ship in group:
                if ship.state != ShipState.FIRING:
                    return False
        return True
    
    def do_catastrophic_damage(self, explody_ship, explode_roll, explode_radius):
        out = []
        if explode_roll <= 2:
            out.append('Catastrophic damage result:')
            out.append(f'Burn up')
            out.append(f'no ships affected')
            return out

        ships_in_radius = []
        fleets = [self.p1_battlegroups, self.p2_battlegroups]
        for fleet in fleets:
            for bg in fleet:
                for ship in bg.get_ships():
                    if ship.state is not ShipState.DESTROYED and ship is not explody_ship:
                        x0, y0 = explody_ship.loc
                        x1, y1 = ship.loc
                        dist = math.dist([x0, y0], [x1, y1])
                        if dist < explode_radius:
                            ships_in_radius.append(ship)

        if not ships_in_radius:
            out.append('no ships in explosion radius')
            return out

        ship_list_str = ', '.join([ship.name for ship in ships_in_radius])
        out.append(f'{ship_list_str} affected')

        out.append('Catastrophic damage result:')
        if explode_roll == 3:
            out.append(f'Blazing Wreck: apply minor spike')
            for ship in ships_in_radius:
                ship.apply_spike(1)
        else:
            if explode_roll == 4:
                ex_hits = 1
                ex_crits = 0
                out.append(f'Shredded: 1 hit')

            elif explode_roll == 5:
                ex_hits = 2
                ex_crits = 0
                out.append(f'Explosion: 2 hits')
                
            elif explode_roll == 6:
                ex_hits = 0
                ex_crits = 2
                out.append(f'Radiation Burst: 2 crits')
                
            elif explode_roll > 6:
                ex_hits = 0
                ex_crits = random.randint(1,6)
                out.append(f'Distortion Bubble: {ex_crits} crits')

            for ship in ships_in_radius:
                explosion_mitigation = ship.mitigate(ex_hits, ex_crits)
                for line in explosion_mitigation:
                    out.append(line)
        return out

    def resolve_launch_assets(self, ship):
        while self.launch_queue:
            if self.launchresolve_panel.active_player is self.player1:
                self.launchresolve_panel.active_player = self.player2
            else:
                self.launchresolve_panel.active_player = self.player1
            available_ships = self.launchresolve_panel.add_ships()
            if available_ships > 0:
                break
        launch_assets = self.launch_queue.pop(ship)
        immediate_launch_assets = []
        for strike in launch_assets:
            dist = math.dist(strike.ship.loc, ship.loc)
            if dist < strike.thrust:
                print(f'launch asset {str(strike)} in 1x thrust range')
                immediate_launch_assets.append(strike)
            else:
                print(f'launch asset {str(strike)} in 2x thrust range')
                ship.active_launch_assets.append(strike)
        result = ship.resolve_launch(immediate_launch_assets)
        # print(result)
        for line in result:
            self.combatlog.append(line)
        return

class TargetPanel:
    def __init__(self, major_font):
        self.rect = pygame.Rect(0,0,300,0)
        self.active = False
        self.major_font = major_font
        self.target_list = []
        self.target_rect_list = []
        self.buffer = major_font.size('')[1]/2
        self.gun = None
        self.needs_update = False
        self.gamecontroller = None

    def draw(self, surf):
        if not self.active:
            return
        self.rect.right = surf.get_width() - 350
        self.rect.height = (len(self.target_list)+1)*self.buffer*2
        self.rect.bottom = surf.get_height()*.8
        pygame.draw.rect(surf, NordColors.nord1, self.rect)
        y = self.rect.top + self.buffer
        x = self.buffer + self.rect.left
        self.target_rect_list = []
        for target in self.target_list:
            target_render = self.major_font.render(str(target), True, NordColors.snow0)
            target_rect = target_render.get_rect()
            target_rect.topleft = (x,y)
            self.target_rect_list.append(target_rect)
            surf.blit(target_render, (x,y))
            y = y + self.buffer*2

    def scroll(self, dir):
        return

class Player:
    def __init__(self, number, playarea):
        self.battlegroups = []
        self.ships = []
        self.number = number
        self.playarea = playarea
        self.gamecontroller = None
        
        self.torpedo_launch = []
        self.bomber_launch = []
        self.fighter_launch = []
        self.dropship_launch = []
        self.bulklander_launch = []
    
    def load_fleet(self, file):
        fleetfile_lines = file.readlines()
        currentBG = None
        # BG_sizemap = {'Pathfinder':1, 'Line':2, 'Vanguard':3, 'Flag':4}
        for line in fleetfile_lines:
            if line.startswith('SR'):
                vals = line.split()
                currentBG = Battlegroup(vals[1], vals[3][1:-4])
                currentBG.player = self
                self.battlegroups.append(currentBG)
            elif line[0].isdigit():
                vals = line.split()
                # print(vals)
                if vals[2] in ['New', 'St', 'San']:
                    vals[2] = f'{vals[2]} {vals[3]}'
                    vals.pop(3)
                # print(vals[2])
                group = ShipGroup()
                for i in range(int(vals[0])):
                    if self.number == 1:
                        image = 'blueship.png'
                    else:
                        image = 'redship.png'
                    newship = Ship(self.playarea,shipclass=vals[2], imagepath=image)
                    newship.player = self
                    newship.battlegroup = currentBG
                    newship.group = group
                    newship.gamecontroller = self.gamecontroller
                    self.ships.append(newship)
                    # draggables.append(newship)
                    # sprites.add(newship)
                    # self.ships.append(newship)
                    group.ships.append(newship)
                currentBG.groups.append(group)
        for bg in self.battlegroups:
            bg.update_sr()
        return self.battlegroups
    
    def add_launch_assets(self):
        for bg in self.battlegroups:
            for ship in bg.get_ships():
                    # print('this ship has launch')
                if ship.torpedoes:
                    self.torpedo_launch.append(ship)
                if ship.fighters:
                    self.bomber_launch.append(ship)
                    self.fighter_launch.append(ship)
                elif ship.dropships:
                    self.dropship_launch.append(ship)
                elif ship.bulk_landers:
                    self.bulklander_launch.append(ship)
    
    # def get_ships(self):
    #     out = 
    
    def update(self):
        pass
        # for bg in self.battlegroups:
        #     bg.update()
        # if self.state is 

class TargetQueue:
    def __init__(self, font):
        self.target_queue = []
        self.rect = pygame.Rect(350,0,300,0)
        self.font = font
        self.active = False
        self.font_height = font.size('')[1]

    def draw(self, surf):
        # self.rect.left = 350
        self.rect.height = len(self.target_queue)*self.font_height
        x = self.rect.left
        y = 0
        if not self.target_queue:
            return
        pygame.draw.rect(surf, NordColors.nord0, self.rect)
        for gun, target, count in self.target_queue:
            if count > 1:
                line_str = f'{gun.guntype} x{count} -> {target}'
            else:
                line_str = f'{gun.guntype} on {gun.ship} -> {target}'
            line_render = self.font.render(line_str, True, NordColors.snow0)
            surf.blit(line_render, (x,y))
            y = y + self.font_height
    
    def append(self, gun, target):
        attack_pooled = False
        if gun.close_action:
            for index, queue_entry in enumerate(self.target_queue):
                queue_gun, queue_target, queue_count = queue_entry
                if queue_gun.close_action and queue_target is target and queue_gun.ship in gun.ship.group:
                    print('pooling close action attack')
                    attack_pooled = True
                    self.target_queue.pop(index)
                    self.target_queue.append((queue_gun, queue_target, queue_count + 1))
                    break

        if not attack_pooled:
            self.target_queue.append((gun,target,1))
    
    def pop(self):
        return self.target_queue.pop(0)
    
    def is_empty(self):
        return len(self.target_queue) == 0

    def scroll(self, dir):
        pass


class LaunchQueue:
    def __init__(self, font):
        self.target_queue = dict()
        self.rect = pygame.Rect(350,0,200,0)
        self.font = font
        self.active = False
        self.font_height = font.size('')[1]
        # self.active_group = None

    def draw(self, surf):
        # self.rect.left = 350
        self.rect.height = len(self.target_queue)*self.font_height
        x = self.rect.left
        y = 0
        if not self.target_queue:
            return
        pygame.draw.rect(surf, NordColors.nord0, self.rect)
        for target in self.target_queue:
            queue_str = list(map(str, self.target_queue[target]))
            queue_str = f'{queue_str} -> {target}'
            if self.font.size(queue_str)[0] > self.rect.width:
                self.rect.width = self.font.size(queue_str)[0]
            line_render = self.font.render(queue_str, True, NordColors.snow0)
            surf.blit(line_render, (x,y))
            y = y + self.font_height
    
    def append(self, launch_asset, target):
        # if not self.target_queue:
        #     self.active_group = launch_asset.ship.group
        # elif launch_asset.ship not in self.active_group:
        #     print(f'ship not in current group')
        #     return

        print(f'check if {launch_asset} already has a target')
        key_to_delete = None
        for key, row in self.target_queue.items():
            if launch_asset in row:
                row.remove(launch_asset)
            if not row:
                key_to_delete = key
        if key_to_delete:
            self.target_queue.pop(key_to_delete)
        print(f'adding {launch_asset} to {target}')
        try:
            self.target_queue[target].append(launch_asset)
        except KeyError:
            self.target_queue[target] = [launch_asset]
    
    def pop(self, ship):
        return self.target_queue.pop(ship)
    
    def is_empty(self):
        return len(self.target_queue) == 0

    def scroll(self, dir):
        pass

    def __iter__(self):
        return iter(self.target_queue.items())

class SquadronPanel:
    def __init__(self, font, playarea):
        self.launch_asset = None
        self.selected_squadron = None
        self.playarea = playarea
        self.target_panel = SquadronTargetPanel(font, playarea)
        self.target_panel.squadron_panel = self
        self.active = False
        self.rect = pygame.Rect(0,0,150,0)
        self.font = font
        self.active_player = None
        self.targetable_ships = None

    def draw(self, surf):
        if not self.active:
            return
        
        self.rect.right = surf.get_width()-350

        buffer = self.font.size('')[1]/2
        squadrons = self.launch_asset.squadrons
        self.rect.height = buffer * 2 * (len(squadrons) + 2)
        self.rect.bottom = surf.get_height()*.8
        pygame.draw.rect(surf, NordColors.nord1, self.rect)

        x = self.rect.left + buffer
        y = self.rect.top + buffer
        header_render = self.font.render('Launch:', True, NordColors.snow0)
        surf.blit(header_render, (x, y))
        y = y + buffer * 2
        for index, squadron in enumerate(squadrons):
            # print(squadron)
            sq_str = f'{str(squadron)} {index + 1}'
            sq_render = self.font.render(sq_str, True, NordColors.frost0)
            surf.blit(sq_render, (x, y))

            squadron.rect = sq_render.get_rect()
            squadron.rect.topleft = (x, y)

            if squadron.highlight or squadron is self.selected_squadron:
                pygame.draw.rect(surf, NordColors.frost0, squadron.rect, 1)

            y = y + buffer * 2
        
        if self.selected_squadron:
            self.target_panel.draw(surf)

    def scroll(self, dir):
        return

    def on_click(self, mousepos):
        print('check click on selected squadron')
        if self.selected_squadron and self.selected_squadron.rect.collidepoint(mousepos):
            print('deselect squadron')
            self.selected_squadron = None
            return None
        
        print('check which squadron clicked')
        squadrons = self.launch_asset.squadrons
        for squadron in squadrons:
            if squadron.rect.collidepoint(mousepos):
                self.selected_squadron = squadron
                self.target_panel.squadron = squadron
                return squadron

class SquadronTargetPanel:
    def __init__(self, font, playarea):
        self.font = font
        self.squadron = None
        self.rect = pygame.Rect(0,0,300,0)
        self.squadron_panel = None
        self.targets = None
        self.target_rects = None
        self.playarea = playarea

    def draw(self, surf):
        if not self.squadron:
            # print('no squadron selected')
            return
        self.targets = self.squadron.get_targets(self.squadron_panel.targetable_ships)
        self.target_rects = []

        buffer = self.font.size('')[1]/2
        self.rect.height = buffer * 2 * (len(self.targets) + 2)
        self.rect.bottomright = self.squadron_panel.rect.bottomleft
        pygame.draw.rect(surf, NordColors.nord1, self.rect)

        x = self.rect.left + buffer
        y = self.rect.top + buffer
        for target in self.targets:
            # print('draw target')
            target_str = str(target)
            target_render = self.font.render(target_str, True, NordColors.snow0)
            surf.blit(target_render, (x, y))

            target_rect = target_render.get_rect()
            target_rect.topleft = (x, y)
            self.target_rects.append(target_rect)

            if target_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, NordColors.frost0, target_rect, 1)
                source_pos = self.squadron.ship.rect.center
                target_pos = target.rect.center
                pygame.draw.line(surf, NordColors.frost0, source_pos, target_pos)

            y = y + buffer * 2

    def on_click(self, mousepos):
        for index, target_rect in enumerate(self.target_rects):
            if target_rect.collidepoint(mousepos):
                return self.targets[index]
        return

    def scroll(self, dir):
        pass

class LaunchGroupSelectionPanel:
    def __init__(self, major_font, minor_font):
        self.active = False
        self.groups = []
        self.group_rects = []
        self.active_group = None
        
        self.rect = pygame.Rect(0,0,0,0)
        # self.skip_rect = None
        self.major_font = major_font
        self.minor_font = minor_font
    
    def set_launch_list(self, launch, launch_type):
        self.groups = [ship.group for ship in launch if ship.group.can_launch(launch_type)]
        self.groups = list(set(self.groups))
        self.group_rects = [pygame.Rect(0,0,0,0) for i in self.groups]
    
    def on_click(self, mousepos):
        for index, group_rect in enumerate(self.group_rects):
            if group_rect.collidepoint(mousepos):
                self.active = False
                self.active_group = self.groups[index]
                return self.active_group
        # if self.skip_rect.collidepoint(mousepos):
        #     self.active = False
        return
    
    def draw(self, surf):
        if not self.active:
            return
        major_font_height = self.major_font.get_height()
        minor_font_height = self.minor_font.get_height()
        self.rect.center = surf.get_rect().center
        self.rect.height = len(self.groups)*(major_font_height+minor_font_height)+major_font_height#*2
        self.rect.width = 350
        pygame.draw.rect(surf, NordColors.nord0, self.rect)
        x, y = self.rect.topleft
        header_render = self.major_font.render('choose group to launch from', True, NordColors.snow0)
        surf.blit(header_render, (x,y))
        y = y + major_font_height
        for index, group in enumerate(self.groups):
            group_name_render = self.major_font.render(str(group), True, NordColors.snow0)
            self.group_rects[index] = group_name_render.get_rect()
            group_rect = self.group_rects[index]
            group_rect.topleft = (x,y)
            surf.blit(group_name_render, (x,y))
            if group_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, NordColors.frost0, group_rect, 2)
                for ship in group:
                    ship.hover = True
            # else:
            #     for ship in group:
            #         ship.hover = False
            y = y + major_font_height
            group_desc_render = self.minor_font.render('group contents', True, NordColors.snow0)
            surf.blit(group_desc_render, (x,y))
            y = y + minor_font_height
        # skip_render = self.major_font.render('skip',True,NordColors.snow0)
        # skip_x = x + self.rect.width - skip_render.get_rect().width
        # self.skip_rect = skip_render.get_rect()
        # self.skip_rect.topleft = (skip_x,y)
        # surf.blit(skip_render, (skip_x,y))

class LaunchAssetResolvePanel:
    def __init__(self, major_font, minor_font):
        self.active = False
        self.ships = []
        self.ship_rects = []
        self.launch_queue = None
        self.active_player = None

        self.rect = pygame.Rect(0,0,0,0)
        self.major_font = major_font
        self.minor_font = minor_font
    
    def add_ships(self):
        self.ships = []
        for (ship, launch_assets) in self.launch_queue:
            if ship.player is not self.active_player:
                self.ships.append(ship)
        self.ship_rects = [pygame.Rect(0,0,0,0) for i in self.ships]
        return len(self.ships)

    def on_click(self, mousepos):
        for index, rect in enumerate(self.ship_rects):
            if rect.collidepoint(mousepos):
                self.active = False
                return self.ships[index]
        return
    
    def draw(self, surf):
        if not self.active:
            return
        major_font_height = self.major_font.get_height()
        minor_font_height = self.minor_font.get_height()
        self.rect.center = surf.get_rect().center
        self.rect.height = major_font_height*(len(self.ships)+1)
        self.rect.width = 350
        x, y = self.rect.topleft
        pygame.draw.rect(surf, NordColors.nord0, self.rect)
        header_str = f'Player {self.active_player.number}, select a ship to resolve strike craft'
        header_render = self.major_font.render(header_str, True, NordColors.snow0)
        surf.blit(header_render, (x,y))
        y = y + major_font_height
        self.add_ships()
        for index, ship in enumerate(self.ships):
            ship_str = str(ship)
            ship_render = self.major_font.render(ship_str, True, NordColors.snow0)
            surf.blit(ship_render, (x,y))
            self.ship_rects[index] = ship_render.get_rect()
            self.ship_rects[index].topleft = (x,y)
            if self.ship_rects[index].collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, NordColors.frost0, self.ship_rects[index], 2)
                ship.hover = True
            y = y + major_font_height