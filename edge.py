from compare import convert_to_m

class Edge():
    def __init__(self, coords, ref_start, ref_end):
        self.coords = coords
        self.ref_start = ref_start
        self.ref_end = ref_end
        if (coords):
            self.coords_in_m = convert_to_m (coords)
        if (ref_start):
            self.ref_start = ref_start.lstrip("0")
        if (ref_end):
            self.ref_end = ref_end.lstrip("0")

        self.renamed_from = None # If the node is renamed, this has the old name (that is in OSM)
        self.change_type = None # When matched, this gives the change type

        self.matched_edge = None # Edge that has been matched to this edge by the analysis program
        self.closest_match_edge = None # Closest edge that has been matched to this edge by the analysis program
        self.closest_match_dist = None # Distance to closest_match_node

        #self.closest_dist = None # Distance to closest_node

        self.coords_in_m

    @property
    def __geo_interface__(self):
        return {"geometry": {"coordinates": (self.lat, self.lon), "type": "Point"},
                "properties": {"rwn_ref": self.rwn_ref, "rcn_ref": self.rcn_ref}, "type": "Feature"}
