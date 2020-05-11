import pygame, sys, math
# import numpy as np
from pygame.locals import *
from ship import *
from guns import *
# from queue import Queue
import random

nord0 = (46,52,64)
nord1 = (59,66,82)
nord2 = (67,76,94)
nord3 = (76,86,106)
snow0 = (216,222,233)
snow1 = (229,233,240)
snow2 = (236,239,244)
frost0 = (143,188,187)
frost1 = (136,192,208)
frost2 = (129,161,193)
frost3 = (94,129,172)
aurora0 = (191,97,106)
aurora1 = (208,135,112)
aurora2 = (235,203,139)
aurora3 = (163,190,140)
aurora4 = (180,142,173)

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
        return dist/self.dim[0]*self.rect.width

class CombatLog:
    def __init__(self, font_obj, width_frac=.3):
        self.log = []
        self.width = 0
        self.height = 0
        self.rect = None
        self.color = nord1
        self.line_font = font_obj
        self.font_color = snow0
        self.currentline = 0
        self.width_frac = width_frac
    
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
        self.color = nord0
        self.line_font = major_font
        self.minor_font = minor_font
        self.side = side
        self.width_frac = width_frac
        self.surf = None
        self.content_height = 0
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
                bg_color = nord3
            elif bg.state == 'active':
                bg_color = frost0
            elif bg.state == 'pending active':
                bg_color = frost2
            elif bg.state == 'not yet active':
                bg_color = snow0
            font_render = self.line_font.render(str(bg),True,bg_color)
            self.surf.blit(font_render,(buffer, y))
            y = y + line_height + buffer
            for group in bg.groups:
                for ship in group:
                    font_render = self.line_font.render(f'{ship.faction} {ship.name}',True,snow1)
                    class_render = self.minor_font.render(f'{ship.shipclass}-class {ship.shiptype}',True,snow2)
                    box_height = line_height+2*minor_height+buffer
                    
                    ship.panel_rect.left = 1.5*buffer
                    ship.panel_rect.top = y-buffer/2
                    ship.panel_rect.width = self.width-3*buffer
                    ship.panel_rect.height = box_height

                    pygame.draw.rect(self.surf, nord2, ship.panel_rect)

                    hull_string = f'{ship.hp}/{ship.hull}'
                    hull_string_width = self.line_font.size(hull_string)[0]
                    hull_render = self.line_font.render(hull_string, True, snow1)
                    self.surf.blit(hull_render, (self.rect.width-2*buffer-hull_string_width, y))

                    if ship.hover:
                        pygame.draw.rect(self.surf, frost0, ship.panel_rect, 2)
                    self.surf.blit(font_render, (2 * buffer, y))
                    y = y + line_height
                    self.surf.blit(class_render, (2 * buffer, y))
                    y = y + minor_height + buffer

                    hull_bar_length = ship.panel_rect.width-2*buffer
                    hp_start = ship.panel_rect.left+buffer
                    hp_end = ship.panel_rect.left+buffer+hull_bar_length*ship.hp/ship.hull
                    hull_end = hp_start+hull_bar_length
                    pygame.draw.line(self.surf,aurora3,(hp_start,y),(hp_end,y),4)
                    
                    if hp_end < hull_end:
                        pygame.draw.line(self.surf,aurora0,(hp_end,y),(hull_end,y),4)

                    ship.panel_rect.left = 1.5*buffer + self.rect.left

                    y = y + 2*buffer                    
                y = y + buffer
            bg_boundary = pygame.Rect(.5*buffer, bg_top-.5*buffer, self.width-buffer, y-bg_top-.5*buffer)
            if bg.state == 'active' or bg.hovered:
                pygame.draw.rect(self.surf, frost0, bg_boundary, 2)
            elif bg.state == 'pending active':
                pygame.draw.rect(self.surf, frost2, bg_boundary, 2)
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
        self.color = nord2
        self.buffer = 10
        self.line_font = major_font
        self.minor_font = minor_font

    def draw(self, surf):
        self.rect = pygame.Rect(surf.get_width()/2,surf.get_height()*(1-self.height_frac),surf.get_width()*self.width_frac,surf.get_height()*self.height_frac)
        pygame.draw.rect(surf, self.color, self.rect)
        
        # line_font = pygame.font.Font('kooten.ttf', 18)
        # minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = self.line_font.size('')[1]
        minor_height = self.minor_font.size('')[1]

        y = self.rect.top + self.buffer
        header_render = self.line_font.render('Ship Info',True,snow0)
        surf.blit(header_render, (self.rect.left+self.buffer,y))
        y = y + line_height# + self.buffer

        # print(f'selected ship {self.selectedship}')
        if self.selectedship:
            shipname_render = self.line_font.render(f'{self.selectedship.name}, {self.selectedship.shipclass}-class {self.selectedship.shiptype}', True, snow0)
            surf.blit(shipname_render, (self.rect.left+self.buffer,y))
            y = y + line_height
            for gun in self.selectedship.guns:
                gun_render = self.minor_font.render(str(gun), True, frost0)
                surf.blit(gun_render, (self.rect.left+self.buffer,y))
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
    
    def draw(self, surf):
        x = (surf.get_width()-self.width)/2
        y = 200
        major_font_height = self.major_font.size('')[1]
        minor_font_height = self.minor_font.size('')[1]
        buffer = major_font_height/2
        height = len(self.bgs)*(2*major_font_height+buffer)+buffer
        pygame.draw.rect(surf,nord1,pygame.Rect(x-buffer,y-buffer,self.width+2*buffer,height))
        arrow_offset = 20
        # print(f'in draw {self.bgs}')
        for index, bg in enumerate(self.bgs):
            bg_y = y
            mousepos = pygame.mouse.get_pos()
            bg_render = self.major_font.render(f'{str(bg)}', True, snow0)
            # pygame.draw.rect()
            surf.blit(bg_render, (x+arrow_offset,y))
            if index != 0:
                up_arrow_render = self.major_font.render('/\\', True, snow0)
            else:
                up_arrow_render = self.major_font.render('/\\', True, nord1)
            bg.up_arrow_rect = up_arrow_render.get_rect()
            bg.up_arrow_rect.topleft = (x,y)
            surf.blit(up_arrow_render, (x,y))
            y = y + major_font_height
            bg_ships_render = self.minor_font.render(bg.printships(), True, frost0)
            surf.blit(bg_ships_render, (x+arrow_offset,y))
            if index != len(self.bgs)-1:
                down_arrow_render = self.major_font.render('\\/', True, snow0)
            else:
                down_arrow_render = self.major_font.render('\\/', True, nord1)                
            bg.down_arrow_rect = down_arrow_render.get_rect()
            bg.down_arrow_rect.topleft = (x,y)
            # print(bg.down_arrow_rect)
            # print(f'setting bg down arrow rect at {(x,y)}')
            surf.blit(down_arrow_render, (x,y))
            y = y + major_font_height + buffer
            select_box = pygame.Rect(x,bg_y,self.width,y-bg_y)
            bg.hovered = select_box.collidepoint(mousepos)

