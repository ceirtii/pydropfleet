import pygame, sys, math, io
from pygame.locals import *
import pygame.gfxdraw
from ship import *
from guns import *
from helper import *
from ui import *
from queue import Queue
import random

draw_fps = False
debug = True
if not debug:
    sys.stdout = io.StringIO()

print('starting program')
pygame.init()
DISPLAYSURF = pygame.display.set_mode((1600,900), pygame.RESIZABLE)# | pygame.OPENGLBLIT)
pygame.display.set_caption('Dropfleet Commander')
INTERNALCLOCK = pygame.time.Clock()
fps_font = pygame.font.Font('kooten.ttf', 20)

print('initializing ui')
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
playarea.scale = min(DISPLAYSURF.get_width()/playarea.rect.width, 
        DISPLAYSURF.get_height()/playarea.rect.height)

playarea.image = pygame.transform.rotozoom(playarea.image0,0,playarea.scale)
playarea.rect = playarea.image.get_rect()
draggables.append(playarea)
sprites.add(playarea)

print('loading clusters')
clusters = [
    Cluster((4, 24), [
        SectorType.COMMERCIAL, SectorType.INDUSTRIAL, SectorType.COMMERCIAL, SectorType.MILITARY
    ], playarea),
    Cluster((24, 24), [
        SectorType.MILITARY, SectorType.COMMERCIAL, SectorType.MILITARY, SectorType.INDUSTRIAL
    ], playarea),
    Cluster((44, 24), [
        SectorType.MILITARY, SectorType.COMMERCIAL, SectorType.INDUSTRIAL, SectorType.COMMERCIAL
    ], playarea),
    Cluster((12, 30), [
        SectorType.COMMERCIAL, SectorType.MILITARY, SectorType.INDUSTRIAL
    ], playarea),
    Cluster((36, 18), [
        SectorType.MILITARY, SectorType.INDUSTRIAL, SectorType.COMMERCIAL
    ], playarea)
]
for cluster in clusters:
    draggables.append(cluster)
    sprites.add(cluster)
    for sector in cluster.sectors:
        draggables.append(sector)
        sprites.add(sector)

title_font = pygame.font.Font('wscsnbd.ttf', 24)
major_font = pygame.font.Font('wscsnbd.ttf', 18)
minor_font = pygame.font.Font('wscsnrg.ttf', 14)
print('fonts loaded')

print('initializing gamecontroller')
gamecontroller = GameController(title_font, major_font, minor_font)
ui.append(gamecontroller)
launchsel_panel = gamecontroller.launchsel_panel
launchresolve_panel = gamecontroller.launchresolve_panel

print('initializing combat log')
combatlog = CombatLog(minor_font)
gamecontroller.combatlog = combatlog
ui.append(combatlog)

print('initializing fleet panels')
p1_fleetpanel = FleetPanel('left', major_font, minor_font)
p2_fleetpanel = FleetPanel('right', major_font, minor_font)
ui.append(p1_fleetpanel)
ui.append(p2_fleetpanel)
p1_fleetpanel.resize(DISPLAYSURF)
p2_fleetpanel.resize(DISPLAYSURF)

print('initializing info panel')
infopanel = InfoPanel(major_font, minor_font)
ui.append(infopanel)

print('initializing target panel')
targetpanel = TargetPanel(minor_font)
ui.append(targetpanel)
infopanel.targetpanel = targetpanel
targetpanel.gamecontroller = gamecontroller

print('initializing target queue')
targetqueue = TargetQueue(minor_font)
ui.append(targetqueue)
gamecontroller.target_queue = targetqueue

print('initializing squadron panel')
squadronpanel = SquadronPanel(minor_font, playarea)
ui.append(squadronpanel)
# gamecontroller.target_queue = targetqueue

print('initializing launch queue')
launchqueue = LaunchQueue(minor_font)
ui.append(launchqueue)
gamecontroller.launch_queue = launchqueue

print('initializing players')
player1 = Player(1, playarea)
player2 = Player(2, playarea)
player1.gamecontroller = gamecontroller
player2.gamecontroller = gamecontroller
gamecontroller.player1 = player1
gamecontroller.player2 = player2

