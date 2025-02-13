from .reload_addon import VIEW3D_PT_reload_addon
from ..libs.blender_utils import register_classes, unregister_classes
from .shape_key_selector import VIEW3D_PT_shape_key_selector

classes = (
  VIEW3D_PT_reload_addon,
  VIEW3D_PT_shape_key_selector,
)

def register():
  register_classes(classes)

def unregister():
  unregister_classes(classes)
