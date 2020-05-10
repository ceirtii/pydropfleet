import pygame, sys, math
# import numpy as np
from pygame.locals import *
from enum import Enum, auto
import csv

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

shipfile = open('ships.csv', encoding="utf-8-sig")
shipreader = csv.reader(shipfile)
shipDB = dict()
for row in shipreader:
    print(row)
    shipname,faction,scan,sig,thrust,hull,armor,pd,shiptype = row
    stats = {'faction':faction,'scan':int(scan),'sig':int(sig),'thrust':int(thrust),'hull':int(hull),'armor':int(armor),'pd':int(pd),'type':shiptype}
    shipDB.update({shipname:stats})
print(shipDB)
shipfile.close()

class Ship(pygame.sprite.Sprite):

    def __init__(self, playarea, loc=(10.0,10.0), name='test', shipclass='test'):
       pygame.sprite.Sprite.__init__(self)
       self.shipclass = shipclass
       self.faction = shipDB[shipclass]['faction']
       self.scan = shipDB[shipclass]['scan']
       self.sig = shipDB[shipclass]['sig']
       self.thrust = shipDB[shipclass]['thrust']
       self.hull = shipDB[shipclass]['hull']
       self.hp = self.hull
       self.armor = shipDB[shipclass]['armor']
       self.pd = shipDB[shipclass]['pd']
       self.shiptype = shipDB[shipclass]['type']

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
    
    def zoom(self, zoom_increment):
        self.rect.center = playarea.gridtopixel(self.loc)
        pass

    def draw_firingarcs(self, surf):
        pass
        # surf.draw
    
    def update_loc(self, playarea):
        if self.is_selected:
            self.selection_loc = playarea.pixeltogrid(self.rect.center)
            self.selection_bearing = self.bearing
        else:
            self.selection_loc = None
            self.loc = playarea.pixeltogrid(self.rect.center)
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
    def __init__(self, surf=None, width_frac=.6):
        self.log = []
        self.width = 0
        self.height = 0
        self.rect = None
        self.color = nord1
        self.font_color = snow0
        self.currentline = 0
        self.width_frac = width_frac
    
    def draw(self, surf):
        self.width = int(surf.get_width()*self.width_frac)
        self.height = int(surf.get_height()*.2)
        self.rect = pygame.Rect(surf.get_width()/2-self.width/2,surf.get_height()-self.height,self.width,self.height)
        pygame.draw.rect(surf, self.color, self.rect)
        
        printloglines = self.log.copy()
        printloglines.reverse()
        line_font = pygame.font.Font('kooten.ttf', 20)
        line_height = line_font.size('')[1]
        lines = int(self.height/line_height)
        if lines < len(printloglines):
            printloglines = printloglines[self.currentline:lines+self.currentline]
        printloglines.reverse()

        line_pixel = 0
        for line in printloglines:
            line_font_surface = line_font.render(line,True,self.font_color)
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
    def __init__(self, side, width_frac=.2):
        self.battlegroups = []
        self.width = 0
        self.height = 0
        self.rect = pygame.Rect(0,0,self.width,self.height)
        self.color = nord0
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

        line_font = pygame.font.Font('kooten.ttf', 18)
        minor_font = pygame.font.Font('kooten.ttf', 14)
        line_height = line_font.size('')[1]
        minor_height = minor_font.size('')[1]
        buffer = line_height/2
        y = self.rect.top + buffer
        for bg in self.battlegroups:
            font_render = line_font.render(str(bg),True,snow0)
            self.surf.blit(font_render,(self.rect.left + buffer, y))
            y = y + line_height + buffer
            for group in bg.groups:
                for ship in group:
                    font_render = line_font.render(f'{ship.faction} {ship.name}',True,snow1)
                    class_render = minor_font.render(f'{ship.shipclass}-class {ship.shiptype}',True,snow2)
                    box_height = line_height+2*minor_height+buffer
                    ship_box = pygame.Rect(self.rect.left+1.5*buffer, y-buffer/2, self.width-2*buffer, box_height)
                    pygame.draw.rect(self.surf, nord2, ship_box)

                    hull_string = f'{ship.hp}/{ship.hull}'
                    hull_string_width = line_font.size(hull_string)[0]
                    hull_render = line_font.render(hull_string, True, snow1)
                    self.surf.blit(hull_render, (self.rect.right-buffer-hull_string_width, y))

                    if ship.hover:
                        pygame.draw.rect(self.surf, frost0, ship_box, 2)
                    self.surf.blit(font_render, (self.rect.left + 2 * buffer, y))
                    y = y + line_height
                    self.surf.blit(class_render, (self.rect.left + 2 * buffer, y))
                    y = y + minor_height + buffer

                    hull_bar_length = ship_box.width-2*buffer
                    hp_start = ship_box.left+buffer
                    hp_end = ship_box.left+buffer+hull_bar_length*ship.hp/ship.hull
                    hull_end = hp_start+hull_bar_length
                    pygame.draw.line(self.surf,aurora3,(hp_start,y),(hp_end,y))
                    pygame.draw.line(self.surf,aurora0,(hp_end,y),(hull_end,y))

                    y = y + 2*buffer
                    
                y = y + buffer
        self.content_height = y
        surf.blit(self.surf,self.rect.topleft)

    def scroll(self, dir):
        scrollspeed = 20
        if self.rect.y == 0 and dir > 0:
            return
        if self.content_height <= self.height - self.rect.y and dir < 0:
            return
        self.rect.y = self.rect.y + dir*scrollspeed

