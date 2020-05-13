import pygame
from pygame.locals import *
from helper import *
from ship import *
import random
from enum import Enum, auto
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
        self.scale = self.scale*(1+zoom_increment)
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
        self.width_frac = width_frac
        self.needs_update = True
    
    def draw(self, surf):
        self.width = int(surf.get_width()*self.width_frac)
        self.height = int(surf.get_height()*.2)
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
        lines = int(self.height/line_height)
        if lines < len(printloglines):
            printloglines = printloglines[self.currentline:lines+self.currentline]
        printloglines.reverse()

        line_pixel = 0
        for line in printloglines:
            line_font_surface = self.line_font.render(line,True,self.font_color)
            surf.blit(line_font_surface,(self.rect.x, self.rect.y + line_pixel))
            line_pixel += line_height
    
    def scroll(self, dir):
        line_height = pygame.font.Font('kooten.ttf', 20).size('')[1]
        if len(self.log)*line_height < self.height:
            return
        if self.currentline + dir < 0:
            return
        if self.currentline + dir + self.height/line_height - 1 >= len(self.log):
            return
        self.currentline += dir

class FleetPanel:
    def __init__(self, side, major_font, minor_font, width_frac=.2):
        self.battlegroups = []
        self.battlegroups_originalorder = []
        self.width = 0
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
        # self.buffer = 10
    
    def draw(self, surf):
        self.width = int(surf.get_width()*self.width_frac)
        self.height = surf.get_height()
        self.rect.width = self.width
        self.rect.height = surf.get_height()*4
        self.surf = pygame.Surface((self.width, self.height*4),pygame.SRCALPHA)
        if self.side == 'right':
            self.rect.right = surf.get_width()
        
        pygame.draw.rect(surf, self.color, self.rect)

        # line_font = pygame.font.Font('kooten.ttf', 18)
        # minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = self.line_font.size('')[1]
        minor_height = self.minor_font.size('')[1]
        buffer = line_height/2
        y = self.rect.top + buffer
        for bg in self.battlegroups_originalorder:
            bg_top = y
            if bg.state == 'activated':
                bg_color = NordColors.nord3
            elif bg.state == 'active':
                bg_color = NordColors.frost0
            elif bg.state == 'pending active':
                bg_color = NordColors.frost2
            elif bg.state == 'not yet active':
                bg_color = NordColors.snow0
            font_render = self.line_font.render(str(bg),True,bg_color)
            self.surf.blit(font_render,(buffer, y))
            y = y + line_height + buffer
            for group in bg.groups:
                for ship in group:
                    font_render = self.line_font.render(f'{ship.faction} {ship.name}',True,NordColors.snow1)
                    class_render = self.minor_font.render(f'{ship.shipclass}-class {ship.shiptype}',True,NordColors.snow2)
                    box_height = line_height+2*minor_height+buffer
                    
                    ship.panel_rect.left = 1.5*buffer
                    ship.panel_rect.top = y-buffer/2
                    ship.panel_rect.width = self.width-3*buffer
                    ship.panel_rect.height = box_height

                    pygame.draw.rect(self.surf, NordColors.nord2, ship.panel_rect)

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
                    y = y + minor_height + buffer

                    hull_bar_length = ship.panel_rect.width-2*buffer
                    hp_start = ship.panel_rect.left+buffer
                    hp_end = ship.panel_rect.left+buffer+hull_bar_length*ship.hp/ship.hull
                    hull_end = hp_start+hull_bar_length
                    pygame.draw.line(self.surf,NordColors.aurora3,(hp_start,y),(hp_end,y),4)
                    
                    if hp_end < hull_end:
                        pygame.draw.line(self.surf,NordColors.aurora0,(hp_end,y),(hull_end,y),4)

                    ship.panel_rect.left = 1.5*buffer + self.rect.left
                    ship.panel_rect.top = ship.panel_rect.top + self.rect.top + buffer/2

                    y = y + 2*buffer                    
                y = y + buffer
            bg_boundary = pygame.Rect(.5*buffer, bg_top-.5*buffer, self.width-buffer, y-bg_top-.5*buffer)
            if bg.state == 'active' or bg.hovered:
                pygame.draw.rect(self.surf, NordColors.frost0, bg_boundary, 2)
            elif bg.state == 'pending active':
                pygame.draw.rect(self.surf, NordColors.frost2, bg_boundary, 2)
        self.content_height = y
        # surf.blit(self.surf,(0,0))
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
        self.width_frac = width_frac
        self.color = NordColors.nord2
        self.buffer = 10
        self.line_font = major_font
        self.minor_font = minor_font
        self.hovered_gun = None
        self.selected_gun = None
        self.needs_update = True
        self.targetpanel = None

    def draw(self, surf):
        self.hovered_gun = None
        self.rect = pygame.Rect(surf.get_width()/2,surf.get_height()*(1-self.height_frac),surf.get_width()*self.width_frac,surf.get_height()*self.height_frac)
        pygame.draw.rect(surf, self.color, self.rect)
        
        # line_font = pygame.font.Font('kooten.ttf', 18)
        # minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = self.line_font.size('')[1]
        minor_height = self.minor_font.size('')[1]

        y = self.rect.top + self.buffer
        header_render = self.line_font.render('Ship Info',True,NordColors.snow0)
        surf.blit(header_render, (self.rect.left+self.buffer,y))
        y = y + line_height# + self.buffer

        # print(f'selected ship {self.selectedship}')
        if self.selectedship:
            shipname_render = self.line_font.render(f'{self.selectedship.name}, {self.selectedship.shipclass}-class {self.selectedship.shiptype}', True, NordColors.snow0)
            surf.blit(shipname_render, (self.rect.left+self.buffer,y))
            y = y + line_height
            for gun in self.selectedship.guns:
                if gun.active:
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

    def scroll(self, dir):
        pass

