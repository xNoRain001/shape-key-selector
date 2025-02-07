from .reload_addon import Reload_Addon
from .shape_key_selector import Shape_Key_Selector
from ..libs.blender_utils import register_classes, unregister_classes
from .click_mode import Click_Mode

classes = (
  Reload_Addon,
  Shape_Key_Selector,
  Click_Mode
)

def register():
  register_classes(classes)

def unregister():
  unregister_classes(classes)
