from ..libs.blender_utils import get_operator

class OBJECT_OT_init_category (get_operator()):
  bl_idname = "object.init_category"
  bl_label = "Init Category"

  def execute(self, context):
    list = ['phoneme', 'mouth', 'eyebrow', 'eye']
    
    for item in list:
      r = context.scene.categories.add()
      r.name = item
    
    return {'FINISHED'}
  