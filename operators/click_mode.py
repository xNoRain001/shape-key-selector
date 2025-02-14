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
  active_object_,
  get_selected_objects,
  set_current_frame
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
    def update_driver (selectors, frame):
      for selector in selectors:
        selector.location[0] = ref_image.location[0]
        selector.location[2] = ref_image.location[2]
        # 会触发 depsgraph_update_handler 执行
        selector.select_set(True)
        # 不激活它，active_object 就会为 None，
        # 就不会执行 depsgraph_update_handler 中写的其它逻辑
        active_object_(selector)
        selector_insert_keyframe(selector, frame)
          
    def update_shape_key_value (shape_key_map, types, frame):
      for item in types:
        shape_key_insert_keyframe(shape_key_map[item], frame)

    ref_image.select_set(False)
    active_object_(None)
    frame = get_current_frame()
    update_driver(selectors, frame)
    # 更新视图，选择器会移动到被点击的图片的位置上，形态键的值就是最新的了
    # 否则形态键插帧时的值是上一次的值，要等函数执行完，视图更新后，值才会更新
    update_view()
    # types 是开启选中的选择器
    update_shape_key_value(shape_key_map, types, frame)

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
  list = [0, 2]

  for index in list:
    selector.keyframe_insert(data_path = "location", index = index, frame = frame) 
    fcurve = selector.animation_data.action.fcurves.find("location", index = index)
    keyframe_point = [kp for kp in fcurve.keyframe_points if kp.co[0] == frame][0]
    keyframe_point.interpolation = 'CONSTANT'

def update_shape_key_value (shape_keys):
  empty_object = get_object_(shape_key_empty_object)

  for shape_key in shape_keys:
    shape_key.value = empty_object[shape_key.name]

def shape_key_update_keyframe (selector, shape_keys, current_frame, mesh):
  fcurves = mesh.data.shape_keys.animation_data.action.fcurves

  for shape_key in shape_keys:
    data_path = f'key_blocks["{ shape_key.name }"].value'
    fcurves.remove(fcurves.find(data_path))
  
  action = selector.animation_data.action

  # 所有帧都被删除时值为 None
  if action:
    keyframe_points = selector.animation_data.action.fcurves.find("location", index = 0).keyframe_points
    
    for keyframe_point in keyframe_points:
      frame = int(keyframe_point.co[0])
      set_current_frame(frame)
      update_shape_key_value(shape_keys)
      shape_key_insert_keyframe(shape_keys, frame)

  set_current_frame(current_frame)

  # fcurves = mesh.data.shape_keys.animation_data.action.fcurves

  # for shape_key in shape_keys:
  #   data_path = f'key_blocks["{ shape_key.name }"].value'
  #   keyframe_points = fcurves.find(data_path).keyframe_points
  #   keyframe_point = [kp for kp in keyframe_points if kp.co[0] == frame][0]
  #   keyframe_points.remove(keyframe_point)

def _on_depsgraph_update (merged_category_names, shape_key_name, mesh):
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

    # 删除时， active_object 时值变为 None
    if not active_object or not active_object.name.startswith(selector_prefix):
      on_depsgraph_update.operator = active_operator

      return
    
    # 点击 selector 时会进入这里，但是 is_updated_transform 值为 False

    for update in depsgraph.updates:
      if update.is_updated_transform:
        # 左边橙色 右边红色 active_object 全程 .l，update.id 全程 .l
        # 左边红色 右边橙色 active_object 全程 .r，update.id 全程 .l
        # 可能为 mesh
        selector = update.id
        selectors = get_selected_objects()
        segments = selectors[0].name.split('_')[3].split('.')
        category = segments[0]
        side = '.' + segments[1] if len(segments) > 1 else ''
        # 全程 .l
        x, _, z = selectors[0].location
        skip = on_depsgraph_update.prev_x == x and on_depsgraph_update.prev_z == z

        if on_depsgraph_update.operator == active_operator:
          if skip:
            # print('假移动')
            return
          else:
            # print(f'{ update.id.name } 移动中...')
            on_depsgraph_update.prev_x = x
            on_depsgraph_update.prev_z = z

            if len(selectors) > 1:
              # .l 和 .r
              mirror_side = '.l' if side == '.r' else '.r'
              update_shape_key_value(shape_key_map[category + side])
              update_shape_key_value(shape_key_map[category + mirror_side])
            else:
              update_shape_key_value(shape_key_map[category + side])
        
            return
          
        op_name = active_operator.name
        print(op_name)
        frame = get_current_frame()

        
        # TODO: 帧移动，缩放，复制，删除
        if (
          op_name == 'Delete Keyframes' or
          op_name == 'Transform' or
          op_name == 'Duplicate'
        ):
          if len(selectors) > 1:
            mirror_side = '.l' if side == '.r' else '.l'
            shape_key_update_keyframe(selectors[0], shape_key_map[category + side], frame, mesh)
            shape_key_update_keyframe(selectors[1], shape_key_map[category + mirror_side], frame, mesh)
          else:
            shape_key_update_keyframe(selectors[0], shape_key_map[category + side], frame, mesh)

        if active_operator.name == 'Move':
          # 无法判断，存在移动完成后继续移动，
          # if skip:
          #   print(f'{ update.id.name } 假移动完成...')
          # else:
          # print(f'{ active_object } 移动完成...')


          # print(f'{ update.id.name } 移动完成...')
          if len(selectors) > 1:
            # .l 和 .r
            mirror_side = '.l' if side == '.r' else '.r'
            for s in selectors:
              selector_insert_keyframe(s, frame)
            shape_key_insert_keyframe(shape_key_map[category + side], frame)
            shape_key_insert_keyframe(shape_key_map[category + mirror_side], frame)
          else:
            selector_insert_keyframe(selectors[0], frame)
            # print(selector)
            # print(category + side)
            # print(selectors == selector)
            # <bpy_struct, Object("shape_key_selector_eyebrow.r") at 0x000002C22A7D2420>
            # print(selectors[0])
            # <bpy_struct, Object("shape_key_selector_eyebrow.r") at 0x000002C22C7D3908, evaluated>
            # print(selector)
            shape_key_insert_keyframe(shape_key_map[category + side], frame)
          
        on_depsgraph_update.operator = active_operator

        break

  # 在第一次移动中，context.active_operator 为上一次操作结束后的那个值，
  # 移动结束后会有一个新值，
  # 在第二次移动中，context.active_operator 上一次移动（或其他操作）结束后给的那个值，
  # 移动结束后会有一个新值
  on_depsgraph_update.operator = get_context().active_operator
  on_depsgraph_update.prev_x = None
  on_depsgraph_update.prev_z = None

  return on_depsgraph_update, shape_key_map

from .init_shape_key_selector import merge_category_names

class OBJECT_OT_click_mode (get_operator()):
  bl_idname = "object.click_mode"
  bl_label = "Click Mode"

  def execute(self, context):
    scene = context.scene
    categories = scene.categories
    shape_key_name = scene.shape_key_name
    mesh_name = scene.mesh_name
    mesh = get_object_(mesh_name)
    merged_category_names, dichotomy_category_names = merge_category_names(categories)
    cb, shape_key_map = _on_depsgraph_update(merged_category_names, shape_key_name, mesh)
    get_app().handlers.depsgraph_update_post.append(cb)
    add_click_mode(shape_key_map, categories)

    # for key, value in shape_key_map.items():
    #   print(key + ' -----------------')
    #   for item in value:
    #     print(item)

    return {'FINISHED'}
