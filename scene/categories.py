from ..libs.blender_utils import get_property_group, get_props

# 这两个参数必须填写，否则注册失败
def on_update (self, context):
  return

class Categories (get_property_group()):
  name: get_props().StringProperty(name="name")
  is_selected: get_props().BoolProperty(name="is_selected", update=on_update)
  dichotomy: get_props().BoolProperty(name="dichotomy")
