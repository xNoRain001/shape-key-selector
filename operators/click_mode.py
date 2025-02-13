from collections import defaultdict

from ..const import selector_prefix, ref_image_prefix
from ..libs.blender_utils import (
  get_operator, 
  get_object_,
  update_view,
  get_active_object,
  get_layer_objects,
  get_msgbus,
  get_shape_keys,
  get_context,
  get_current_frame,
  get_ops,
  get_app,
  get_data,
  get_types_object,
  get_operator,
  active_object_
)

from ..const import selector_prefix, shape_key_empty_object

# 选择器位置发生变化时自动插入相关帧
def shape_key_insert_keyframe (shape_keys, frame):
  empty_object = get_object_(shape_key_empty_object)

  for shape_key in shape_keys:
    shape_key.value = empty_object[shape_key.name]
    shape_key.keyframe_insert(data_path="value", frame = frame)

def add_click_mode (shape_key_map, categories):
  def get_selectors (name, categories):
    selectors = []
    # shape_key_ref_eye_blink -> eye
    type = name.split('_')[3]
    prefix_or_name = selector_prefix + type
    selector = get_object_(prefix_or_name)
    types = []

    if selector:
      # 能找到，说明没有拆分
      selectors.append(selector)
      types.append(type)
    else:
      # TODO: 优化性能
      for category in categories:
        name = category.name

        if name.startswith(type + '.') and category.is_selected:
          selectors.append(get_object_(selector_prefix + name))
          types.append(name)

    return selectors, types

  def update_selectors (selectors, ref_image, types):
    # round(var) -> 1
    def update_driver (selectors, frame):
      for selector in selectors:
        selector.location[0] = ref_image.location[0]
        selector.location[2] = ref_image.location[2]
        # 会触发 depsgraph_update_handler 执行
        selector.select_set(True)
        # 不激活它，就不会执行 depsgraph_update_handler 中写的其它逻辑
        # active_object_(selector)
        selector_insert_keyframe(selector, frame)
        
        # driver = (
        #   selector.animation_data.drivers.find('location', index = i).driver
        # )
        # old_exp = driver.expression
        # driver.expression = str(o.location[i])
        # drivers.append(driver)
        # exps.append(old_exp)
    
    # 1 -> round(var)
    def restore_driver (drivers, exps):
      for index, driver in enumerate(drivers):
        driver.expression = exps[index]
          
    def update_shape_key_value (shape_key_map, types, frame):
      for item in types:
        shape_key_insert_keyframe(shape_key_map[item], frame)

    drivers = []
    exps = []
    ref_image.select_set(False)
    active_object_(None)
    # types 是开启选中的选择器

    frame = get_current_frame()
    update_driver(selectors, frame)
    # 更新视图，否则形态键插帧时的值是上一次的值
    update_view()
    update_shape_key_value(shape_key_map, types, frame)

    # 更新视图，选择器会移动到被点击的图片的位置上
    # update_view()
    # restore_driver(drivers, exps)
    drivers.clear()
    exps.clear()

  def cb():
    active_object = get_active_object()
    name = active_object.name

    if name.startswith(ref_image_prefix):
      selectors, types = get_selectors(name, categories)
      update_selectors(selectors, active_object, types)

  # 监听图片是否被点击
  def subscribe_rna():
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

def selector_insert_keyframe (selector, frame):
  selector.keyframe_insert(data_path = "location", index = 0, frame = frame) 
  selector.keyframe_insert(data_path = "location", index = 2, frame = frame) 

def update_shape_key_value (shape_keys):
  empty_object = get_object_(shape_key_empty_object)

  for shape_key in shape_keys:
    shape_key.value = empty_object[shape_key.name]

