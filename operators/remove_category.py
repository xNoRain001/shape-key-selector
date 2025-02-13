from ..libs.blender_utils import get_operator, get_props

class OBJECT_OT_remove_category (get_operator()):
  bl_idname = "object.remove_category"
  bl_label = "Remove Category"
  index: get_props().IntProperty()

  def execute(self, context):
    context.scene.categories.remove(self.index)
    return {'FINISHED'}
  