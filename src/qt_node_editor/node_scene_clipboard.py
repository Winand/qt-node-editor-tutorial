import logging
from typing import TYPE_CHECKING, cast

from qt_node_editor.node_graphics_edge import QDMGraphicsEdge
from qt_node_editor.node_graphics_node import QDMGraphicsNode

if TYPE_CHECKING:
    from qt_node_editor.node_edge import Edge, EdgeSerialize
    from qt_node_editor.node_graphics_view import QDMGraphicsView
    from qt_node_editor.node_node import NodeSerialize
    from qt_node_editor.node_scene import Scene
    from qt_node_editor.node_socket import Socket

log = logging.getLogger(__name__)


class SceneClipboard:
    def __init__(self, scene: "Scene") -> None:
        self.scene = scene

    def serialize_selected(self, delete=False):
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

        data = {
            'nodes': sel_nodes,
            'edges': edges_final
        }
        if delete:
            view = cast('QDMGraphicsView', self.scene.gr_scene.views()[0])
            view.delete_selected()
        return data
    
    def deserialize_from_clipboard(self, data):
        print(f"deseralizing from clipboard, {data=}")
