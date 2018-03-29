''' Contains the Zone object '''


class Zone(object):
    ''' Correlates with beginning and end of Frames to add functionality '''
    zone_id = 0

    def __init__(self, begin, end, zone_type='generic'):
        Zone.zone_id += 1

        self.zone_id = Zone.zone_id
        self.begin = begin
        self.end = end
        self.zone_type = zone_type

    def __str__(self):
        return "Zone  #" + str(self.zone_id).ljust(2) + " - Range: [" + str(self.begin) + "," + str(self.end) + "] - Type: " + str(self.zone_type)

    def check(self, pos):
        ''' Returns True if the given position is in the zone '''
        return self.begin <= pos <= self.end
