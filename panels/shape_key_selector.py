from ..libs.blender_utils import (
  get_panel, 
  add_scene_custom_prop,
  add_row_with_operator,
  add_row_with_label_and_operator,
  add_row_with_label,
  add_row,
  get_operator,
  get_property_group
)
import bpy

class MyPropertyGroup(get_property_group()):
  name: bpy.props.StringProperty(name="my_properties")

class AddPropertyOperator(get_operator()):
  bl_idname = "scene.add_property"
  bl_label = "Add Property"

  def execute(self, context):
    context.scene.my_properties.add()
    return {'FINISHED'}
  
class InitPropertyOperator(get_operator()):
  bl_idname = "scene.init_property"
  bl_label = "Init Property"

  def execute(self, context):
    list = ['phoneme', 'mouth', 'eyebrow', 'eye']
    
    for item in list:
      r = context.scene.my_properties.add()
      r.name = item
    
    return {'FINISHED'}

class RemovePropertyOperator(get_operator()):
  bl_idname = "scene.remove_property"
  bl_label = "Remove Property"
  index: bpy.props.IntProperty()

  def execute(self, context):
    context.scene.my_properties.remove(self.index)
    return {'FINISHED'}

class Shape_Key_Selector (get_panel()):
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = "Item"
  bl_label = "Shape Key Selector"
  bl_idname = "_PT_Shape_Key_Selector_PT_"

  def draw(self, context):
    layout = self.layout
    scene = context.scene

    for index, prop in enumerate(scene.my_properties):
      remove_op = add_row_with_label_and_operator(
        layout, 
        prop, 
        "name", 
        f"类别 { index + 1 }",
        "scene.remove_property", 
        '', 
        'X'
      )
      remove_op.index = index

    add_row_with_label(layout, '形态键名称:', scene, "shape_key", .5)
    add_row_with_operator(
      layout, 
      "scene.init_property", 
      text="初始化类别", 
      icon='ADD'
    )
    add_row_with_operator(
      layout, 
      "scene.add_property", 
      text="添加类别", 
      icon='ADD'
    )
    add_row_with_label(layout, 'image output:', scene.render, "filepath", .5)
    add_row(layout, scene, "overwrite", text = '图片已经存在时，是否重写')
    add_row_with_operator(layout, "object.shape_key_selector", text = '初始化形态键选择器')
    add_row_with_operator(layout, "object.click_mode", text = '点击模式')

add_scene_custom_prop('overwrite', 'Bool', False, '')
add_scene_custom_prop('shape_key', 'String', 'Key', '')
