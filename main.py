import pygame, sys, math
# import numpy as np
from pygame.locals import *
import pygame.gfxdraw
from enum import Enum
from ship import *
from guns import *
from helper import *
from ui import *
from queue import Queue
import random

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
gamecontroller.combatlog = combatlog
ui.append(combatlog)

p1_fleetpanel = FleetPanel('left', major_font, minor_font)
p2_fleetpanel = FleetPanel('right', major_font, minor_font)
ui.append(p1_fleetpanel)
ui.append(p2_fleetpanel)

infopanel = InfoPanel(major_font, minor_font)
ui.append(infopanel)

targetpanel = TargetPanel(minor_font)
ui.append(targetpanel)
infopanel.targetpanel = targetpanel
targetpanel.gamecontroller = gamecontroller
p1_ships = []
p2_ships = []

p1_fleetfile = open('p1.txt','r')
p1_fleetfile_lines = p1_fleetfile.readlines()
p2_fleetfile = open('p2.txt','r')
p2_fleetfile_lines = p2_fleetfile.readlines()

fleetfiles = [[p1_fleetpanel.battlegroups, p1_fleetfile_lines], [p2_fleetpanel.battlegroups, p2_fleetfile_lines]]
currentBG = None
# BG_sizemap = {'Pathfinder':1, 'Line':2, 'Vanguard':3, 'Flag':4}
for player, [fleetlist, lines] in enumerate(fleetfiles):
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
                if player == 0:
                    p1_ships.append(newship)
                elif player == 1:
                    p2_ships.append(newship)
                newship.player = player + 1
                newship.group = group
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

selectedship = None
hoveredship = None
show_cohesion = False
show_signature = False
dragging = False
targeting_ship = None
# selected_gun = None
firing_queue = []
playwindow = pygame.Rect(DISPLAYSURF.get_width()*.2,0,DISPLAYSURF.get_width()*.6,DISPLAYSURF.get_height()*.7)

