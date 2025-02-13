from ..libs.blender_utils import register_classes, unregister_classes, add_scene_custom_prop
from ..libs.blender_utils import add_scene_custom_prop
from .categories import Categories 

classes = (Categories, )

def register():
  register_classes(classes)
  add_scene_custom_prop('categories', 'Collection', type = Categories)
  add_scene_custom_prop('overwrite', 'Bool', False, '')
  add_scene_custom_prop('shape_key_name', 'String', 'Key')
  add_scene_custom_prop('mesh_name', 'String', '纳西妲_mesh')

def unregister():
  unregister_classes(classes)