class GameController:
    def __init__(self, title_font, major_font, minor_font):
        self.current_state = 'Setup'
        self.title_font = title_font
        self.rect = pygame.Rect(0,0,0,0)
        self.major_font = major_font
        self.minor_font = minor_font
        self.p1_battlegroups = []
        self.p2_battlegroups = []
        self.bg_plan_screen = None
        self.turn = 1
        self.firstplayer = 0
        self.p1_button = None
        self.p2_button = None
        # self.activation_queue = Queue()
    
    def draw(self, surf):
        state_text = f'{self.current_state}'
        gamephase_render = self.title_font.render(state_text, True, snow0)
        gamephase_render_size = self.title_font.size(state_text)
        surf.blit(gamephase_render, ((surf.get_width()-gamephase_render_size[0])/2,0))

        endturn = 'End Turn'
        endturnbutton_render = self.major_font.render(endturn, True, snow0)
        endturnbutton_render_width = self.major_font.size(endturn)
        self.rect.left = (surf.get_width()-endturnbutton_render_width[0])/2
        self.rect.top = gamephase_render_size[1]
        self.rect.size = endturnbutton_render_width
        pygame.draw.rect(surf, nord3, self.rect)
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
            pygame.draw.rect(surf, nord1, pygame.Rect(x-buffer,y-buffer,panel_width+2*buffer,height))
            panel_title = f'Player {self.firstplayer}, select who goes first:'
            panel_title_render = self.title_font.render(panel_title, True, snow0)
            surf.blit(panel_title_render,(x,y))
            y = y + title_font_size[1] + buffer

            p1_button_render = self.title_font.render('P1', True, snow1)
            p1_button_loc = (x,y)
            self.p1_button = p1_button_render.get_rect()
            self.p1_button.topleft = p1_button_loc
            surf.blit(p1_button_render,p1_button_loc)

            p2_button_render = self.title_font.render('P2', True, snow1)
            p2_button_loc = (x+panel_width-title_font_size[0],y)
            self.p2_button = p2_button_render.get_rect()
            self.p2_button.topleft = p2_button_loc
            surf.blit(p2_button_render,p2_button_loc)
    
    def next_phase(self, next_player=None):
        # print('changing phase')
        if self.current_state == 'Setup':
            # print('movement phase')
            self.current_state = 'Planning (P1)'
            self.bg_plan_screen = BattlegroupPlanner(self.p1_battlegroups, self.major_font, self.minor_font)
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
            elif p1_sr < p2_sr:
                self.firstplayer = 1
            else:
                self.firstplayer = 2
        elif 'Select Player Order' in self.current_state:
            self.current_state = f'Turn {self.turn}: P{next_player} Activate Battlegroup'
            if next_player == 1:
                self.p2_battlegroups[self.turn-1].state = 'pending active'
            else:
                self.p1_battlegroups[self.turn-1].state = 'pending active'
        return self.current_state
        # print(f'now on phase {self.current_state}')
    
    def ship_selectable(self):
        return self.current_state == 'Setup' or 'Activate' in self.current_state