print('loading fleets')
p1_fleetfile = open('p1.txt','r')
p2_fleetfile = open('p2.txt','r')
p1_fleetpanel.battlegroups = player1.load_fleet(p1_fleetfile)
p2_fleetpanel.battlegroups = player2.load_fleet(p2_fleetfile)

ships = []
for ship in player1.ships + player2.ships:
    sprites.add(ship)
    draggables.append(ship)
    ships.append(ship)

p1_fleetpanel.battlegroups_originalorder = [bg for bg in p1_fleetpanel.battlegroups]
p2_fleetpanel.battlegroups_originalorder = [bg for bg in p2_fleetpanel.battlegroups]

p1_fleetfile.close()
p2_fleetfile.close()

gamecontroller.p1_battlegroups = p1_fleetpanel.battlegroups
gamecontroller.p2_battlegroups = p2_fleetpanel.battlegroups

selectedship = None
hoveredship = None
show_cohesion = True
show_p1_sig = False
show_p2_sig = False
show_tooltip = True
dragging = False
targeting_ship = None
moving_ship = None
# selected_gun = None
# firing_queue = []
playwindow = pygame.Rect(DISPLAYSURF.get_width()*.2,0,DISPLAYSURF.get_width()*.6,DISPLAYSURF.get_height()*.7)

selection_color = NordColors.frost1

