from ..libs.blender_utils import get_operator, get_props, add_scene_custom_prop

class OBJECT_OT_dichotomy (get_operator()):
  bl_idname = "object.dichotomy"
  bl_label = "Dichotomy"
  index: get_props().IntProperty()

  def execute(self, context):
    categories = context.scene.categories
    name = categories[self.index].name
    list = ['.l', '.r']
    index = self.index

    for i, item in enumerate(list):
      add_scene_custom_prop(name + item, 'Bool', False)
      r = categories.add()
      r.name = name + item
      r.is_selected = True
      r.dichotomy = True
      categories.move(len(categories) - 1, index + i)
      
    categories.remove(self.index + len(list))

    return {'FINISHED'}
  