pygame.init()
DISPLAYSURF = pygame.display.set_mode((1600,900), pygame.RESIZABLE)# | pygame.OPENGLBLIT)
pygame.display.set_caption('Dropfleet Commander')
INTERNALCLOCK = pygame.time.Clock()
fps_font = pygame.font.Font(None, 20)

sprites = pygame.sprite.Group()
draggables = []
draggable_offsets = []
playobjects = []
ships = pygame.sprite.Group()

# Ship.load_shipDB()
# Weapon.load_gunDB()

ui = []
ui_needs_update = True

playarea = PlayArea()
playarea.scale = min(DISPLAYSURF.get_width()/playarea.rect.width, DISPLAYSURF.get_height()/playarea.rect.height)

playarea.image = pygame.transform.rotozoom(playarea.image0,0,playarea.scale)
playarea.rect = playarea.image.get_rect()
draggables.append(playarea)
sprites.add(playarea)

title_font = pygame.font.Font('kooten.ttf', 24)
major_font = pygame.font.Font('kooten.ttf', 18)
minor_font = pygame.font.Font('kooten.ttf', 14)

gamecontroller = GameController(title_font, major_font, minor_font)
ui.append(gamecontroller)

combatlog = CombatLog(major_font)
ui.append(combatlog)
p1_fleetpanel = FleetPanel('left', major_font, minor_font)
p2_fleetpanel = FleetPanel('right', major_font, minor_font)
ui.append(p1_fleetpanel)
ui.append(p2_fleetpanel)
infopanel = InfoPanel(major_font, minor_font)
ui.append(infopanel)

p1_fleetfile = open('p1.txt','r')
p1_fleetfile_lines = p1_fleetfile.readlines()
p2_fleetfile = open('p2.txt','r')
p2_fleetfile_lines = p2_fleetfile.readlines()
fleetfiles = [[p1_fleetpanel.battlegroups, p1_fleetfile_lines], [p2_fleetpanel.battlegroups, p2_fleetfile_lines]]
currentBG = None
# BG_sizemap = {'Pathfinder':1, 'Line':2, 'Vanguard':3, 'Flag':4}
for fleetlist, lines in fleetfiles:
    for line in lines:
        if line.startswith('SR'):
            vals = line.split()
            currentBG = Battlegroup(vals[0][2:], vals[1], vals[3][1:-4])
            fleetlist.append(currentBG)
        elif line[0].isdigit():
            vals = line.split()
            # print(vals)
            if vals[2] == 'New':
                vals[2] = f'{vals[2]} {vals[3]}'
                vals.pop(3)
            # print(vals[2])
            group = []
            for i in range(int(vals[0])):
                newship = Ship(playarea,shipclass=vals[2])
                draggables.append(newship)
                sprites.add(newship)
                ships.add(newship)
                group.append(newship)
            currentBG.groups.append(group)
