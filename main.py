import pygame, sys, math
import numpy as np
from pygame.locals import *
from enum import Enum, auto

selection_color = (255,0,0)

class Ship(pygame.sprite.Sprite):

    def __init__(self, playarea, loc=(0.0,0.0), name='test'):
       pygame.sprite.Sprite.__init__(self)
       self.image0 = pygame.image.load('blueship.png').convert_alpha()
       self.scale = .2
       self.image = pygame.transform.rotozoom(self.image0, 90, self.scale)
       self.rect = self.image.get_rect()
       self.playarea = playarea
       self.loc = loc
       self.rect.center = playarea.gridtopixel(loc)
       self.is_selected = False
       self.selection_loc = None
       self.bearing = 0
       self.thrust = 10
       self.name = name
       self.order = ShipOrder.STANDARD
       self.minthrust = self.thrust/2
       self.maxthrust = self.thrust
    
    def zoom(self, zoom_increment):
        self.rect.center = playarea.gridtopixel(self.loc)
        pass

    def draw_firingarcs(self, surf):
        pass
        # surf.draw
    
    def update_loc(self, playarea):
        if self.is_selected:
            self.selection_loc = playarea.pixeltogrid(self.rect.center)
        else:
            self.selection_loc = None
            self.loc = playarea.pixeltogrid(self.rect.center)
        print(f'new location {self.loc}')

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

class CombatLog:
    def __init__(self, surf):
        self.log = []
        self.width = 0
        self.height = 0
        self.rect = None
        self.color = (100,100,100)
        self.font_color = (255,255,255)
        self.currentline = 0
    
    def draw(self, surf):
        self.width = int(surf.get_width()*.3)
        self.height = int(surf.get_height()*.2)
        self.rect = pygame.Rect(surf.get_width()-self.width,surf.get_height()-self.height,self.width,self.height)
        pygame.draw.rect(surf, self.color, self.rect)
        
        printloglines = self.log.copy()
        printloglines.reverse()
        lines = int(self.height/20)
        if lines < len(printloglines):
            printloglines = printloglines[self.currentline:lines+self.currentline]
        printloglines.reverse()

        line_pixel = 0
        for line in printloglines:
            line_font = pygame.font.Font(None, 20)
            line_font_surface = line_font.render(line,False,self.font_color)
            surf.blit(line_font_surface,(self.rect.x, self.rect.y + line_pixel))
            line_pixel += 20
    
    def scroll(self, dir):
        if len(self.log)*20 < self.height:
            return
        if self.currentline + dir < 0:
            return
        if self.currentline + dir + self.height/20 - 1 >= len(self.log):
            return
        self.currentline += dir

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

playarea = PlayArea()
playarea.scale = min(DISPLAYSURF.get_width()/playarea.rect.width, DISPLAYSURF.get_height()/playarea.rect.height)

playarea.image = pygame.transform.rotozoom(playarea.image0,0,playarea.scale)
playarea.rect = playarea.image.get_rect()
draggables.append(playarea)
sprites.add(playarea)

ship1 = Ship(playarea)
draggables.append(ship1)
sprites.add(ship1)
ships.add(ship1)

combatlog = CombatLog(DISPLAYSURF)
ui.append(combatlog)

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
            DISPLAYSURF.set_at(pygame.mouse.get_pos(), Color(255,0,0))
            # print(pygame.mouse.get_pos())

            if event.button == 1:
                # print(playarea.pixeltogrid(event.pos))
                for ship in ships:
                    if ship.rect.collidepoint(pygame.mouse.get_pos()):
                        if ship != selectedship:
                            selectedship = ship
                            draggables.remove(ship)
                            # pos0 = playarea.pixeltogrid(ship.rect.center)
                            selectoffset_x = ship.rect.center[0] - event.pos[0]
                            selectoffset_y = ship.rect.center[1] - event.pos[1]
                            ship.is_selected = True
                        else:
                            draggables.append(ship)
                            selectedship = None
                            ship.is_selected = False
                            ship.loc = playarea.pixeltogrid(ship.rect.center)
                            ship.selection_loc = None
                            combatlog.log.append(f'{ship.name} moved to {ship.loc[0]:.1f}, {ship.loc[1]:.1f}')

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
                move_pos = playarea.gridtopixel(selectedship.loc)
                dist = math.sqrt(math.pow(selectedship.selection_loc[0] - selectedship.loc[0],2) + math.pow(selectedship.selection_loc[1] - selectedship.loc[1],2))
                if dist > selectedship.maxthrust or dist < selectedship.minthrust:
                    # print(f'ship selection loc {selectedship.selection_loc}')
                    # print(f'ship loc {selectedship.loc}')
                    if dist > selectedship.maxthrust:
                        thrust = selectedship.maxthrust
                    else:
                        thrust = selectedship.minthrust
                    if dist == 0: dist = .001
                    center_x = (selectedship.selection_loc[0] - selectedship.loc[0])/dist*thrust + selectedship.loc[0]
                    center_y = (selectedship.selection_loc[1] - selectedship.loc[1])/dist*thrust + selectedship.loc[1]
                    center = playarea.gridtopixel((center_x,center_y))
                # print(dist)
                
                x = center[0] - move_pos[0]
                y = center[1] - move_pos[1]
                if x == 0:
                    if y > 0:
                        bearing = 180
                    else:
                        bearing = 0
                elif x < 0:
                    bearing = 90-math.degrees(math.atan(y/x))
                else:
                    bearing = 270-math.degrees(math.atan(y/x))
                selectedship.bearing = bearing
                # print(bearing)

                selectedship.image = pygame.transform.rotozoom(selectedship.image0, bearing, selectedship.scale)
                selectedship.rect = selectedship.image.get_rect()
                selectedship.rect.center = center
            if dragging:
                mouse_x, mouse_y = event.pos
                for index, draggable in enumerate(draggables):
                    draggable.rect.x = mouse_x + draggable_offsets[index][0]
                    draggable.rect.y = mouse_y + draggable_offsets[index][1]

    # pygame.draw.rect(DISPLAYSURF,(255,255,255),rectangle)
    sprites.draw(DISPLAYSURF)
    # for ship in ships:
    if selectedship:
        # selectedship.update_loc(playarea)
        pygame.draw.rect(DISPLAYSURF, selection_color, selectedship.rect,1)

        for i in [selectedship.minthrust,selectedship.maxthrust]:
            if i == 0: break
            selectedship_thrust_pixel,val = playarea.gridtopixel((i,0))
            selectedship_thrust_pixel = selectedship_thrust_pixel - playarea.rect.x
            pygame.draw.circle(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship_thrust_pixel, 1)

        selectedship.draw_firingarcs(DISPLAYSURF)
        pygame.draw.line(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship.rect.center)
        # DISPLAYSURF.blit(sprite.image,(sprite.x, sprite.y))
    
    for ui_el in ui:
        ui_el.draw(DISPLAYSURF)
    # fps_font_surface = fps_font.render(str(INTERNALCLOCK.get_fps()),False,(255,255,255))
    # DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.flip()