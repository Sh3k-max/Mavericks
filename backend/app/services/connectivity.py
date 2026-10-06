import networkx as nx
import numpy as np
from typing import List, Dict, Any, Tuple
from ..utils.logger import logger
from ..utils.geometry import euclidean_distance

class ConnectivityEngine:
    """
    Builds a topological NetworkX connectivity graph from detected components and pipeline lines:
    - Associates component ports/centers with nearest pipeline endpoints or segments.
    - Resolves multi-segment pipeline paths between components.
    - Discovers physical fluid flow paths (e.g. Pump -> Valve -> Transmitter).
    """

    def __init__(self, connection_tolerance: float = 180.0):
        self.connection_tolerance = connection_tolerance

    def build_graph(
        self,
        components: List[Dict[str, Any]],
        lines: List[Dict[str, Any]],
        sheet_id: str
    ) -> Dict[str, Any]:
        logger.info(f"Building connectivity graph for sheet {sheet_id}")

        G = nx.Graph()

        # 1. Add Component nodes
        for comp in components:
            c_id = comp["id"]
            cx = comp["center_x"]
            cy = comp["center_y"]
            tag = comp.get("tag", "UNTAGGED")
            c_type = comp.get("component_type", "Unknown")

            G.add_node(
                c_id,
                node_type="component",
                tag=tag,
                component_type=c_type,
                x=cx,
                y=cy,
                data=comp
            )

        # 2. Build line graph
        line_graph = nx.Graph()

        # Add line endpoints as nodes and line segments as edges
        for idx, line in enumerate(lines):
            p1 = (round(line["start"][0], 1), round(line["start"][1], 1))
            p2 = (round(line["end"][0], 1), round(line["end"][1], 1))
            line_graph.add_edge(p1, p2, line_idx=idx, length=line.get("length", 10.0))

        # Connect line endpoints that are near each other (junctions/elbows/tees, up to 35px at 2x scale)
        nodes = list(line_graph.nodes())
        for i in range(len(nodes)):
            for j in range(i + 1, min(len(nodes), i + 40)):
                n1 = nodes[i]
                n2 = nodes[j]
                d = euclidean_distance(n1, n2)
                if d <= 35.0:
                    line_graph.add_edge(n1, n2, line_idx=-1, length=d)

        # Link each component to its nearest line node or line segment
        comp_to_line_node = {}
        for comp in components:
            c_id = comp["id"]
            c_pos = (comp["center_x"], comp["center_y"])
            best_node = None
            min_dist = float("inf")

            # Check existing line endpoints
            for node in line_graph.nodes():
                d = euclidean_distance(c_pos, node)
                if d < min_dist and d <= self.connection_tolerance:
                    min_dist = d
                    best_node = node

            # If no endpoint is close enough, check distance to line segments
            if best_node is None:
                for line in lines:
                    ls = line["start"]
                    le = line["end"]
                    d_seg = self._point_to_segment_distance(c_pos[0], c_pos[1], ls[0], ls[1], le[0], le[1])
                    if d_seg < min_dist and d_seg <= self.connection_tolerance:
                        min_dist = d_seg
                        # Use nearest endpoint of that line
                        d_s = euclidean_distance(c_pos, ls)
                        d_e = euclidean_distance(c_pos, le)
                        best_node = (round(ls[0], 1), round(ls[1], 1)) if d_s < d_e else (round(le[0], 1), round(le[1], 1))

            if best_node is not None:
                comp_to_line_node[c_id] = (best_node, min_dist)

        # 3. Find paths between component pairs through the line graph
        connections = []
        comp_list = list(components)

        for i in range(len(comp_list)):
            for j in range(i + 1, len(comp_list)):
                c1 = comp_list[i]
                c2 = comp_list[j]
                c1_id = c1["id"]
                c2_id = c2["id"]

                direct_dist = euclidean_distance(
                    (c1["center_x"], c1["center_y"]),
                    (c2["center_x"], c2["center_y"])
                )

                connected = False
                path_coords = []

                if c1_id in comp_to_line_node and c2_id in comp_to_line_node:
                    n1, _ = comp_to_line_node[c1_id]
                    n2, _ = comp_to_line_node[c2_id]
                    if n1 == n2:
                        connected = True
                        path_coords = [
                            [c1["center_x"], c1["center_y"]],
                            [n1[0], n1[1]],
                            [c2["center_x"], c2["center_y"]]
                        ]
                    elif nx.has_path(line_graph, n1, n2):
                        shortest_path = nx.shortest_path(line_graph, n1, n2)
                        path_len = len(shortest_path)
                        if path_len <= 25:
                            connected = True
                            path_coords = [
                                [c1["center_x"], c1["center_y"]],
                                *[[p[0], p[1]] for p in shortest_path],
                                [c2["center_x"], c2["center_y"]]
                            ]

                # Fallback: if two components are collinearly aligned and close
                if not connected and direct_dist <= 300.0:
                    mid_x = (c1["center_x"] + c2["center_x"]) / 2.0
                    mid_y = (c1["center_y"] + c2["center_y"]) / 2.0
                    for l in lines:
                        ls = l["start"]
                        le = l["end"]
                        d_mid_line = self._point_to_segment_distance(mid_x, mid_y, ls[0], ls[1], le[0], le[1])
                        if d_mid_line <= 45.0:
                            connected = True
                            path_coords = [
                                [c1["center_x"], c1["center_y"]],
                                [mid_x, mid_y],
                                [c2["center_x"], c2["center_y"]]
                            ]
                            break

                if connected:
                    G.add_edge(c1_id, c2_id, weight=direct_dist)
                    connections.append({
                        "sheet_id": sheet_id,
                        "source_component_id": c1_id,
                        "target_component_id": c2_id,
                        "source_tag": c1.get("tag", ""),
                        "target_tag": c2.get("tag", ""),
                        "line_label": f"LINE-{c1.get('tag', '')}->{c2.get('tag', '')}",
                        "line_type": "primary_pipeline",
                        "start_x": float(c1["center_x"]),
                        "start_y": float(c1["center_y"]),
                        "end_x": float(c2["center_x"]),
                        "end_y": float(c2["center_y"]),
                        "path_points": path_coords,
                        "confidence": 0.92
                    })

        logger.info(f"Connectivity engine identified {len(connections)} connected component pairs")
        return {
            "graph": G,
            "connections": connections,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges()
        }

    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2) -> float:
        l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if l2 == 0:
            return euclidean_distance((px, py), (x1, y1))
        t = max(0.0, min(1.0, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return euclidean_distance((px, py), (proj_x, proj_y))
