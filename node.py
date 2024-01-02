from compare import convert_to_m

class Node():
    def __init__(self, lat, lon, rwn_ref, rcn_ref):
        self.lat = float(lat)
        self.lon = float(lon)
        self.rwn_ref = rwn_ref
        self.rcn_ref = rcn_ref
        if (lat):
            coords = []
            coords.append((self.lon, self.lat))
            #coords[0][0] = self.lon
            #coords[0][1] = self.lat
            coords_in_m = convert_to_m (coords)
            self.lon_in_m = coords_in_m[0][0]
            self.lat_in_m = coords_in_m[0][1]
        if (rwn_ref):
            self.rwn_ref = rwn_ref.lstrip("0")
        if (rcn_ref):
            self.rcn_ref = rcn_ref.lstrip("0")
        self.renamed_from = None # If the node is renamed, this has the old name (that is in OSM)
        self.matched_node = None # Node that has been matched to this node by the analysis program
        self.change_type = None # When matched, this gives the change type

        self.closest_match_node = None # Closest node that has been matched to this node by the analysis program
        self.closest_match_dist = None # Distance to closest_match_node

        self.closest_node = None # Closest node to this node
        self.closest_dist = None # Distance to closest_node

        self.lat_scaled = None
        self.lon_scaled = None

    @property
    def __geo_interface__(self):
        return {"geometry": {"coordinates": (self.lat, self.lon), "type": "Point"},
                "properties": {"rwn_ref": self.rwn_ref, "rcn_ref": self.rcn_ref}, "type": "Feature"}
