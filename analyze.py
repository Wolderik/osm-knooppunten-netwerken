import math
from enum import Enum
from compare import find_closest_node, dist_complicated
from import_osm import import_osm
from import_geojson import import_geojson, export_geojson
from compare import find_matching_point, dist_complicated, find_closest_node
from osm_knooppunten.helper import is_small_rename
from _version import __version__

class ChangeType(Enum):
    # No significant change
    NO = 1

    # Exists in OSM dataset, but does not exist in import dataset and is not renamed
    REMOVED = 2

    # Does not exist in OSM dataset, but does exist in import dataset and is not renamed
    ADDED = 3

    # Close to node in other dataset with a different name. The other node
    # doesn't have a matching node either. Minor renames are classified as RENAMED_MINOR
    RENAMED = 4

    # Matches with a node in the other dataset with distance 1-100m
    MOVED_SHORT = 5

    # Matches with a node in the other dataset with distance 100-1000m
    MOVED_LONG = 6

    # None of the others
    OTHER = 7

    # Same as renamed, but used for minor renames. This is used when the
    # difference is just a couple of letters. When it's a different number,
    # it's classified as a normal rename.
    RENAMED_MINOR = 8

    def __str__(self):
        if self == ChangeType.NO:
            return "No change"

        if self == ChangeType.REMOVED:
            return "Removed"

        if self == ChangeType.ADDED:
            return "Added"

        if self == ChangeType.RENAMED:
            return "Renamed"

        if self == ChangeType.RENAMED_MINOR:
            return "Minor rename"

        if self == ChangeType.MOVED_SHORT:
            return "Moved short distance"

        if self == ChangeType.MOVED_LONG:
            return "Moved long distance"

        if self == ChangeType.OTHER:
            return "Other"

        return "Unknown enum value: {}".format(self.value)

def get_node_change_type_ext(node_ext, nodes_osm, nodes_ext):
    all_matching_nodes = node_ext.matching_nodes
    all_matching_nodes.extend(node_ext.bad_matching_nodes)

    closest_match = find_closest_node(node_ext, all_matching_nodes)
    if (closest_match):
        closest_match_dist = dist_complicated(closest_match.lat, closest_match.lon, node_ext.lat, node_ext.lon)
    else:
        closest_match_dist = math.inf

    closest_node = find_closest_node(node_ext, nodes_osm)
    if closest_node:
        closest_node_dist = dist_complicated(closest_node.lat, closest_node.lon, node_ext.lat, node_ext.lon)
    else:
        closest_node_dist = math.inf

    # TODO: Should find next closest node if closest node has a match
    if closest_match_dist > 1000 and closest_node_dist < 10 and len(closest_node.matching_nodes) == 0:
        node_ext.renamed_from = closest_node.rwn_ref
        if is_small_rename(node_ext.rwn_ref, closest_node.rwn_ref):
            return ChangeType.RENAMED_MINOR, closest_node
        else:
            return ChangeType.RENAMED, closest_node

    if not all_matching_nodes or len(all_matching_nodes) == 0:
        return ChangeType.ADDED, None

    if closest_match_dist > 1000:
        return ChangeType.ADDED, None

    if closest_match_dist > 1 and closest_match_dist < 100:
        return ChangeType.MOVED_SHORT, closest_match

    if closest_match_dist > 100 and closest_match_dist < 1000:
        return ChangeType.MOVED_LONG, closest_match

    if closest_match_dist < 1:
        return ChangeType.NO, closest_match

    return ChangeType.OTHER, None

def is_node_removed_osm(node_osm, nodes_osm, nodes_ext):
    all_matching_nodes = node_osm.matching_nodes
    all_matching_nodes.extend(node_osm.bad_matching_nodes)

    closest_match = find_closest_node(node_osm, all_matching_nodes)
    if (closest_match):
        closest_match_dist = dist_complicated(closest_match.lat, closest_match.lon, node_osm.lat, node_osm.lon)
    else:
        closest_match_dist = math.inf

    if not all_matching_nodes or len(all_matching_nodes) == 0 or closest_match_dist > 1000:
        return True

def do_analysis_internal(nodes_osm, nodes_ext, nodes_ext_invalid, progress):
    i = 0
    for node in nodes_ext:
        best_match = find_matching_point(node, nodes_osm)
        if best_match:
            dist = dist_complicated(best_match.lat, best_match.lon, node.lat, node.lon)
            if dist < 100:
                best_match.matching_nodes.append(node)
                node.matching_nodes.append(best_match)
            else:
                best_match.bad_matching_nodes.append(node)
                node.bad_matching_nodes.append(best_match)
        i = i + 1
        progress.emit("Pre-processing nodes {}/{}".format(i, len(nodes_ext)))

    node_changes_dict = dict()
    for key in ChangeType:
        node_changes_dict[key] = []

    i = 0;
    for node in nodes_ext:
        # print("Node", i)
        change_type, matched_node = get_node_change_type_ext(node, nodes_osm, nodes_ext)
        if matched_node and matched_node.matched_node:
            # The matched node was already matched to some other node
            # TODO give better warning here
            print("ERROR: Node was matched twice")

        node.change_type = change_type
        if matched_node:
            matched_node.matched_node = node
            matched_node.change_type = change_type
            node.matched_node = matched_node

        node_changes_dict[change_type].append(node)
        i += 1
        progress.emit("Analyzing nodes {}/{}".format(i, len(nodes_ext)))

    for node in nodes_osm:
        if not node.matched_node and is_node_removed_osm(node, nodes_osm, nodes_ext):
            node.change_type = ChangeType.REMOVED
            node_changes_dict[ChangeType.REMOVED].append(node)


    for key in node_changes_dict:
        print("{}: {}".format(key, len(node_changes_dict[key])))

    progress.emit("Exporting results")
    export_geojson(nodes_ext_invalid, "invalid_nodes_ext.geojson")

    exported_files = []
    for key in ChangeType:
        if key == ChangeType.REMOVED:
            export_file = export_geojson(node_changes_dict[key], "{}_osm.geojson".format(key))
        else:
            export_file = export_geojson(node_changes_dict[key], "{}_ext.geojson".format(key))
        exported_files.append(export_file)
    progress.emit("Done")
    return exported_files

def do_analysis(osmfile, importfilename, filter_region, filter_province, progress):
    progress.emit("Importing data")
    nodes_osm = import_osm(osmfile)
    nodes_ext, nodes_ext_invalid = import_geojson(importfilename, rwn_name="knooppuntnummer", filter_regio=filter_region, filter_province=filter_province)

    print("OSM dataset:", osmfile.name, "({} nodes)".format(len(nodes_osm)))

    if (filter_region):
        print("External dataset: {}, filtered by region '{}' ({} nodes)".format(importfilename, filter_region, len(nodes_ext)))
    else:
        print("External dataset:", importfilename, "({} nodes)".format(len(nodes_ext)))
    print()

    return do_analysis_internal(nodes_osm, nodes_ext, nodes_ext_invalid, progress)

