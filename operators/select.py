from ..libs.blender_utils import get_operator, get_props

class OBJECT_OT_select (get_operator()):
  bl_idname = "object.select"
  bl_label = "Select"
  index: get_props().IntProperty()

  def execute(self, context):
    return {'FINISHED'}
  