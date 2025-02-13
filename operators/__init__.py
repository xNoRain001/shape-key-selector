from .reload_addon import OBJECT_OT_reload_addon
from .init_shape_key_selector import OBJECT_OT_shape_key_selector
from ..libs.blender_utils import register_classes, unregister_classes
from .click_mode import OBJECT_OT_click_mode
from .add_category import OBJECT_OT_add_category
from .init_category import OBJECT_OT_init_category
from .remove_category import OBJECT_OT_remove_category
from .dichotomy import OBJECT_OT_dichotomy
from .select import OBJECT_OT_select

classes = (
  OBJECT_OT_reload_addon,
  OBJECT_OT_shape_key_selector,
  OBJECT_OT_click_mode,
  OBJECT_OT_add_category,
  OBJECT_OT_init_category,
  OBJECT_OT_remove_category,
  OBJECT_OT_dichotomy,
  OBJECT_OT_select
)

def register():
  register_classes(classes)

def unregister():
  unregister_classes(classes)