while True:

    pygame.draw.rect(DISPLAYSURF,(0,0,0),pygame.Rect(0,0,DISPLAYSURF.get_width(),DISPLAYSURF.get_height()))
    # DISPLAYSURF.fill((0,0,0))

    for ship in ships:
        ship.update()

    # -----------------------------------------------------------------------------------
    # GET USER INPUT
    # -----------------------------------------------------------------------------------
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.VIDEORESIZE:
            DISPLAYSURF = pygame.display.set_mode((event.w,event.h), pygame.RESIZABLE)# | pygame.OPENGLBLIT)

        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if targetpanel.rect.collidepoint(event.pos):
                    if targetpanel.active and targetpanel.gun.active:
                        for index, rect in enumerate(targetpanel.target_rect_list):
                            if rect.collidepoint(event.pos):
                                targeted_ship = targetpanel.target_list[index]
                                firing_queue.append([targetpanel.gun, targeted_ship])
                                targetpanel.gun.active = False
                    break

                if gamecontroller.rect.collidepoint(event.pos):
                    if 'Select Player Order' not in gamecontroller.current_state:
                        gamecontroller.next_phase()
                    break

                if infopanel.rect.collidepoint(event.pos):
                    if not infopanel.selectedship:
                        break
                    print(f'checking self ship for state: {infopanel.selectedship.state}')
                    if infopanel.selected_gun and infopanel.selected_gun.rect.collidepoint(event.pos):
                        infopanel.selected_gun = None
                        targetpanel.active = False
                        
                    elif infopanel.selectedship.state is ShipState.FIRING and gamecontroller.firingphase():
                        for gun in infopanel.selectedship.guns:
                            if gun.rect.collidepoint(event.pos):
                                infopanel.selected_gun = gun
                                targetpanel.gun = gun
                                targetpanel.active = True
                                if gun.ship.player == 1:
                                    check_ships = p2_ships
                                if gun.ship.player == 2:
                                    check_ships = p1_ships
                                targetpanel.target_list = gun.get_targetable_ships(check_ships, playarea)

                if 'Planning' in gamecontroller.current_state:
                    bg_list = gamecontroller.bg_plan_screen.bgs
                    for index, bg in enumerate(bg_list):
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

                if 'Activate' in gamecontroller.current_state:
                    selectable_ships = []
                    for group in gamecontroller.active_bg.groups:
                        for ship in group:
                            selectable_ships.append(ship)
                else:
                    selectable_ships = ships

                if gamecontroller.ship_selectable():
                    # print('checking mouse click')
                    for ship in selectable_ships:
                        if ship.panel_rect.collidepoint(event.pos):
                            if infopanel.selectedship:
                                infopanel.selectedship.highlight = False
                            infopanel.selectedship = ship
                            ship.highlight = True
                            # infopanel.selectedship.is_selected = True

                        if ship.rect.collidepoint(event.pos):
                            if infopanel.selectedship:
                                infopanel.selectedship.highlight = False
                            infopanel.selectedship = ship
                            ship.highlight = True
                            if ship.state in [ShipState.SETUP, ShipState.MOVING]:
                                if not ship.is_selected:
                                    selectedship = ship
                                    draggables.remove(ship)
                                    # pos0 = playarea.pixeltogrid(ship.rect.center)
                                    selectoffset_x = ship.rect.center[0] - event.pos[0]
                                    selectoffset_y = ship.rect.center[1] - event.pos[1]
                                    ship.is_selected = True
                                    # if ship.state == ShipState.ACTIVATED:
                                        # ship.state = ShipState.MOVING
                                    # print(f'initial bearing {ship.bearing}')
                                else:
                                    draggables.append(ship)
                                    selectedship = None
                                    ship.is_selected = False
                                    ship.loc = playarea.pixeltogrid(ship.rect.center)
                                    ship.selection_loc = None
                                    ship.bearing = ship.selection_bearing
                                    combatlog.log.append(f'{ship.name} moved to {ship.loc[0]:.1f}, {ship.loc[1]:.1f} bearing {ship.bearing:.3f}')
                                    if ship.state is ShipState.MOVING:
                                        ship.state = ShipState.FIRING
                            elif ship.state is ShipState.FIRING:
                                if not gamecontroller.firingphase():
                                    combatlog.log.append('cannot fire, not all ships have moved!')
                                    break
                                if ship is not selectedship:
                                    selectedship = ship
                                    break
                                else:
                                    selectedship = None
                            break


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
            if event.key == pygame.K_c:
                show_cohesion = not show_cohesion
            if event.key == pygame.K_s:
                show_signature = not show_signature

    #-----------------------------------------------------------------------------------
    # DRAW STUFF
    #-----------------------------------------------------------------------------------
    # pygame.draw.rect(DISPLAYSURF,(255,255,255),rectangle)
    sprites.draw(DISPLAYSURF)
                    
    # infopanel.selectedship = None
    mousepos = pygame.mouse.get_pos()
    # infopanel.selectedship = hoveredship
    if infopanel.selected_gun:
        gun_to_draw = infopanel.selected_gun
    elif infopanel.hovered_gun:
        gun_to_draw = infopanel.hovered_gun
    else:
        gun_to_draw = None
    if gun_to_draw:
        gun_to_draw.draw(DISPLAYSURF, playarea)
        if gun_to_draw.linked > 0:
            gun_to_draw.linked_gun.draw(DISPLAYSURF, playarea, linked=True)
        if gun_to_draw.ship.player == 1:
            check_ships = p2_ships
        if gun_to_draw.ship.player == 2:
            check_ships = p1_ships
        if not targetpanel.active:
            targetable_ships = gun_to_draw.get_targetable_ships(check_ships,playarea)
            for ship in targetable_ships:
                pt1 = gun_to_draw.ship.rect.center
                pt2 = ship.rect.center
                pygame.draw.line(DISPLAYSURF, NordColors.frost0,pt1,pt2)
    
    if infopanel.selectedship:
        if infopanel.selected_gun and infopanel.selected_gun.ship is not infopanel.selectedship:
            infopanel.selected_gun = None
        pygame.draw.rect(DISPLAYSURF, NordColors.frost1, infopanel.selectedship.rect, 1)

    if targetpanel.active:
        if targetpanel.gun.ship is not infopanel.selectedship:
            targetpanel.active = False
        elif targetpanel.rect.collidepoint(mousepos):
            for index, rect in enumerate(targetpanel.target_rect_list):
                if rect.collidepoint(mousepos):
                    targeted_ship = targetpanel.target_list[index]
                    pt1 = gun_to_draw.ship.rect.center
                    pt2 = ship.rect.center
                    pygame.draw.line(DISPLAYSURF, NordColors.frost0,pt1,pt2)

    for ship in ships:
        # ship.hover = False
        if show_signature:
            if ship.player == 1:
                sig_color = NordColors.frost3
            else:
                sig_color = NordColors.aurora4
            x, y = ship.rect.center
            sig = playarea.scalegridtopixel(ship.sig)
            alpha = (128,)
            pygame.gfxdraw.filled_circle(DISPLAYSURF,x,y,sig,sig_color+alpha)

        # if not hoveredship_drawn and (ship.panel_rect.collidepoint(mousepos) or (ship.rect.collidepoint(mousepos))):
        #     hoveredship_drawn = True
        #     ship.hover = True
        #     pygame.draw.rect(DISPLAYSURF, NordColors.frost1, ship.rect, 1)
        #     hoveredship = ship
        #     if show_cohesion:
        #         for neighbor_ship in ship.group:
        #             if neighbor_ship is ship:
        #                 continue
        #             pygame.draw.line(DISPLAYSURF, NordColors.aurora3, neighbor_ship.rect.center, ship.rect.center)
                # print(f'ship hovered: {ship}')

    if selectedship and selectedship.state is ShipState.SETUP and selectedship.is_selected:
        # center = (selectoffset_x + mousepos[0], selectoffset_y + mousepos[1])
        center = mousepos
        selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of selectedship when selected
        center = playarea.gridtopixel(selectedship.selection_loc)

        selectedship.image = pygame.transform.rotozoom(selectedship.image0, selectedship.bearing, selectedship.scale)
        selectedship.rect = selectedship.image.get_rect()
        selectedship.rect.center = center

        selectedship.selection_bearing = selectedship.bearing

    if selectedship and selectedship.state is ShipState.MOVING and selectedship.is_selected:
        # center = (selectoffset_x + mousepos[0], selectoffset_y + mousepos[1])
        center = mousepos
        selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of selectedship when selected
        center = playarea.gridtopixel(selectedship.selection_loc)
        dist = math.sqrt(math.pow(selectedship.selection_loc[0] - selectedship.loc[0],2) + math.pow(selectedship.selection_loc[1] - selectedship.loc[1],2))
        # if dist > selectedship.maxthrust or dist < selectedship.minthrust:
            # print(f'selectedship selection loc {selectedship.selection_loc}')
            # print(f'selectedship loc {selectedship.loc}')
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
        # selectedship.update_loc(playarea)
        pygame.draw.rect(DISPLAYSURF, NordColors.frost1, selectedship.rect,1)

        # print(selectedship.bearing)
        minthrust_pixel = playarea.scalegridtopixel(selectedship.minthrust)
        maxthrust_pixel = playarea.scalegridtopixel(selectedship.maxthrust)
        selectedshipx_pixel = playarea.gridtopixel(selectedship.loc)[0]
        selectedshipy_pixel = playarea.gridtopixel(selectedship.loc)[1]
        border1_bearing = (selectedship.bearing + 45) % 360
        border2_bearing = (selectedship.bearing - 45) % 360
        for bearing in [border1_bearing, border2_bearing]:
            border1_x1 = -minthrust_pixel * math.sin(math.radians(bearing)) + selectedshipx_pixel
            border1_x2 = -maxthrust_pixel * math.sin(math.radians(bearing)) + selectedshipx_pixel
            border1_y1 = -minthrust_pixel * math.cos(math.radians(bearing)) + selectedshipy_pixel
            border1_y2 = -maxthrust_pixel * math.cos(math.radians(bearing)) + selectedshipy_pixel
            pygame.draw.line(DISPLAYSURF,NordColors.frost0, (border1_x1, border1_y1), (border1_x2, border1_y2))

        for i in [selectedship.minthrust,selectedship.maxthrust]:
            if i == 0: break
            selectedship_thrust_pixel,val = playarea.gridtopixel((i,0))
            selectedship_thrust_pixel = selectedship_thrust_pixel - playarea.rect.x
            # pygame.draw.circle(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship_thrust_pixel, 1)
            left = playarea.gridtopixel(selectedship.loc)[0] - selectedship_thrust_pixel
            top = playarea.gridtopixel(selectedship.loc)[1] - selectedship_thrust_pixel
            dim = 2*selectedship_thrust_pixel
            pygame.draw.arc(DISPLAYSURF, NordColors.frost0, pygame.Rect(left,top, dim, dim), math.radians(border1_bearing), math.radians(border2_bearing-180))

        selectedship.draw_firingarcs(DISPLAYSURF)
        pygame.draw.line(DISPLAYSURF, NordColors.frost0, playarea.gridtopixel(selectedship.loc), selectedship.rect.center)
        # DISPLAYSURF.blit(sprite.image,(sprite.x, sprite.y))
    # else:
    #     for ship in ships:
    #         if ship.hover:
                # infocard_bg = pygame.Rect(ship.rect.right,ship.rect.top+20,200,20)
                # pygame.draw.rect(DISPLAYSURF,(100,100,100),infocard_bg)
    for ui_el in ui:
        # if ui_el.needs_update:
        ui_el.draw(DISPLAYSURF)
            # ui_el.needs_update = False

    fps_font_surface = fps_font.render(f'{INTERNALCLOCK.get_fps():.1f}', True, (255,255,255))
    DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.update()