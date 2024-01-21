import math
from scipy.spatial import KDTree
import numpy as np
from rijksdriehoek import rijksdriehoek

def convert_rd_to_wgs(coords):
    coords_in_wgs=[]
    
    for lonlat in coords:
        rd = rijksdriehoek.Rijksdriehoek(lonlat[0], lonlat[1])  
        lat_wgs, lon_wgs = rd.to_wgs()
      
        coords_in_wgs.append((lon_wgs, lat_wgs))
    
    return coords_in_wgs
    
def dist_complicated(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return 1000 * km

def convert_to_m (coords):
    coords_in_m = []

    for lonlat in coords:
        lon_rad, lat_rad = map(math.radians, [lonlat[0], lonlat[1]])
      
        x_in_m = 1000 * 6371 * math.cos(lat_rad) * lon_rad
        y_in_m = 1000 * 6371 * lat_rad
 
        coords_in_m.append((x_in_m, y_in_m))
    
    return coords_in_m

def dist_simple_sq(lat1, lon1, lat2, lon2):
    # approximate squared distance
    # exact formula in function dist_complicated
    # simplify: a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    # to: dlat**2 + cos(lat_Utrecht)**2*dlon**2 = dlat**2 + cos(52 degrees)**2*dlon**2
    # = 0.38*dlon**2 + dlat**2
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    return 0.38*dlon**2 + dlat**2

def find_matching_point(node_ext, nodes_osm):
    closest_node = None
    best_dist_sq = math.inf
    for node in nodes_osm:
        if node.rwn_ref and node.rwn_ref != "-1" and node.rwn_ref == node_ext.rwn_ref or \
            node.rcn_ref and node.rcn_ref != "-1" and node.rcn_ref == node_ext.rcn_ref:
            dist_sq = dist_simple_sq(node.lat, node.lon, node_ext.lat, node_ext.lon)
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                closest_node = node

    if closest_node:
        actual_dist = dist_complicated(closest_node.lat, closest_node.lon, node_ext.lat, node_ext.lon)

    return closest_node

def find_matching_nodes(nodes_osm, nodes_ext):
    
    for node in nodes_osm:
        node.closest_match_dist = None
        node.closest_match_node = None

    for node in nodes_ext:
        node.closest_match_dist = None
        node.closest_match_node = None

    for node_ext in nodes_ext:
        for node in nodes_osm:

            if node.rwn_ref and node.rwn_ref != "-1" and node.rwn_ref == node_ext.rwn_ref or \
                node.rcn_ref and node.rcn_ref != "-1" and node.rcn_ref == node_ext.rcn_ref:
                dist_sq = dist_simple_sq(node.lat, node.lon, node_ext.lat, node_ext.lon)
                #dist=dist_complicated(node.lat, node.lon, node_ext.lat, node_ext.lon)
                #dist_sq=dist

                if node_ext.closest_match_dist != None:
                    if dist_sq < node_ext.closest_match_dist:
                        node_ext.closest_match_dist = dist_sq
                        node_ext.closest_match_node = node
                else:
                    node_ext.closest_match_dist = dist_sq
                    node_ext.closest_match_node = node
                    
                if node.closest_match_dist != None:
                    if dist_sq < node.closest_match_dist:
                        node.closest_match_dist = dist_sq
                        node.closest_match_node = node_ext
                else:
                    node.closest_match_dist = dist_sq
                    node.closest_match_node = node_ext

    for node in nodes_osm:
        if node.closest_match_node:
            best_match=node.closest_match_node
            node.closest_match_dist = dist_complicated(best_match.lat, best_match.lon, node.lat, node.lon)

    for node in nodes_ext:
        if node.closest_match_node:
            best_match=node.closest_match_node
            node.closest_match_dist = dist_complicated(best_match.lat, best_match.lon, node.lat, node.lon)


# Returns the closest node from the given node
def find_closest_node(node, comparison_nodes):
    closest_node = None
    best_dist_sq = math.inf
    for n in comparison_nodes:
        dist_sq = dist_simple_sq(node.lat, node.lon, n.lat, n.lon)
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            closest_node = n

    return closest_node

def find_closest_node_using_tree(node, comparison_nodes, comparison_tree):
    dd, ii = comparison_tree.query([[node.lon_in_m, node.lat_in_m]], k=1)
    
    closest_node = comparison_nodes[ii[0]]

    return closest_node

def create_tree(nodes):
        n = len(nodes)
        #print(n)
        xy_points=np.zeros((n,2))
        i=0
        for node in nodes:
            i=i+1
            xy_points[i-1][0]=node.lon_in_m 
            xy_points[i-1][1]=node.lat_in_m
        tree = KDTree(xy_points)
        return tree

def find_matching_nodes_using_tree(nodes_osm, nodes_ext, tree_osm, tree_ext):
        
    for node in nodes_osm:
        node.closest_match_dist = None
        node.closest_match_node = None

    for node in nodes_ext:
        node.closest_match_dist = None
        node.closest_match_node = None

    max_distance = 3000
    k_start = 10

    for node_ext in nodes_ext:

        k_val = k_start
        
        while True:
            dd, ii = tree_osm.query([[node_ext.lon_in_m, node_ext.lat_in_m]], k = k_val, distance_upper_bound=max_distance)
            if ii[0][-1] >=len(nodes_osm):
                break
            else:
                k_val=k_val*2
           
        #for node_index in np.nditer(ii):

        for node_index in ii[0]:
            #print("node_index: ")
            #print(node_index)

            if node_index>=len(nodes_osm):
                break

            node = nodes_osm[node_index]
   
            if node.rwn_ref and node.rwn_ref != "-1" and node.rwn_ref == node_ext.rwn_ref or \
                node.rcn_ref and node.rcn_ref != "-1" and node.rcn_ref == node_ext.rcn_ref:
                
                node_ext.closest_match_node = node
                node_ext.closest_match_dist = dist_complicated(node.lat, node.lon, node_ext.lat, node_ext.lon)

                break

    for node in nodes_osm:

        k_val = k_start
        
        while True:
            dd, ii = tree_ext.query([[node.lon_in_m, node.lat_in_m]], k = k_val, distance_upper_bound=max_distance)
            if ii[0][-1] >=len(nodes_ext):
                break
            else:
                k_val=k_val*2

        for node_index in ii[0]:
            if node_index>=len(nodes_ext):
                break

            node_ext = nodes_ext[node_index]

            if node.rwn_ref and node.rwn_ref != "-1" and node.rwn_ref == node_ext.rwn_ref or \
                node.rcn_ref and node.rcn_ref != "-1" and node.rcn_ref == node_ext.rcn_ref:
                
                node.closest_match_node = node_ext
                node.closest_match_dist = dist_complicated(node.lat, node.lon, node_ext.lat, node_ext.lon)

                break

