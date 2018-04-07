""" Test functions for the LinMaze module """

def test_imoports():
    try:
        import GramophoneTools.LinMaze.LinMaze
        import GramophoneTools.LinMaze.Level
        import GramophoneTools.LinMaze.Frame
        import GramophoneTools.LinMaze.Event
        import GramophoneTools.LinMaze.Rule
        import GramophoneTools.LinMaze.Zone
        import GramophoneTools.LinMaze.Tools
        import GramophoneTools.LinMaze.Perlin
    except Exception as err:
        print(err)
        assert False
    else:
        assert True
