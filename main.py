import pygame, sys, math
import numpy as np
from pygame.locals import *

selection_color = (255,0,0)

class Ship(pygame.sprite.Sprite):
    def __init__(self, playarea, loc=(0.0,0.0)):
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

class console:
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
                print(playarea.pixeltogrid(event.pos))
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

            if event.button == 3:            
                dragging = True
                mouse_x, mouse_y = event.pos
                draggable_offsets = []
                for draggable in draggables:
                    offset_x = draggable.rect.x - mouse_x
                    offset_y = draggable.rect.y - mouse_y
                    draggable_offsets.append([offset_x, offset_y])

            elif event.button == 4: # mouse wheel up
                for draggable in draggables:
                    draggable.zoom(.1)
                    # center = draggable.rect.center
                    # draggable.scale = draggable.scale*1.1
                    # draggable.image = pygame.transform.rotozoom(draggable.image0, 0, draggable.scale)
                    # draggable.rect = draggable.image.get_rect()
                    # draggable.rect.center = center
                    # print(draggable.scale)
                    # rectangle = draggable.rect
                    # if rectangle.width < 10*DISPLAYSURF.get_width() and rectangle.height < 10*DISPLAYSURF.get_height():
                    #     rectangle.inflate_ip(rectangle.width/10, rectangle.height/10)

            elif event.button == 5: # mouse wheel down
                min_frac = .8
                for draggable in draggables:
                    draggable.zoom(-.1)
                    # center = draggable.rect.center
                    # draggable.scale = draggable.scale*.9
                    # draggable.image = pygame.transform.rotozoom(draggable.image0, 0, draggable.scale)
                    # draggable.rect = draggable.image.get_rect()
                    # draggable.rect.center = center
                    # print(draggable.scale)
                    # rectangle = draggable.rect
                    # if rectangle.width > DISPLAYSURF.get_width()*min_frac or rectangle.height > DISPLAYSURF.get_height()*min_frac:
                    #     rectangle.inflate_ip(-rectangle.width/10, -rectangle.height/10)
        
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
                if dist > selectedship.thrust:
                    print(f'ship selection loc {selectedship.selection_loc}')
                    print(f'ship loc {selectedship.loc}')
                    center_x = (selectedship.selection_loc[0] - selectedship.loc[0])/dist*selectedship.thrust + selectedship.loc[0]
                    center_y = (selectedship.selection_loc[1] - selectedship.loc[1])/dist*selectedship.thrust + selectedship.loc[1]
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

        selectedship_thrust_pixel,val = playarea.gridtopixel((selectedship.thrust,0))
        selectedship_thrust_pixel = selectedship_thrust_pixel - playarea.rect.x
        pygame.draw.circle(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship_thrust_pixel, 1)

        selectedship.draw_firingarcs(DISPLAYSURF)
        pygame.draw.line(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship.rect.center)
        # DISPLAYSURF.blit(sprite.image,(sprite.x, sprite.y))
    
    # fps_font_surface = fps_font.render(str(INTERNALCLOCK.get_fps()),False,(255,255,255))
    # DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.flip()