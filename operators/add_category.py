from ..libs.blender_utils import get_operator

class OBJECT_OT_add_category (get_operator()):
  bl_idname = "object.add_category"
  bl_label = "Add Category"

  def execute(self, context):
    context.scene.categories.add()
    
    return {'FINISHED'}
  