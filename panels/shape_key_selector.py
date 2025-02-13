from ..libs.blender_utils import (
  get_panel, 
  add_row_with_operator,
  add_row_with_label_and_operator,
  add_row_with_label,
  add_row,
  get_property_group,
  get_props
)

from ..operators.click_mode import OBJECT_OT_click_mode
from ..operators.init_shape_key_selector import OBJECT_OT_shape_key_selector
from ..operators.init_category import OBJECT_OT_init_category
from ..operators.add_category import OBJECT_OT_add_category
from ..operators.remove_category import OBJECT_OT_remove_category
from ..operators.dichotomy import OBJECT_OT_dichotomy
from ..operators.select import OBJECT_OT_select

class VIEW3D_PT_shape_key_selector (get_panel()):
  bl_label = "Shape Key Selector"
  bl_idname = "VIEW3D_PT_shape_key_selector"
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI'
  bl_category = 'Item'

  def draw(self, context):
    layout = self.layout
    scene = context.scene
    categories = scene.categories

    add_row_with_label(layout, '形态键:', scene, "mesh_name", .5)
    add_row_with_label(layout, '形态键名称:', scene, "shape_key_name", .5)

    for index, prop in enumerate(categories):
      row = layout.row()
      row.prop(prop, 'name', text = f"类别 { index + 1 }")
      if prop.dichotomy:
        row.prop(prop, 'is_selected', text = "选中")
        # r.index = index
      else:
        r = row.operator(OBJECT_OT_dichotomy.bl_idname, text = '拆分')
        r.index = index
      r = row.operator(OBJECT_OT_remove_category.bl_idname, text = '', icon = 'X')
      r.index = index
    
    add_row_with_operator(
      layout, 
      OBJECT_OT_init_category.bl_idname, 
      text="初始化类别", 
      icon='ADD'
    )
    add_row_with_operator(
      layout, 
      OBJECT_OT_add_category.bl_idname, 
      text="添加类别", 
      icon='ADD'
    )
    add_row_with_label(layout, 'image output:', scene.render, "filepath", .5)
    add_row(layout, scene, "overwrite", text = '图片已经存在时，是否重写')
    add_row_with_operator(layout, OBJECT_OT_shape_key_selector.bl_idname, text = '初始化形态键选择器')
    add_row_with_operator(layout, OBJECT_OT_click_mode.bl_idname, text = '点击模式')
