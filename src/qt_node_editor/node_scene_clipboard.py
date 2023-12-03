from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qt_node_editor.node_scene import Scene


class SceneClipboard:
    def __init__(self, scene: "Scene") -> None:
        self.scene = scene

    def serialize_selected(self, delete=False):
        return {}
    
    def deserialize_from_clipboard(self, data):
        print(f"deseralizing from clipboard, {data=}")
