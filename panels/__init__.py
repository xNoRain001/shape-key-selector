from .reload_addon import Reload_Addon
from ..libs.blender_utils import register_classes, unregister_classes
from .shape_key_selector import InitPropertyOperator, Shape_Key_Selector, MyPropertyGroup, AddPropertyOperator, RemovePropertyOperator
from ..libs.blender_utils import add_scene_custom_prop

classes = (
  Reload_Addon,
  Shape_Key_Selector,
  MyPropertyGroup,
  AddPropertyOperator,
  RemovePropertyOperator,
  InitPropertyOperator
)

import bpy

def register():
  register_classes(classes)
  # add_scene_custom_prop('my_properties', 'Collection', type2 = MyPropertyGroup)
  bpy.types.Scene.my_properties = bpy.props.CollectionProperty(type=MyPropertyGroup)

def unregister():
  unregister_classes(classes)