print('starting game')
while True:
    # DISPLAYSURF.fill((0,0,0))

    # for ship in ships:
    #     ship.update()

    # -----------------------------------------------------------------------------------
    # GET USER INPUT
    # -----------------------------------------------------------------------------------
    for event in pygame.event.get():
        ui_needs_update = True
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.VIDEORESIZE:
            DISPLAYSURF = pygame.display.set_mode((event.w,event.h), pygame.RESIZABLE)# | pygame.OPENGLBLIT)
            p1_fleetpanel.resize(DISPLAYSURF)
            p2_fleetpanel.resize(DISPLAYSURF)

        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                print(f'mouse click at {event.pos}')
                if launchresolve_panel.active and launchresolve_panel.rect.collidepoint(event.pos):
                    print('mouse click on launch resolve selection panel')
                    clicked_ship = launchresolve_panel.on_click(event.pos)
                    if clicked_ship is None:
                        continue
                    print(f'clicked on ship {str(clicked_ship)}')
                    gamecontroller.resolve_launch_assets(clicked_ship)
                    continue
                if launchsel_panel.active and launchsel_panel.rect.collidepoint(event.pos):
                    print('mouse click on launch group selection panel')
                    clicked_group = launchsel_panel.on_click(event.pos)
                    if clicked_group is None:
                        print('no ship clicked')
                        continue
                    print(f'clicked on group {str(clicked_group)}')
                    for ship in clicked_group:
                        ship.set_state(ShipState.LAUNCHING)
                    continue

                if targetpanel.active and targetpanel.rect.collidepoint(event.pos):
                    print('mouse click on target panel')
                    if targetpanel.gun.state is GunState.TARGETING:
                        for index, rect in enumerate(targetpanel.target_rect_list):
                            if rect.collidepoint(event.pos):
                                targeted_ship = targetpanel.target_list[index]
                                targetqueue.append(targetpanel.gun, targeted_ship)
                                targetpanel.gun.state = GunState.FIRED
                                # if targetpanel.gun.linked_gun is None:
                                    # targetpanel.gun.ship.fired_guns = targetpanel.gun.ship.fired_guns + 1
                    continue
                
                if squadronpanel.active and squadronpanel.rect.collidepoint(event.pos):
                    if gamecontroller.active_player is player1:
                        if squadronpanel.launch_asset.launch_type == 'Fighter':
                            squadronpanel.targetable_ships = player1.ships + player2.ships
                        else:
                            squadronpanel.targetable_ships = player2.ships
                    elif gamecontroller.active_player is player2:
                        if squadronpanel.launch_asset.launch_type == 'Fighter':
                            squadronpanel.targetable_ships = player1.ships + player2.ships
                        else:
                            squadronpanel.targetable_ships = player1.ships
                    squadronpanel.on_click(event.pos)
                    continue
                
                if squadronpanel.target_panel.squadron and squadronpanel.target_panel.rect.collidepoint(event.pos):
                    result = squadronpanel.target_panel.on_click(event.pos)
                    if result:
                        launching_sq = squadronpanel.target_panel.squadron
                        print('squadron launching')
                        if not launching_sq.ship.has_launched:
                            launching_sq.ship.has_launched = True
                            launching_sq.ship.apply_spike(1)
                        if launching_sq.launch_type == 'Bomber':
                            launching_sq.ship.bombers_launched = launching_sq.ship.bombers_launched + 1
                        launching_sq.launching = True
                        launchqueue.append(launching_sq, result)
                    continue

                if gamecontroller.rect.collidepoint(event.pos):
                    print('mouse click on next turn button')
                    if gamecontroller.resolve_attacks:
                        print('resolving next attack queued')
                        if not gamecontroller.target_queue.is_empty():
                            gun, target, count = gamecontroller.target_queue.pop()
                            result = gun.shoot(target, count)
                            print(result)
                            for line in result:
                                combatlog.append(line)
                    
                    # elif gamecontroller.resolve_launch:
                    #     print('resolving next launch target queued')
                    #     print(launchqueue)

                    elif 'Select Player Order' not in gamecontroller.current_state:
                        print('next phase')
                        if infopanel.selectedship:
                            print('unselecting ship on infopanel')
                            # infopanel.selectedship.highlight = False
                            infopanel.change_selected_obj(None)
                            if squadronpanel.active:
                                squadronpanel.active = False
                        gamecontroller.next_phase()
                        
                    elif 'Launch' in gamecontroller.current_state and 'Resolve' not in gamecontroller.current_state:
                        print('finishing launch activation for this ship')
                    continue

                if infopanel.rect.collidepoint(event.pos):
                    print('mouse click on infopanel')
                    if not infopanel.selectedship:
                        continue

                    if infopanel.selected_gun and infopanel.selected_gun.rect.collidepoint(event.pos):
                        infopanel.selected_gun = None
                        targetpanel.active = False
                        
                    elif isinstance(infopanel.selectedship, Ship):
                        print(f'checking self ship for state: {infopanel.selectedship.state}')
                        if infopanel.selectedship.state is ShipState.FIRING:
                            print('showing potential targets')
                            for gun in infopanel.selectedship.guns:
                                if gun.rect.collidepoint(event.pos):
                                    infopanel.selected_gun = gun
                                    targetpanel.gun = gun
                                    targetpanel.active = True
                                    # if gun.ship.player == 1:
                                    #     check_ships = p2_ships
                                    # if gun.ship.player == 2:
                                    #     check_ships = p1_ships
                                    targetpanel.target_list = gun.get_targetable_ships(check_ships, playarea)
                    continue
                
                if p1_fleetpanel.rect.collidepoint(event.pos) or p2_fleetpanel.rect.collidepoint(event.pos):
                    print('fleetpanel clicked')
                    bgs = player1.battlegroups + player2.battlegroups
                    clicked = False
                    for bg in bgs:
                        if bg.rect.collidepoint(event.pos):
                            print(f'battlegroup {str(bg)} clicked')
                            clicked = True
                            infopanel.change_selected_obj(bg)
                            break

                        for group in bg.groups:
                            if group.rect.collidepoint(event.pos):
                                print(f'shipgroup {str(group)} clicked')
                                print(group.rect)
                                clicked = True
                                infopanel.change_selected_obj(group)
                                break
                        if clicked:
                            break

                    if clicked:
                        continue

                if 'Planning' in gamecontroller.current_state:
                    print('checking for click on battlegroup selector')
                    bg_list = gamecontroller.bg_plan_screen.bgs
                    for index, bg in enumerate(bg_list):
                        if bg.up_arrow_rect and bg.up_arrow_rect.collidepoint(event.pos) and index > 0:
                            bg_list[index-1], bg_list[index] = bg_list[index], bg_list[index-1]
                            break
                        if bg.down_arrow_rect and bg.down_arrow_rect.collidepoint(event.pos) and index < len(bg_list)-1:
                            bg_list[index], bg_list[index+1] = bg_list[index+1], bg_list[index]
                            break
                    continue

                if 'Select Player Order' in gamecontroller.current_state:
                    print('checking for click on player activation order selection')
                    if gamecontroller.p1_button.collidepoint(event.pos):
                        gamecontroller.next_phase(next_player=1)
                    elif gamecontroller.p2_button.collidepoint(event.pos):
                        gamecontroller.next_phase(next_player=2)
                    continue

                if gamecontroller.ship_selectable():
                    
                    print('modifying selectable ships')
                    if 'Activate' in gamecontroller.current_state:
                        # print('modifying selectable ships if in an activation phase')
                        selectable_ships = []
                        for ship in gamecontroller.active_bg.get_ships():
                            selectable_ships.append(ship)

                    elif 'Launch' in gamecontroller.current_state:
                        selectable_ships = []
                        for ship in gamecontroller.active_player.ships:
                            if ship.state is ShipState.LAUNCHING:
                                selectable_ships.append(ship)

                    else:
                        selectable_ships = player1.ships + player2.ships

                    print(f'checking mouse click')
                    print(f'from list: {[str(ship) for ship in player1.ships]}')
                    for index, ship in enumerate(selectable_ships):
                        # print(f'checking ship {index}, {str(ship)}')
                        # print(f'ship rect: {ship.rect}')
                        # print(f'ship panel rect: {ship.panel_rect}')
                        # print(f'ship state: {ship.state}')

                        # if ship.rect.collidepoint(event.pos) and 'Launch' in gamecontroller.current_state:
                        #     if infopanel.selectedship:
                        #         if ship is infopanel.selectedship:
                        #             print('deselect ship if possible')
                        #         else:
                        #             print('target ship with launch asset')
                        #     else:
                        #         print('launch assets from this ship')
                        #         infopanel.selectedship = ship
                            
                        if ship.rect.collidepoint(event.pos) and ship is infopanel.selectedship:
                            if ship.state in [ShipState.SETUP, ShipState.MOVING]:
                                if moving_ship is None:
                                    print('moving selected ship')
                                    moving_ship = ship
                                    # infopanel.selectedship = ship
                                    # infopanel.change_selected_obj(ship)
                                    selectedship = ship
                                    draggables.remove(ship)
                                    # pos0 = playarea.pixeltogrid(ship.rect.center)
                                    selectoffset_x = ship.rect.center[0] - event.pos[0]
                                    selectoffset_y = ship.rect.center[1] - event.pos[1]
                                    # ship.is_selected = True
                                    # if ship.state == ShipState.ACTIVATED:
                                        # ship.state = ShipState.MOVING
                                    # print(f'initial bearing {ship.bearing}')
                                    break
                                else:
                                    print('finishing movement of selected ship')
                                    moving_ship = None
                                    # infopanel.selectedship = None
                                    # infopanel.change_selected_obj(None)
                                    draggables.append(ship)
                                    selectedship = None
                                    ship.is_selected = False
                                    ship.loc = playarea.pixeltogrid(ship.rect.center)
                                    ship.selection_loc = None
                                    ship.bearing = ship.selection_bearing
                                    move_str = f'{ship.name} moved to {ship.loc[0]:.1f},'
                                    move_str = move_str + f' {ship.loc[1]:.1f} bearing {int(ship.bearing)}'
                                        
                                    if ship.moving_up:
                                        ship.move_up()
                                        move_str = move_str + f' up to {ship.layer.name}'

                                    elif ship.moving_down:
                                        ship.move_down()
                                        move_str = move_str + f' down to {ship.layer.name}'

                                    combatlog.log.append(move_str)

                                    if ship.state is ShipState.MOVING:
                                        ship.set_state(ShipState.FIRING)
                                    break
                            # elif ship.state is ShipState.FIRING:
                            #     if not gamecontroller.firingphase():
                            #         combatlog.log.append('cannot fire, not all ships have moved!')
                            #         break
                            #     elif ship is not selectedship:
                            #         selectedship = ship
                            #         break
                            #     else:
                            #         selectedship = None
                            #         break
                        if ship.rect.collidepoint(event.pos) or ship.panel_rect.collidepoint(event.pos):
                            print(f'ship {index} panel or box clicked')
                            if infopanel.selectedship and ship is infopanel.selectedship:
                                print('unselecting ship on infopanel')
                                infopanel.change_selected_obj(None)
                                if squadronpanel.active:
                                    squadronpanel.active = False
                            else:
                                print('selecting new infopanel ship')
                                # if infopanel.selectedship:
                                #     infopanel.selectedship.highlight = False
                                infopanel.change_selected_obj(ship)
                                # ship.highlight = True
                                if 'Launch' in gamecontroller.current_state and 'Resolve' not in gamecontroller.current_state:
                                    print('show squadron launch panel')
                                    if 'Bomber' in gamecontroller.current_state:
                                        squadronpanel.launch_asset = ship.bombers
                                    elif 'Fighter' in gamecontroller.current_state:
                                        squadronpanel.launch_asset = ship.fighters
                                    elif 'Dropship' in gamecontroller.current_state:
                                        squadronpanel.launch_asset = ship.dropships
                                    elif 'Bulk' in gamecontroller.current_state:
                                        squadronpanel.launch_asset = ship.bulk_landers
                                    squadronpanel.active = True
                            for gun in ship.guns:
                                gun.get_targetable_ships(selectable_ships, playarea)
                            # ship.launch_range(player1.ships + player2.ships)
                    continue

                print('did nothing with mouse click')

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
            # print(f'key pressed: {event.key}')
            if event.key == pygame.K_ESCAPE:
                if selectedship:
                    draggables.append(selectedship)
                    selectedship.is_selected = False
                    selectedship.selection_loc = None
                    print(f'{selectedship.loc}, {playarea.gridtopixel(selectedship.loc)}')
                    selectedship.image = pygame.transform.rotozoom(selectedship.image0, 
                            selectedship.bearing, 
                            selectedship.scale)
                    selectedship.rect = selectedship.image.get_rect()
                    selectedship.rect.center = playarea.gridtopixel(selectedship.loc)
                    print(f'returned to {playarea.pixeltogrid(selectedship.rect.center)}, {selectedship.rect.center}')
                    selectedship = None
                    moving_ship = None
                elif infopanel.selectedship:
                    infopanel.selectedship.highlight = False
                    infopanel.change_selected_obj(None)

            if event.key == pygame.K_a:
                for ship in ships:
                    if ship.rect.collidepoint(pygame.mouse.get_pos()):
                        ship.hp = ship.hp - 1

            if event.key == pygame.K_c:
                print('toggle cohesion display')
                show_cohesion = not show_cohesion

            if event.key == pygame.K_s:
                if not show_p1_sig and not show_p2_sig:
                    show_p1_sig = True
                elif show_p1_sig:
                    show_p1_sig = False
                    show_p2_sig = True
                elif show_p2_sig:
                    show_p2_sig = False
                else:
                    print('how did you get here?')
                    raise Exception

            if event.key == pygame.K_q:
                if selectedship and selectedship.state is ShipState.SETUP:
                    selectedship.bearing = selectedship.bearing + 45
                    print(f'new bearing {selectedship.bearing}')

            if event.key == pygame.K_e:
                if selectedship and selectedship.state is ShipState.SETUP:
                    selectedship.bearing = selectedship.bearing - 45
                    print(f'new bearing {selectedship.bearing}')

            if event.key == pygame.K_t:
                show_tooltip = not show_tooltip
            
            if event.key == pygame.K_PAGEUP:
                print('check move up conditions:')
                print(f'selectedship={selectedship}')
                print(f'selectedship moving? {selectedship.state}')
                print(f'selectedship selected? {selectedship.is_selected}')

                if selectedship.moving_down:
                    print('cancelling move down')
                    selectedship.moving_down = False
                elif selectedship and selectedship.state is ShipState.MOVING and selectedship.is_selected:
                    print('check ship conditions')
                    if selectedship.layer is not OrbitalLayer.HIGH_ORBIT and selectedship.can_turn and selectedship.thrust >= 4:
                        print('moving up by one layer')
                        selectedship.moving_up = True

            if event.key == pygame.K_PAGEDOWN:
                print('check move down conditions:')
                print(f'selectedship={selectedship}')
                print(f'selectedship moving? {selectedship.state}')
                print(f'selectedship selected? {selectedship.is_selected}')

                if selectedship.moving_up:
                    print('cancelling move up')
                    selectedship.moving_up = False
                elif selectedship and selectedship.state is ShipState.MOVING and selectedship.is_selected:
                    print('check ship conditions')
                    if selectedship.layer is not OrbitalLayer.ATMOSPHERE and selectedship.can_turn:
                        print('moving down by one layer')
                        selectedship.moving_down = True

    player1.update()
    player2.update()
    gamecontroller.update()
    infopanel.update()

    #-----------------------------------------------------------------------------------
    # DRAW STUFF
    #-----------------------------------------------------------------------------------
    # pygame.draw.rect(DISPLAYSURF,(255,255,255),rectangle)
    if ui_needs_update:    
        pygame.draw.rect(DISPLAYSURF,(0,0,0),pygame.Rect(0,0,DISPLAYSURF.get_width(),DISPLAYSURF.get_height()))
        sprites.draw(DISPLAYSURF)
        pygame.draw.rect(DISPLAYSURF, NordColors.snow0, playarea.rect, 2)
                    
    # infopanel.selectedship = None
    mousepos = pygame.mouse.get_pos()
    # infopanel.selectedship = hoveredship
    if infopanel.selected_gun:
        # print('drawing infopanel selected gun')
        gun_to_draw = infopanel.selected_gun
    elif infopanel.hovered_gun:
        # print('drawing infopanel hovered gun')
        gun_to_draw = infopanel.hovered_gun
    else:
        # print('no gun to draw')
        gun_to_draw = None
    if ui_needs_update and gun_to_draw is not None:
        # print(gun_to_draw)
        gun_to_draw.draw(DISPLAYSURF, playarea)
        if gun_to_draw.linked > 0:
            gun_to_draw.linked_gun.draw(DISPLAYSURF, playarea, linked=True)
        
        check_ships = []
        if gun_to_draw.ship.player is player1:
            for ship in player2.ships:
                if ship.state is not ShipState.DESTROYED:
                    check_ships.append(ship)
        elif gun_to_draw.ship.player is player2:
            for ship in player1.ships:
                if ship.state is not ShipState.DESTROYED:
                    check_ships.append(ship)
        if not targetpanel.active:
            targetable_ships = gun_to_draw.get_targetable_ships(check_ships,playarea)
            for ship in targetable_ships:
                pt1 = gun_to_draw.ship.rect.center
                pt2 = ship.rect.center
                pygame.draw.line(DISPLAYSURF, NordColors.frost0,pt1,pt2)
        else:
            if targetpanel.rect.collidepoint(mousepos):
                for index, rect in enumerate(targetpanel.target_rect_list):
                    if rect.collidepoint(mousepos):
                        targeted_ship = targetpanel.target_list[index]
                        pt1 = gun_to_draw.ship.rect.center
                        pt2 = targeted_ship.rect.center
                        pygame.draw.line(DISPLAYSURF, NordColors.frost0,pt1,pt2)
    
    if ui_needs_update and infopanel.selectedship:
        if isinstance(infopanel.selectedship, Ship):
            if show_cohesion:
                infopanel.selectedship.draw_cohesion(DISPLAYSURF)
            if infopanel.selected_gun and infopanel.selected_gun.ship is not infopanel.selectedship:
                infopanel.selected_gun = None
            pygame.draw.rect(DISPLAYSURF, NordColors.frost1, infopanel.selectedship.rect, 1)
            if infopanel.selectedship.player is player1:
                check_ships = player2.ships
            elif infopanel.selectedship.player is player2:
                check_ships = player1.ships
            for gun in infopanel.selectedship.guns:
                targetable_ships = gun.get_targetable_ships(check_ships,playarea)
    
    if targetpanel.active:
        if targetpanel.gun.ship is not infopanel.selectedship:
            targetpanel.active = False
    
    if squadronpanel.active:
        squadrons = squadronpanel.launch_asset.squadrons
        for squadron in squadrons:
            if squadron is not squadronpanel.selected_squadron and squadron.rect.collidepoint(mousepos):
                squadron.highlight = True
            else:
                squadron.highlight = False
        
        if ui_needs_update and squadronpanel.selected_squadron:
            squadron = squadronpanel.selected_squadron
            ship = squadron.ship
            center = ship.rect.center
            thrust_px = playarea.scalegridtopixel(squadron.thrust)
            pygame.gfxdraw.filled_circle(DISPLAYSURF, center[0], center[1], thrust_px*2, NordColors.frost0 + (96,))
            pygame.draw.circle(DISPLAYSURF, NordColors.frost1, center, thrust_px, 1)
            pygame.draw.circle(DISPLAYSURF, NordColors.frost1, center, thrust_px*2, 1)

    # DRAW STUFF FOR ALL THE SHIPS
    if ui_needs_update:
        for ship in player1.ships + player2.ships:
            if ship.state is ShipState.DESTROYED and ship in ships:
                ships.remove(ship)
                if ship in draggables:
                    draggables.remove(ship)
                if ship in sprites:
                    sprites.remove(ship)
                if ship in player1.ships:
                    player1.ships.remove(ship)
                if ship in player2.ships:
                    player2.ships.remove(ship)

            if show_p1_sig and ship in player1.ships:
                ship.draw_sig(DISPLAYSURF)
            elif show_p2_sig and ship in player2.ships:
                ship.draw_sig(DISPLAYSURF)

            if ship.panel_rect.collidepoint(mousepos) or ship.rect.collidepoint(mousepos):
                if show_tooltip and ship.rect.collidepoint(mousepos):
                    ship.draw_tooltip(DISPLAYSURF, mousepos, minor_font)
                # hoveredship_drawn = True
                ship.hover = True
                # hoveredship = ship
                    # print(f'ship hovered: {ship}')
            if ship.hover:
                pygame.draw.rect(DISPLAYSURF, NordColors.frost2, ship.rect, 1)
                if show_cohesion:
                    ship.draw_cohesion(DISPLAYSURF)
            ship.update()

    # show sectors
    if ui_needs_update and selectedship and selectedship.is_selected:
        # print('drawing arcs')
        segments = [11.25,33.75,90,90,90,33.75]
        draw_dist = playarea.scalegridtopixel(selectedship.scan)
        if selectedship.selection_bearing:
            angle = selectedship.selection_bearing
        else:
            angle = selectedship.bearing
        x0, y0 = selectedship.rect.center
        for arc in segments:
            angle = angle + arc
            x1 = x0 - draw_dist * math.sin(math.radians(angle))
            y1 = y0 - draw_dist * math.cos(math.radians(angle))
            pygame.draw.line(DISPLAYSURF, selection_color, (x0,y0), (x1,y1))
        pygame.draw.circle(DISPLAYSURF, selection_color, (x0,y0), draw_dist, 1)

    # just move the ship
    if selectedship and selectedship.state is ShipState.SETUP and selectedship.is_selected:
        # center = (selectoffset_x + mousepos[0], selectoffset_y + mousepos[1])
        center = mousepos
        selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of selectedship when selected
        center = playarea.gridtopixel(selectedship.selection_loc)

        selectedship.image = pygame.transform.rotozoom(selectedship.image0, selectedship.bearing, selectedship.scale)
        selectedship.rect = selectedship.image.get_rect()
        selectedship.rect.center = center

        selectedship.selection_bearing = selectedship.bearing

    # move the ship and limit movement to thrust and max turn
    if selectedship and selectedship.state is ShipState.MOVING and selectedship.is_selected:
        # center = (selectoffset_x + mousepos[0], selectoffset_y + mousepos[1])
        center = mousepos
        selectedship.selection_loc = playarea.pixeltogrid(center) #grid location of selectedship when selected
        center = playarea.gridtopixel(selectedship.selection_loc)
        dist = math.dist(selectedship.selection_loc, selectedship.loc)
        # if dist > selectedship.maxthrust or dist < selectedship.minthrust:
            # print(f'selectedship selection loc {selectedship.selection_loc}')
            # print(f'selectedship loc {selectedship.loc}')
        
        maxthrust = selectedship.max_thrust()
        minthrust = selectedship.min_thrust()
        # modify thrust values for moving up an orbital layer
        # if selectedship.moving_up:
        #     maxthrust = maxthrust - 4
        #     if maxthrust < 0:
        #         maxthrust = 0
        #     minthrust = minthrust - 4
        #     if minthrust < 0:
        #         minthrust = 0

        if dist > maxthrust:
            thrust = maxthrust
        elif dist < minthrust:
            thrust = minthrust
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
        if ui_needs_update:
            pygame.draw.rect(DISPLAYSURF, NordColors.frost1, selectedship.rect,1)

        # print(selectedship.bearing)
        # minthrust_pixel = playarea.scalegridtopixel(selectedship.minthrust)
        # maxthrust_pixel = playarea.scalegridtopixel(selectedship.maxthrust)
        # selectedshipx_pixel = playarea.gridtopixel(selectedship.loc)[0]
        # selectedshipy_pixel = playarea.gridtopixel(selectedship.loc)[1]
        # border1_bearing = (selectedship.bearing + 45) % 360
        # border2_bearing = (selectedship.bearing - 45) % 360
        # for bearing in [border1_bearing, border2_bearing]:
        #     border1_x1 = -minthrust_pixel * math.sin(math.radians(bearing)) + selectedshipx_pixel
        #     border1_x2 = -maxthrust_pixel * math.sin(math.radians(bearing)) + selectedshipx_pixel
        #     border1_y1 = -minthrust_pixel * math.cos(math.radians(bearing)) + selectedshipy_pixel
        #     border1_y2 = -maxthrust_pixel * math.cos(math.radians(bearing)) + selectedshipy_pixel
        #     pygame.draw.line(DISPLAYSURF,
        #             NordColors.frost0, 
        #             (border1_x1, border1_y1), 
        #             (border1_x2, border1_y2))

        r1 = playarea.scalegridtopixel(minthrust)
        r2 = playarea.scalegridtopixel(maxthrust)
        t1 = math.radians((selectedship.bearing + 45) % 360)
        t2 = t1 + math.pi/2
        ship_x = playarea.gridtopixel(selectedship.loc)[0]
        ship_y = playarea.gridtopixel(selectedship.loc)[1]
        if ui_needs_update:
            fill_sector(DISPLAYSURF, (ship_x, ship_y), r1, r2, t1, t2, NordColors.frost0 + (96,))

        # for i in [selectedship.minthrust,selectedship.maxthrust]:
        #     if i == 0: break
        #     selectedship_thrust_pixel,val = playarea.gridtopixel((i,0))
        #     selectedship_thrust_pixel = selectedship_thrust_pixel - playarea.rect.x
        #     # pygame.draw.circle(DISPLAYSURF, selection_color, playarea.gridtopixel(selectedship.loc), selectedship_thrust_pixel, 1)
        #     left = playarea.gridtopixel(selectedship.loc)[0] - selectedship_thrust_pixel
        #     top = playarea.gridtopixel(selectedship.loc)[1] - selectedship_thrust_pixel
        #     dim = 2*selectedship_thrust_pixel
        #     pygame.draw.arc(DISPLAYSURF, 
        #             NordColors.frost0, 
        #             pygame.Rect(left,top, dim, dim), 
        #             math.radians(border1_bearing), 
        #             math.radians(border2_bearing-180))

        if ui_needs_update:
            selectedship.draw_firingarcs(DISPLAYSURF)
            pygame.draw.line(DISPLAYSURF, 
                    NordColors.frost0, 
                    playarea.gridtopixel(selectedship.loc), 
                    selectedship.rect.center)
        
        # if selectedship.moving_down:
        #     up_indicator = title_font.render('\\/', True, NordColors.frost0)
        #     DISPLAYSURF.blit(up_indicator, center)

        # DISPLAYSURF.blit(sprite.image,(sprite.x, sprite.y))
    # else:
    #     for ship in ships:
    #         if ship.hover:
                # infocard_bg = pygame.Rect(ship.rect.right,ship.rect.top+20,200,20)
                # pygame.draw.rect(DISPLAYSURF,(100,100,100),infocard_bg)
    if ui_needs_update:
        for ui_el in ui:
            ui_el.draw(DISPLAYSURF)
        ui_needs_update = False
    for ship in player1.ships + player2.ships:
        ship.hover = False
    if draw_fps:
        fps_font_surface = fps_font.render(f'{INTERNALCLOCK.get_fps():.1f}', 
                True, 
                (255,255,255))
        DISPLAYSURF.blit(fps_font_surface,(0,0))

    INTERNALCLOCK.tick()
    pygame.display.update()