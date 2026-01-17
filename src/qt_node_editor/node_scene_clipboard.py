# TODO: use DI or Protocol? https://gemini.google.com/app/d3cef879926b87b8
import logging
import math
from typing import TYPE_CHECKING

from qtpy.QtCore import QPointF

from qt_node_editor.node_edge import Edge
from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode

if TYPE_CHECKING:
    from qt_node_editor.node_edge import EdgeSerialize
    from qt_node_editor.node_node import NodeSerialize
    from qt_node_editor.node_scene import Scene, SceneSerialize
    from qt_node_editor.node_serializable import SerializableMap
    from qt_node_editor.node_socket import Socket

log = logging.getLogger(__name__)


class SceneClipboard:
    "Support for cut/copy/paste actions."

    def __init__(self, scene: "Scene") -> None:
        """
        Initialize :class:`SceneClipboard`.

        :param scene: reference to a :class:`.Scene` object
        """
        self.scene = scene

    # TODO: do not delete items inside this method.
    def serialize_selected(self, *, delete: bool = False) -> "SceneSerialize":
        """
        Serialize selected items in the scene into :class:`.SceneSerialize`.

        :param delete: Delete selected part of the scene after serialization (cut)
        :return: Currently selected part of the scene serialized
        """
        log.debug("--- COPY TO CLIPBOARD ---")
        sel_nodes: list[NodeSerialize] = []
        sel_edges: list[Edge] = []
        sel_sockets: dict[int, Socket] = {}

        for item in self.scene.gr_scene.selectedItems():
            if isinstance(item, QDMGraphicsNode):
                sel_nodes.append(item.node.serialize())
                for socket in (item.node.inputs + item.node.outputs):
                    sel_sockets[socket.id] = socket
            elif isinstance(item, QDMGraphicsEdge):
                sel_edges.append(item.edge)

        log.debug("  NODES\n%s", sel_nodes)
        log.debug("  EDGES\n%s", sel_edges)
        log.debug("  SOCKETS\n%s", sel_sockets)

        edges_to_remove = []
        for edge in sel_edges:
            if edge.start_socket.id not in sel_sockets \
                    or edge.end_socket.id not in sel_sockets:
                log.debug("edge %s is not connected with both sides", edge)
                edges_to_remove.append(edge)
        for edge in edges_to_remove:
            sel_edges.remove(edge)
        edges_final: list[EdgeSerialize] = []
        for edge in sel_edges:
            edges_final.append(edge.serialize())

        data: SceneSerialize = {
            'nodes': sel_nodes,
            'edges': edges_final,
        }
        if delete:  # delete on cut action
            self.scene.get_view().delete_selected()
            self.scene.history.store_history("Cut out elements from scene",
                                             modified=True)
        return data

    def deserialize_from_clipboard(self, data: "SceneSerialize") -> None:
        """
        Deserialize data from the clipboard.

        :param data: Data for deserialization into the :class:`.Scene` object
        """
        hashmap: SerializableMap = {}
        mouse_scene_pos = self.scene.get_view().last_scene_mouse_position
        # see comment https://www.youtube.com/watch?v=PdqCogmBeXI&lc=UgwvzoSf2dfez6JDf4R4AaABAg
        # TODO: graphical node width should be taken into account too
        minx = miny = math.inf
        maxx = maxy = -math.inf
        for node_data in data["nodes"]:
            x, y = node_data["pos_x"], node_data["pos_y"]
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
        bbox_center_x = (minx + maxx) / 2
        bbox_center_y = (miny + maxy) / 2

        # center = view.mapToScene(view.rect().center())

        # calculate the offset of the newly created nodes
        offset = QPointF(mouse_scene_pos.x() - bbox_center_x,
                         mouse_scene_pos.y() - bbox_center_y)

        for node_data in data["nodes"]:
            new_node = self.scene.get_node_type(node_data)(self.scene)
            new_node.deserialize(node_data, hashmap, restore_id=False)
            # new_node.gr_node.setSelected(True)  # @Winand: deselect prev. sel. first

            # readjust the new node's position
            new_node.set_pos(new_node.pos + offset)

        for edge_data in data["edges"]:
            new_edge = Edge(self.scene)
            new_edge.deserialize(edge_data, hashmap, restore_id=False)

        self.scene.history.store_history("Pasted elements into the scene",
                                         modified=True)

    def __del__(self) -> None:
        log.debug("delete clipboard helper")
