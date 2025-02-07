from ..const import selector_prefix, ref_image_prefix
from ..libs.blender_utils import (
  get_operator, 
  get_object_,
  update_view,
  get_active_object,
  get_layer_objects,
  get_msgbus
)

def add_click_mode ():
  def get_selectors (name):
    selectors = []
    # shape_key_ref_eye_blink -> eye
    type = name.split('_')[3]
    prefix_or_name = selector_prefix + type
    selector = get_object_(prefix_or_name)

    if selector:
      # 能找到，说明没有拆分
      selectors.append(selector)
    else:
      selectors.extend([
        get_object_(prefix_or_name + '.l'), 
        get_object_(prefix_or_name + '.r')
      ])

    return selectors
  
  # map = {}
  # get_object_(selector_prefix + type + '.l')
  
  # TODO: 建立选择器和驱动器，表达式的映射表
  def update_selectors (selectors, o):
    # round(var) -> 1
    def update_driver (selectors):
      for selector in selectors:
        for i in indexs:
          driver = (
            selector.animation_data.drivers.find('location', index = i).driver
          )
          old_exp = driver.expression
          driver.expression = str(o.location[i])
          drivers.append(driver)
          exps.append(old_exp)
    
    # 1 -> round(var)
    def restore_driver (drivers, exps):
      for index, driver in enumerate(drivers):
        driver.expression = exps[index]

    indexs = [0, 2]
    drivers = []
    exps = []

    update_driver(selectors)
    # 更新视图，选择器会移动到被点击的图片的位置上
    update_view()
    restore_driver(drivers, exps)
    drivers.clear()
    exps.clear()

  def cb():
    o = get_active_object()
    name = o.name

    if name.startswith(ref_image_prefix):
      selectors = get_selectors(name)
      update_selectors(selectors, o)

  def subscribe_rna():
    print('sub')
    # 只监听具体的对象，但是它们没有 active 属性，select 属性 4.0 开始被废弃。
    # subscribe_to = o.path_resolve("select")
    # 监听所有对象，回调中再进行筛选
    subscribe_to = (get_layer_objects(), "active")

    get_msgbus().subscribe_rna(
      key = subscribe_to,
      owner = object(),
      args = (),
      notify = cb,
    )

  # 自动执行，但是切换文件时，内存中 flag 没有释放，必须重启 blender
  # global flag
  # if not flag:
  #   flag = True
  #   subscribe_rna()

  subscribe_rna()

# flag = False

class Click_Mode (get_operator()):
  bl_idname = "object.click_mode"
  bl_label = "Click Mode"

  def execute(self, context):
    add_click_mode()

    return {'FINISHED'}
