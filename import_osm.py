import xml.sax
from xml import sax
from node import Node

class OSMContentHandler(xml.sax.ContentHandler):
    def __init__(self, nodes):
        xml.sax.ContentHandler.__init__(self)
        self.rwn_ref = None
        self.rcn_ref = None
        self.lat = None
        self.lon = None
        self.nodes = nodes

    def startElement(self, name, attrs):
        if name == "node":
            # reset ref numbers
            self.rwn_ref = None
            self.rcn_ref = None

            # pares latitude and longtitude
            self.lat = attrs["lat"]
            self.lon = attrs["lon"]

        if name == "tag":
            key = attrs["k"]
            value = attrs["v"]
            if key == "rwn_ref":
                self.rwn_ref = value
            if key == "rcn_ref":
                self.rcn_ref = value

    def endElement(self, name):
        if name == "node":
            self.nodes.append(Node(lat=self.lat, lon=self.lon, rwn_ref=self.rwn_ref, rcn_ref=self.rcn_ref))

def import_osm(filename_or_stream):
    nodes = []
    xml.sax.parse(filename_or_stream, OSMContentHandler(nodes))
    return nodes
