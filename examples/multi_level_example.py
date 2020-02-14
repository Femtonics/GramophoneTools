"""Example fro the teleportation between levels"""

from GramophoneTools.LinMaze import LevelCollection

if __name__ == '__main__':
    # Create a LevelCollection to store levels with different frames
    collection = LevelCollection(name="Example Maze",
                                 screen_res=(800, 600),
                                 zone_offset=400)

    # Create levels using the collection. 'create_level' function will return
    # a level and add it to the list of levels as well. The variable containing
    # the level object doesn't _have_ to be called the same as the 'name'
    # attribute, but makes sense if it does.

    # name: the level can be referenced by this later.
    # transition_width: number of pixels to create a transition between
    #     two blocks.
    #     Note: the frames will be this much longer.
    # rgb: not sure. as before
    main_level = collection.create_level(name="main_level",
                                         transition_width=100,
                                         rgb=(.9, 1, .9))

    neutral_level = collection.create_level(name="neutral_level",
                                            transition_width=100,
                                            rgb=(.9, 1, .9))

    wood_level = collection.create_level(name="wood_level",
                                         transition_width=100,
                                         rgb=(.9, 1, .9))

    # Create frames using the level variables. Take care which block you put in
    # which level. If you want to loop the same type of block, put more than one
    # into the level, otherwise it is going to be ugly rendered.
    main_level.add_block('square', length=1280, wavelength=150, angle=-45, zone_type='aversive')
    main_level.add_block('square', length=1280, wavelength=150, angle=45, zone_type='aversive')
    main_level.add_block('cloud', length=1280, zone_type='neutral')

    neutral_level.add_block('cloud', length=1280, zone_type='neutral')
    neutral_level.add_block('cloud', length=1280, zone_type='neutral')

    wood_level.add_block('wood', length=1280, zone_type='something')
    wood_level.add_block('wood', length=1280, zone_type='something')

    # Create events for the blocks. You can reference another level with the
    # '.' notation. (<level_name>.<block_name>). If no level is specified,
    # the block will looked up from the current level. See below...
    main_level.add_event('tp_to_heaven', 'random_teleport', ['neutral_level.neutral'])
    main_level.add_event('tp_to_somewhere_else_on_this_level', 'random_teleport', ['neutral', 'aversive'])

    neutral_level.add_event('anywhere_but_here', 'random_teleport', ['main_level.aversive', 'main_level.neutral', 'wood_level.something'])

    wood_level.add_event('tp_to_main', 'random_teleport', ['main_level.neutral'])

    # SEE OLD EXAMPLE FOR OTHER EVENTS

    # # RULES
    main_level.add_rule('zone', 'tp_to_heaven', 'aversive', 10)
    main_level.add_rule('zone', 'tp_to_somewhere_else_on_this_level', 'neutral', 10)

    neutral_level.add_rule('zone', 'anywhere_but_here', 'neutral', 3)

    wood_level.add_rule('zone', 'tp_to_main', 'something', 5)

    # Start the program. From now on you don't launch the level, but the
    # collection of levels. You can specify the starting level.
    # collection.show_image()
    collection.play(starting_level='main_level',
                    left_monitor=1,
                    right_monitor=None,
                    vel_ratio=2 * 1280,
                    fullscreen=False,
                    skip_save=True)
