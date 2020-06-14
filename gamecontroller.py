import pygame
from ui import *

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