class Battlegroup:
    def __init__(self, sr, size, points):
        self.size = size
        self.sr = sr
        self.points = points
        self.groups = []

    def __str__(self):
        out_str = f'SR{self.sr} {self.size} {self.points} pts'
        # for group in self.groups:
        #     out_str += f'\n{len(group)} {group[0].shipclass}'
        return out_str
    
class ShipGroup:
    def __init__(self):
        pass

pygame.init()
DISPLAYSURF = pygame.display.set_mode((1600,900), pygame.RESIZABLE)
pygame.display.set_caption('Hello World!')
INTERNALCLOCK = pygame.time.Clock()
fps_font = pygame.font.Font(None, 20)

sprites = pygame.sprite.Group()
draggables = []
draggable_offsets = []
playobjects = []
ships = pygame.sprite.Group()
ui = []
ui_needs_update = True

playarea = PlayArea()
playarea.scale = min(DISPLAYSURF.get_width()/playarea.rect.width, DISPLAYSURF.get_height()/playarea.rect.height)

playarea.image = pygame.transform.rotozoom(playarea.image0,0,playarea.scale)
playarea.rect = playarea.image.get_rect()
draggables.append(playarea)
sprites.add(playarea)

combatlog = CombatLog()
ui.append(combatlog)
p1_fleetpanel = FleetPanel('left',)
p2_fleetpanel = FleetPanel('right')
ui.append(p1_fleetpanel)
ui.append(p2_fleetpanel)

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
            currentBG.groups.append([Ship(playarea,shipclass=vals[2]) for i in range(int(vals[0]))])
# for bg in p1fleetlist:
#     print(bg)

p1_fleetfile.close()
p2_fleetfile.close()

for bg in p1_fleetpanel.battlegroups + p2_fleetpanel.battlegroups:
    for group in bg.groups:
        for ship1 in group:
            draggables.append(ship1)
            sprites.add(ship1)
            ships.add(ship1)

selectedship = None

dragging = False

while True:

    DISPLAYSURF.fill((0,0,0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            DISPLAYSURF = pygame.display.set_mode((event.w,event.h), pygame.RESIZABLE)
        elif event.type == MOUSEBUTTONDOWN:
            # DISPLAYSURF.set_at(pygame.mouse.get_pos(), Color(255,0,0))
            # print(pygame.mouse.get_pos())

            if event.button == 1:
                # print(playarea.pixeltogrid(event.pos))
                for ship in ships:
                    if ship.rect.collidepoint(event.pos):
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
            if selectedship:
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
                    
    for ship in ships:
        shiphovered = False
        if ship.rect.collidepoint(pygame.mouse.get_pos()) and not shiphovered:
            ship.hover = True
            shiphovered = True
        else:
            ship.hover = False
        
    # pygame.draw.rect(DISPLAYSURF,(255,255,255),rectangle)
    sprites.draw(DISPLAYSURF)
    # for ship in ships:
    if selectedship:
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
    else:
        for ship in ships:
            if ship.hover:
                infocard_bg = pygame.Rect(ship.rect.right,ship.rect.top+20,200,20)
                pygame.draw.rect(DISPLAYSURF,(100,100,100),infocard_bg)
    
    for ui_el in ui:
        ui_el.draw(DISPLAYSURF)
    fps_font_surface = fps_font.render(str(INTERNALCLOCK.get_fps()),False,(255,255,255))
    DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.flip()