class Battlegroup:
    def __init__(self, sr, size, points):
        self.size = size
        self.sr = int(sr)
        self.points = points
        self.groups = []
        self.state = 'not yet active'
        self.hovered = False
        self.up_arrow_rect = None
        self.down_arrow_rect = None

    def __str__(self):
        out_str = f'SR{self.sr} {self.size} {self.points} pts'
        # for group in self.groups:
        #     out_str += f'\n{len(group)} {group[0].shipclass}'
        return out_str
    
    def printships(self):
        out_str = ''
        for group in self.groups:
            out_str = out_str + f'{len(group)} {group[0].shipclass}, '
        out_str = out_str[:-2]
        return out_str
    
class ShipGroup:
    def __init__(self):
        pass

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
        self.player_phase = None
        self.bg_plan_screen = None
        self.turn = 1
        self.firstplayer = 0
        self.p1_button = None
        self.p2_button = None
        self.active_bg = None
        self.combatlog = None
        self.firing_queue = Queue()
        # self.needs_update = True
        # self.activation_queue = Queue()
    
    def draw(self, surf):
        state_text = f'{self.current_state}'
        gamephase_render = self.title_font.render(state_text, True, NordColors.snow0)
        gamephase_render_size = self.title_font.size(state_text)
        surf.blit(gamephase_render, ((surf.get_width()-gamephase_render_size[0])/2,0))

        endturn = 'End Turn'
        endturnbutton_render = self.major_font.render(endturn, True, NordColors.snow0)
        endturnbutton_render_width = self.major_font.size(endturn)
        self.rect.left = (surf.get_width()-endturnbutton_render_width[0])/2
        self.rect.top = gamephase_render_size[1]
        self.rect.size = endturnbutton_render_width
        pygame.draw.rect(surf, NordColors.nord3, self.rect)
        surf.blit(endturnbutton_render, (self.rect.left,self.rect.top))

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
        if self.current_state == 'Setup':
            self.current_state = 'Planning (P1)'
            self.bg_plan_screen = BattlegroupPlanner(self.p1_battlegroups, self.major_font, self.minor_font)
            for bg in self.p1_battlegroups+self.p2_battlegroups:
                for group in bg.groups:
                    for ship in group:
                        ship.state = ShipState.NOT_YET_ACTIVATED
        elif self.current_state == 'Planning (P1)':
            self.bg_plan_screen.bgs = self.p2_battlegroups
            self.current_state = 'Planning (P2)'
        elif self.current_state == 'Planning (P2)':
            self.current_state = f'Turn {self.turn}: Select Player Order'
            index = self.turn-1
            p1_sr = self.p1_battlegroups[index].sr
            self.p1_battlegroups[index].state = 'active'
            p2_sr = self.p2_battlegroups[index].sr
            self.p2_battlegroups[index].state = 'active'
            if p1_sr == p2_sr:
                self.firstplayer = random.choice([1,2])
                self.combatlog.log.append(f'Battlegroups have same strategy rating, player {self.firstplayer} picks')
            else:
                if p1_sr < p2_sr:
                    self.firstplayer = 1
                else:
                    self.firstplayer = 2
                self.combatlog.log.append(f'Player {self.firstplayer} picks, has lower strategy rating {min(p1_sr, p2_sr)}')
        elif 'Select Player Order' in self.current_state:
            self.current_state = f'Turn {self.turn}: P{next_player} Activate Battlegroup'
            if next_player == 1:
                self.p2_battlegroups[self.turn-1].state = 'pending active'
                self.active_bg = self.p1_battlegroups[self.turn-1]
            else:
                self.p1_battlegroups[self.turn-1].state = 'pending active'
                self.active_bg = self.p2_battlegroups[self.turn-1]
            for group in self.active_bg.groups:
                for ship in group:
                    ship.state = ShipState.MOVING
                    for gun in ship.guns:
                        gun.active = True
        return self.current_state
        # print(f'now on phase {self.current_state}')
    
    def ship_selectable(self):
        return self.current_state == 'Setup' or 'Activate' in self.current_state
    
    def firingphase(self):
        for group in self.active_bg.groups:
            for ship in group:
                if ship.state != ShipState.FIRING:
                    return False
        return True

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
        self.rect.right = surf.get_width()*.8
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
    
    def load_fleet(self, file):
        fleetfile_lines = file.readlines()
        currentBG = None
        # BG_sizemap = {'Pathfinder':1, 'Line':2, 'Vanguard':3, 'Flag':4}
        for line in fleetfile_lines:
            if line.startswith('SR'):
                vals = line.split()
                currentBG = Battlegroup(vals[0][2:], vals[1], vals[3][1:-4])
                self.battlegroups.append(currentBG)
            elif line[0].isdigit():
                vals = line.split()
                # print(vals)
                if vals[2] == 'New':
                    vals[2] = f'{vals[2]} {vals[3]}'
                    vals.pop(3)
                # print(vals[2])
                group = []
                for i in range(int(vals[0])):
                    if self.number == 1:
                        image = 'blueship.png'
                    else:
                        image = 'redship.png'
                    newship = Ship(self.playarea,shipclass=vals[2], imagepath=image)
                    newship.player = self
                    newship.group = group
                    self.ships.append(newship)
                    # draggables.append(newship)
                    # sprites.add(newship)
                    # self.ships.append(newship)
                    group.append(newship)
                currentBG.groups.append(group)
        return self.battlegroups

class TargetQueue:
    def __init__(self):
        self.target_queue = []