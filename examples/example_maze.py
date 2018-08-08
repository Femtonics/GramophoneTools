''' 3 different zones. Aversive is punishing '''

import GramophoneTools.LinMaze.Level as Level

if __name__ == '__main__':

    LVL = Level(
        name="Example Maze",
        screen_res=(800, 600),
        zone_offset=400,
        transition_width=100,
        rgb=(.9,1,.9)
    )

    # FRAMES
    LVL.add_block('cloud',  length=1280, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=0, zone_type='aversive')
    LVL.add_block('cloud',  length=1280, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=315, zone_type='left')
    LVL.add_block('cloud',  length=1920, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=45, zone_type='right')
    LVL.add_block('cloud',  length=6400, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=45, zone_type='right')
    LVL.add_block('cloud',  length=1920, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=315, zone_type='left')
    LVL.add_block('cloud',  length=1920, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=0, zone_type='aversive')
    LVL.add_block('cloud',  length=3840, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=315, zone_type='left')
    LVL.add_block('cloud',  length=1920, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=0, zone_type='aversive')
    LVL.add_block('cloud',  length=3840, zone_type='neutral')
    LVL.add_block('square', length=1280, wavelength=150, angle=45, zone_type='right')
    LVL.add_block('cloud',  length=1280, zone_type='neutral')
    
    # EVENTS
    LVL.add_event('tp_to_non_neutral', 'random_teleport', ['right', 'left','aversive'])
    LVL.add_event('tp_to_any', 'random_teleport', ['neutral','left','right','aversive'])
    
    LVL.add_event('start_front_puffs', 'start_burst', 1, 1.5, 0.5)
    LVL.add_event('stop_front_puffs', 'stop_burst', 1)
    
    LVL.add_event('start_back_puffs', 'start_burst', 2, 0.7, 0.25)
    LVL.add_event('stop_back_puffs', 'stop_burst', 2)

    LVL.add_event('say_hello', 'print', 'Hello!')

    # RULES
    LVL.add_rule('zone', 'tp_to_non_neutral', 'neutral', 12)
    LVL.add_rule('zone', 'tp_to_any', 'right', 12)
    LVL.add_rule('zone', 'tp_to_any', 'left', 12)
    
    LVL.add_rule('zone', 'start_back_puffs', 'aversive', 3.5)
    LVL.add_rule('zone', 'stop_back_puffs', 'neutral', 0)
    LVL.add_rule('zone', 'stop_back_puffs', 'left', 0)
    LVL.add_rule('zone', 'stop_back_puffs', 'right', 0)
    
    LVL.add_rule('velocity', 'start_front_puffs', 'above', 5, 8)
    LVL.add_rule('velocity', 'stop_front_puffs', 'below', 5, 0)

    LVL.add_rule('keypress', 'tp_to_any', 'F1')
    LVL.add_rule('input', 'say_hello', 1, 'rise')

    LVL.play(left_monitor=1, right_monitor=None, vel_ratio=2*1280, fullscreen=False, skip_save=True)