p1_fleetpanel.battlegroups_originalorder = [bg for bg in p1_fleetpanel.battlegroups]
p2_fleetpanel.battlegroups_originalorder = [bg for bg in p2_fleetpanel.battlegroups]
# for bg in p1fleetlist:
#     print(bg)
# currentBG.state = 'active'

p1_fleetfile.close()
p2_fleetfile.close()

gamecontroller.p1_battlegroups = p1_fleetpanel.battlegroups
gamecontroller.p2_battlegroups = p2_fleetpanel.battlegroups

# for bg in p1_fleetpanel.battlegroups + p2_fleetpanel.battlegroups:
#     for group in bg.groups:
#         for ship1 in group:
#             draggables.append(ship1)
#             sprites.add(ship1)
#             ships.add(ship1)

selectedship = None

dragging = False

print(ships)
for ship in ships:
    print(ship)

while True:

    pygame.draw.rect(DISPLAYSURF,(0,0,0),pygame.Rect(0,0,DISPLAYSURF.get_width(),DISPLAYSURF.get_height()))
    # DISPLAYSURF.fill((0,0,0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            DISPLAYSURF = pygame.display.set_mode((event.w,event.h), pygame.RESIZABLE)# | pygame.OPENGLBLIT)
        elif event.type == MOUSEBUTTONDOWN:
            # DISPLAYSURF.set_at(pygame.mouse.get_pos(), Color(255,0,0))
            # print(pygame.mouse.get_pos())

            if event.button == 1:
                # print(playarea.pixeltogrid(event.pos))
                if gamecontroller.rect.collidepoint(event.pos):
                    # print('next phase')
                    gamecontroller.next_phase()
                    break
                if 'Planning' in gamecontroller.current_state:
                    bg_list = gamecontroller.bg_plan_screen.bgs
                    # print(f'at event listener {bg_list}')
                    for index, bg in enumerate(bg_list):
                        # print(bg.up_arrow_rect)
                        if bg.up_arrow_rect and bg.up_arrow_rect.collidepoint(event.pos) and index > 0:
                            bg_list[index-1], bg_list[index] = bg_list[index], bg_list[index-1]
                            break
                        if bg.down_arrow_rect and bg.down_arrow_rect.collidepoint(event.pos) and index < len(bg_list)-1:
                            bg_list[index], bg_list[index+1] = bg_list[index+1], bg_list[index]
                            break
                if 'Select Player Order' in gamecontroller.current_state:
                    if gamecontroller.p1_button.collidepoint(event.pos):
                        gamecontroller.next_phase(next_player=1)
                    elif gamecontroller.p2_button.collidepoint(event.pos):
                        gamecontroller.next_phase(next_player=2)
                    break
                for ship in ships:
                    if ship.rect.collidepoint(event.pos):
                        if gamecontroller.ship_selectable():
                            if ship != selectedship:
                                selectedship = ship
                                draggables.remove(ship)
                                # pos0 = playarea.pixeltogrid(ship.rect.center)
                                selectoffset_x = ship.rect.center[0] - event.pos[0]
                                selectoffset_y = ship.rect.center[1] - event.pos[1]
                                ship.is_selected = True
                                break
                                # print(f'initial bearing {ship.bearing}')
                            else:
                                draggables.append(ship)
                                selectedship = None
                                ship.is_selected = False
                                ship.loc = playarea.pixeltogrid(ship.rect.center)
                                ship.selection_loc = None
                                ship.bearing = ship.selection_bearing
                                combatlog.log.append(f'{ship.name} moved to {ship.loc[0]:.1f}, {ship.loc[1]:.1f} bearing {ship.bearing:.3f}')

            if event.button == 3:            
                dragging = True
                mouse_x, mouse_y = event.pos
                draggable_offsets = []
                for draggable in draggables:
                    offset_x = draggable.rect.x - mouse_x
                    offset_y = draggable.rect.y - mouse_y
                    draggable_offsets.append([offset_x, offset_y])

            elif event.button == 4: # mouse wheel up
                mouseinui = False
                for ui_el in ui:
                    if ui_el.rect.collidepoint(event.pos):
                        mouseinui = True
                        ui_el.scroll(1)
                        break
                if not mouseinui:
                    for draggable in draggables:
                        draggable.zoom(.1)

            elif event.button == 5: # mouse wheel down
                mouseinui = False
                for ui_el in ui:
                    if ui_el.rect.collidepoint(event.pos):
                        mouseinui = True
                        ui_el.scroll(-1)
                        break
                if not mouseinui:
                    for draggable in draggables:
                        draggable.zoom(-.1)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:            
                dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if gamecontroller.current_state == 'Setup' and selectedship:
                center = (selectoffset_x + event.pos[0], selectoffset_y + event.pos[1])
                selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of ship when selected
                center = playarea.gridtopixel(selectedship.selection_loc)

                selectedship.image = pygame.transform.rotozoom(selectedship.image0, selectedship.bearing, selectedship.scale)
                selectedship.rect = selectedship.image.get_rect()
                selectedship.rect.center = center

                selectedship.selection_bearing = selectedship.bearing

            if 'Activate' in gamecontroller.current_state and selectedship:
                center = (selectoffset_x + event.pos[0], selectoffset_y + event.pos[1])
                selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of ship when selected
                center = playarea.gridtopixel(selectedship.selection_loc)
                dist = math.sqrt(math.pow(selectedship.selection_loc[0] - selectedship.loc[0],2) + math.pow(selectedship.selection_loc[1] - selectedship.loc[1],2))
                # if dist > selectedship.maxthrust or dist < selectedship.minthrust:
                    # print(f'ship selection loc {selectedship.selection_loc}')
                    # print(f'ship loc {selectedship.loc}')
                if dist > selectedship.maxthrust:
                    thrust = selectedship.maxthrust
                elif dist < selectedship.minthrust:
                    thrust = selectedship.minthrust
                    # if dist == 0: dist = .001
                else:
                    thrust = dist
                # print(f'thrust {thrust}')
                    # center_x = (selectedship.selection_loc[0] - selectedship.loc[0])/dist*thrust + selectedship.loc[0]
                    # center_y = (selectedship.selection_loc[1] - selectedship.loc[1])/dist*thrust + selectedship.loc[1]
                    # center = playarea.gridtopixel((center_x,center_y))
                # print(dist)
                
                move_pos = playarea.gridtopixel(selectedship.loc)
                x = center[0] - move_pos[0]
                y = center[1] - move_pos[1]
                bearing = math.atan2(x,-y)
                # print(f'new bearing {bearing}')

                bearing_change = bearing + math.radians(selectedship.bearing)
                # print(f'bearing change {bearing_change}')
                if bearing_change < -math.pi:
                    bearing_change = bearing_change + 2 * math.pi
                if bearing_change < -math.radians(45):
                    bearing = -math.radians(45) - math.radians(selectedship.bearing)
                if bearing_change > math.radians(45):
                    bearing = math.radians(45) - math.radians(selectedship.bearing)
                selectedship.selection_bearing = -math.degrees(bearing%(2*math.pi))

                center_x = thrust * math.sin(bearing) + selectedship.loc[0]
                center_y = thrust * -math.cos(bearing) + selectedship.loc[1]
                center = playarea.gridtopixel((center_x,center_y))

                selectedship.image = pygame.transform.rotozoom(selectedship.image0, selectedship.selection_bearing, selectedship.scale)
                selectedship.rect = selectedship.image.get_rect()
                selectedship.rect.center = center
            if dragging:
                mouse_x, mouse_y = event.pos
                for index, draggable in enumerate(draggables):
                    draggable.rect.x = mouse_x + draggable_offsets[index][0]
                    draggable.rect.y = mouse_y + draggable_offsets[index][1]
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if selectedship:
                    draggables.append(selectedship)
                    selectedship.is_selected = False
                    selectedship.selection_loc = None
                    print(f'{selectedship.loc}, {playarea.gridtopixel(selectedship.loc)}')
                    selectedship.rect.center = playarea.gridtopixel(selectedship.loc)
                    print(f'returned to {playarea.pixeltogrid(selectedship.rect.center)}, {selectedship.rect.center}')
                    selectedship.image = pygame.transform.rotozoom(selectedship.image0, selectedship.bearing, selectedship.scale)
                    selectedship = None
            if event.key == pygame.K_a:
                for ship in ships:
                    if ship.rect.collidepoint(pygame.mouse.get_pos()):
                        ship.hp = ship.hp - 1
        
    # pygame.draw.rect(DISPLAYSURF,(255,255,255),rectangle)
    sprites.draw(DISPLAYSURF)
                    
    infopanel.selectedship = None
    mousepos = pygame.mouse.get_pos()
    infopanel.selectedship = None
    for ship in ships:
        # pygame.draw.rect(DISPLAYSURF, frost1, ship.panel_rect)
        ship.hover = False
        if not infopanel.selectedship:
            if ship.rect.collidepoint(mousepos) or ship.panel_rect.collidepoint(mousepos):
                ship.hover = True
                pygame.draw.rect(DISPLAYSURF, frost1, ship.rect, 1)
                infopanel.selectedship = ship
                # print(f'ship hovered: {ship}')

    # for ship in ships:
    if 'Activate' in gamecontroller.current_state and selectedship:
        # selectedship.update_loc(playarea)
        pygame.draw.rect(DISPLAYSURF, frost1, selectedship.rect,1)

        # print(selectedship.bearing)
        minthrust_pixel = playarea.scalegridtopixel(selectedship.minthrust)
        maxthrust_pixel = playarea.scalegridtopixel(selectedship.maxthrust)
        shipx_pixel = playarea.gridtopixel(selectedship.loc)[0]
        shipy_pixel = playarea.gridtopixel(selectedship.loc)[1]
        border1_bearing = (selectedship.bearing + 45) % 360
        border2_bearing = (selectedship.bearing - 45) % 360
        for bearing in [border1_bearing, border2_bearing]:
            border1_x1 = -minthrust_pixel * math.sin(math.radians(bearing)) + shipx_pixel
            border1_x2 = -maxthrust_pixel * math.sin(math.radians(bearing)) + shipx_pixel
            border1_y1 = -minthrust_pixel * math.cos(math.radians(bearing)) + shipy_pixel
            border1_y2 = -maxthrust_pixel * math.cos(math.radians(bearing)) + shipy_pixel
            pygame.draw.line(DISPLAYSURF,frost0, (border1_x1, border1_y1), (border1_x2, border1_y2))

        for i in [selectedship.minthrust,selectedship.maxthrust]:
            if i == 0: break
            selectedship_thrust_pixel,val = playarea.gridtopixel((i,0))
            selectedship_thrust_pixel = selectedship_thrust_pixel - playarea.rect.x
            # pygame.draw.circle(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship_thrust_pixel, 1)
            left = playarea.gridtopixel(selectedship.loc)[0] - selectedship_thrust_pixel
            top = playarea.gridtopixel(selectedship.loc)[1] - selectedship_thrust_pixel
            dim = 2*selectedship_thrust_pixel
            pygame.draw.arc(DISPLAYSURF, frost0, pygame.Rect(left,top, dim, dim), math.radians(border1_bearing), math.radians(border2_bearing-180))

        selectedship.draw_firingarcs(DISPLAYSURF)
        pygame.draw.line(DISPLAYSURF, frost0, playarea.gridtopixel(selectedship.loc), selectedship.rect.center)
        # DISPLAYSURF.blit(sprite.image,(sprite.x, sprite.y))
    # else:
    #     for ship in ships:
    #         if ship.hover:
                # infocard_bg = pygame.Rect(ship.rect.right,ship.rect.top+20,200,20)
                # pygame.draw.rect(DISPLAYSURF,(100,100,100),infocard_bg)
    
    for ui_el in ui:
        ui_el.draw(DISPLAYSURF)

    fps_font_surface = fps_font.render(f'{INTERNALCLOCK.get_fps():.1f}', True, (255,255,255))
    DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.flip()