def _on_depsgraph_update (merged_category_names, shape_key_name):
  shape_keys = get_shape_keys(shape_key_name)
  shape_key_map = defaultdict(list)
  empty_object = get_object_(shape_key_empty_object)

  for category in merged_category_names:
    for shape_key in shape_keys:
      shape_key_name = shape_key.name

      if (
        shape_key_name.startswith(category + '_') and 
        shape_key_name in empty_object
      ):
        segments = shape_key_name.split('.')
        suffix = segments[1] if len(segments) > 1 else ''

        if suffix == '':
          # category 未被拆分
          shape_key_map[category].append(shape_key)
        else:
          shape_key_map[category + '.' + suffix].append(shape_key)

  def on_depsgraph_update(scene, depsgraph):
    active_object = get_active_object()
    active_operator = get_context().active_operator

    # 删除时 active_object 时值变为 None
    if not active_object or not active_object.name.startswith(selector_prefix):
      on_depsgraph_update.operator = active_operator

      return

    for update in depsgraph.updates:
      if update.is_updated_transform:
        # tip1: msgbus 监听 location 时只有点击 ui 或者代码 location[0] = 0 改变值才触发
        # tip2: 删除关键帧时 is_updated_transform 为 True，但是不会进入任务判断语句内

        # .l 和 .r 同时移动时，其中一个行为和单独移动时相同（假设是 .l），会不断进入
        # 这里，移动完成后更新 operator，之后 .r 只会更新一次，即 .l 完成移动后
        # .r 才进入这里，且只进入一次，并且此时 active_operator 就是 .l 移动完成时的 
        # operator，因此 .r 会进入移动中，所以结尾加上 break，.l 移动时完成 .l 和 .r
        # 形态键值的更新，.l 移动完成后完成 .l 和 .r 曲线编辑器的更新。
        # 所以目前只单独移动.l 或 .r 时也会更新另一半

        print(update.id)
        selector = update.id
        print(selector.name)
        segments = selector.name.split('_')[3].split('.')
        category = segments[0]
        side = '.' + segments[1] if len(segments) > 1 else ''

        if on_depsgraph_update.operator == active_operator:
          # print(f'{ active_object } 移动中...')
          print(f'{ update.id.name } 移动中...')
          update_shape_key_value(shape_key_map[category + side])
          # update_shape_key_value(shape_key_map['eye' + '.l'])
          # update_shape_key_value(shape_key_map[category + '.r'])

          return

        # 左边橙色 右边红色 active_object 全程 .l，update.id 全程 .l
        # 左边红色 右边橙色 active_object 全程 .r，update.id 全程 .l
        if active_operator.name == 'Move':
          # print(f'{ active_object } 移动完成...')
          print(f'{ update.id.name } 移动完成...')
          # frame = get_current_frame()
          # selector_insert_keyframe(selector, frame)
          # shape_key_insert_keyframe(shape_key_map[category], frame)

        on_depsgraph_update.operator = active_operator
        # on_depsgraph_update.done_op = active_operator

        break

  # 在第一次移动中，context.active_operator 为上一次操作结束后的那个值，
  # 移动结束后会有一个新值，
  # 在第二次移动中，context.active_operator 上一次移动（或其他操作）结束后给的那个值，
  # 移动结束后会有一个新值
  on_depsgraph_update.operator = get_context().active_operator

  return on_depsgraph_update, shape_key_map

from .init_shape_key_selector import merge_category_names

class OBJECT_OT_click_mode (get_operator()):
  bl_idname = "object.click_mode"
  bl_label = "Click Mode"

  def execute(self, context):
    scene = context.scene
    categories = scene.categories
    shape_key_name = scene.shape_key_name
    merged_category_names, dichotomy_category_names = merge_category_names(categories)
    cb, shape_key_map = _on_depsgraph_update(merged_category_names, shape_key_name)
    # get_app().handlers.depsgraph_update_post.append(cb)
    add_click_mode(shape_key_map, categories)

    # for key, value in shape_key_map.items():
    #   print(key + ' -----------------')
    #   for item in value:
    #     print(item)

    return {'FINISHED'}
