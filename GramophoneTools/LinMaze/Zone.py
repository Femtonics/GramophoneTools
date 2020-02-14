""" Contains the Zone object """


class Zone(object):
    """Correlates with beginning and end of Frames to add functionality.

    :param begin: The beginning of the Zone in pixels.
    :type begin: int

    :param end: The end of the Zone in pixels.
    :type end: int

    :param zone_type: The type of the Zone for Rules. 'generic' by default.
    :type zone_type: str
    """

    zone_id = 0

    def __init__(self, begin, end, zone_type='generic'):
        Zone.zone_id += 1

        self.zone_id = Zone.zone_id
        self.offset = begin
        self.length = end
        self.zone_type = zone_type

    def __repr__(self):
        return "Zone  #" + str(self.zone_id).ljust(2) \
               + " - offset: " + str(self.offset) \
               + " - length: " + str(self.length) \
               + " - type: " + str(self.zone_type)
    
    def check(self, pos):
        """Returns True if the given position is in the zone.

        :param pos: The position in pixels.
        :type pos: int

        :rtype: bool
        """

        return self.offset <= pos <= self.offset + self.length
