from ..libs.blender_utils import (
  register_classes, unregister_classes, add_scene_custom_prop, get_collection,
  get_context
)
from .categories import Categories 
from ..operators.init_shape_key_selector import freeze_location

classes = (Categories, )

prev = None

def on_update (self, context):
  step = self.step
  selectors = get_collection('shape_key_selectors').objects

  # freeze_location(selectors[0], 'x', step)
  # freeze_location(selectors[0], 'z', step)

  for selector in selectors:
    freeze_location(selector, 'x', step)
    freeze_location(selector, 'z', step)

def register():
  register_classes(classes)
  add_scene_custom_prop('categories', 'Collection', type = Categories)
  add_scene_custom_prop('overwrite', 'Bool', False, '')
  add_scene_custom_prop('shape_key_name', 'String', 'Key')
  add_scene_custom_prop('mesh_name', 'String', '纳西妲_mesh')
  # step = 10 表示每次值变化为 0.1
  add_scene_custom_prop('step', 'Float', 1, step = 10, min = 0.0, max = 1.0, update = on_update)

def unregister():
  unregister_classes(classes)
