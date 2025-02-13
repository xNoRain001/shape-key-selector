import os
import json
from collections import defaultdict

from ..const import selector_prefix, ref_image_prefix, shape_key_empty_object
from ..libs.blender_utils import (
  get_context, 
  get_ops, 
  get_object, 
  create_collection,
  get_active_object,
  snap_cursor,
  set_mode,
  get_operator,
  copy_bone,
  get_material,
  create_material,
  get_data,
  get_shape_keys,
  get_object_,
  active_collection,
  get_active_collection,
  get_props,
  active_object_,
  get_app,
  report_warning
)

def gen_mouth_bone ():
  context = get_context()
  new_collection = create_collection('Face_Panel')
  context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[new_collection.name]
  object.armature_add(enter_editmode = True)
  context.active_bone.name = 'face_panel'

  mouth_bone = copy_bone(context.active_bone, 'mouth', 0.1)
  # add_limit_location_constraint(
  #   mouth_bone, 
  #   owner_space = 'LOCAL',
  #   use_min_x = True,
  #   use_min_z = True,
  #   min_x = -0.2,
  #   min_z = -0.2,
  #   max_x = 0.2,
  #   max_z = 0.2
  # )

def camera_view ():
  context = get_context()
  prev_context = context.area.type
  context.area.type = 'VIEW_3D'
  get_ops().view3d.camera_to_view()
  context.area.type = prev_context

def import_shape_key_images (shape_key_names_map, texts, image_dir):
  images = []
  z = 0

  for category, shape_key_names in shape_key_names_map.items():
    files = []
    text = texts[category]
    text.location = (-1, 0, z)

    for shape_key_name in shape_key_names:
      files.append({ "name": f"{ shape_key_name }.png" })

    for i in range(0, len(files), 8):
      _files = files[i:i+8]
      snap_cursor((0, 0, z))
      get_ops().image.import_as_mesh_planes(
        files = _files, 
        directory = image_dir,
        height = 1,
        align_axis = '-Y',
        offset = True,
        offset_amount = 0,
        use_transparency = False
      )
      
      z -= 1
    
    for shape_key_name in shape_key_names:
      image = get_object_(shape_key_name)
      image.name = f'{ ref_image_prefix }{ image.name }'
      image.parent = text
      image.matrix_parent_inverse = text.matrix_world.inverted()
      images.append(image)

  return images

def freeze_location (target, axis, step = 1):
  # 0 表示 x 轴
  param = 0

  if axis == 'y':
    param = 1
  elif axis == 'z':
    param = 2

  # 如果能有办法判断出移动结束，可以替换掉监听视图更新，达到最好的性能
  # target['x'] = 0.0
  # target.driver_remove('["x"]')
  # driver = target.driver_add('["x"]').driver
  # driver.type = 'SCRIPTED'
  # var = driver.variables.new()
  # var.name = 'var'
  # var.type = 'TRANSFORMS'
  # _target = var.targets[0]
  # _target.id = target
  # _target.transform_type = f'LOC_{ axis.upper() }'
  # _target.transform_space = 'TRANSFORM_SPACE'
  # def driverFunc(var):
  #   # print('自身位置', var)
  #   return var
  
  # driverFunc.operator = None

  # bpy.app.driver_namespace['driverFunc'] = driverFunc
  # driver.expression = f'driverFunc(var)'

  target.driver_remove("location", param)
  driver = target.driver_add("location", param).driver
  driver.type = 'SCRIPTED'
  var = driver.variables.new()
  var.name = 'var'
  var.type = 'TRANSFORMS'
  _target = var.targets[0]
  _target.id = target
  _target.transform_type = f'LOC_{ axis.upper() }'
  _target.transform_space = 'TRANSFORM_SPACE'
  driver.expression = f'round(var * { 1 / step }) / { 1 / step }'

def freeze_selectors_and_shape_key_images(categories, images, dichotomy_category_names):
  for category in categories:
    selectors = []

    if category in dichotomy_category_names:
      selectors.extend([
        get_object_(f'{ selector_prefix }{ category }.l'), 
        get_object_(f'{ selector_prefix }{ category }.r')
      ])
    else:
      selectors.append(get_object_(f'{ selector_prefix }{ category }'))
    
    for selector in selectors:
      # selector.location[1] = -0.01
      # 锁定 y 轴
      selector.lock_location[1] = True
      freeze_location(selector, 'x')
      freeze_location(selector, 'z')

  for image in images:
    image.lock_location[1] = True
    # freeze_location(image, 'x')
    # freeze_location(image, 'z')

def add_driver (options):
  target = options['target']
  prop = options['prop']
  type = options['type']
  vars = options['vars']
  targets = options['targets']
  expression = options['expression']
  target.driver_remove(prop)
  driver = target.driver_add(prop).driver
  driver.type = type

  for index, var in enumerate(vars):
    v = driver.variables.new()
    v.name = var['var_name']
    v.type = var['var_type']
    t1, t2 = v.targets
    t1.id = targets[index][0]['id']
    t1.transform_space = targets[index][0]['transform_space']
    t2.id = targets[index][1]['id']
    t2.transform_space = targets[index][1]['transform_space']
    
  driver.expression = expression

def shape_key_add_driver (shape_key_names_map, dichotomy_category_names, collection_name):
  def init_targets (options, target1, target2):
    options['targets'].append([
      { 
        'id': target1, 
        'transform_space': 'TRANSFORM_SPACE'
      },
      {
        'id': target2, 
        'transform_space': 'TRANSFORM_SPACE'
      }
    ])

  create_collection(collection_name)
  active_collection(collection_name)
  get_ops().object.empty_add(type = 'PLAIN_AXES')
  empty_object = get_active_object()
  empty_object.name = shape_key_empty_object

  for category, shape_key_names in shape_key_names_map.items():
    separated = category in dichotomy_category_names

    for shape_key_name in shape_key_names:
      image = ref_image_prefix + shape_key_name

      if separated:
        list = ['.l', '.r']
        for item in list:
          # 写成浮点数形式，值才是浮点数
          empty_object[shape_key_name + item] = 0.0
          driver_options = {
            'target': empty_object,
            'prop': f'["{ shape_key_name }{ item }"]',
            'type': 'SCRIPTED',
            'vars': [{ 'var_name': 'var', 'var_type': 'LOC_DIFF' }],
            'targets': [],
            'expression': '1 - var'
          }
          selector = get_object_(f'{ selector_prefix }{ category }{ item }')
          init_targets(driver_options, selector, get_object_(image))
          add_driver(driver_options)
      else:
        empty_object[shape_key_name] = 0.0
        driver_options = {
          'target': empty_object,
          'prop': f'["{ shape_key_name }"]',
          'type': 'SCRIPTED',
          'vars': [{ 'var_name': 'var', 'var_type': 'LOC_DIFF' }],
          'targets': [],
          'expression': '1 - var'
        }
        selector = get_object_(f'{ selector_prefix }{ category }')
        init_targets(driver_options, selector, get_object_(image))
        add_driver(driver_options)     

def gen_label_texts (categories, collection_name):
  create_collection(collection_name)
  active_collection(collection_name)
  texts = {}

  for category in categories:
    get_object().text_add(align='WORLD', location=(-1, 0, 0))
    text = get_active_object()
    text.data.body = category
    # text.data.size = 0.05
    text.data.align_x = 'RIGHT'
    text.data.align_y = 'CENTER'
    texts[category] = text
    text.select_set(True)
    text.name = f'shape_key_text_{ category }'
    ops = get_ops()
    ops.transform.rotate(value = -1.5708, orient_axis = 'X', orient_type = 'GLOBAL')
    ops.object.select_all(action='DESELECT')

  return texts

def gen_collections (collection_names):
  # parent_collection_name = 'shape_key_selector'
  # create_collection(parent_collection_name)

  for collection_name in collection_names:
    # create_collection(collection_name, parent_collection_name)
    create_collection(collection_name)

def check_shape_key_names (shape_keys, dichotomy_category_names):
  passing = True

  # 被拆分的类别中 .l 和 .r 必须同时存在
  for category in dichotomy_category_names:
    for shape_key in shape_keys:
      shape_key_name = shape_key.name

      if (
        shape_key_name.startswith(category + '_') and 
        shape_key_name.endswith(('.l', '.r'))
      ):
        # TODO: 保存检测过的一边 之后遇到到另一边时直接跳过
        side = shape_key_name.split('.')[-1]
        mirror_side = 'l' if side == 'r' else 'r'
        mirror_name = shape_key_name[:-1] + mirror_side

        if not shape_keys.get(mirror_name):
          passing = False

          return passing, mirror_name, category
        
  return passing, None, None

def split_shape_keys (shape_keys, mesh, shape_key_names_map, dichotomy_category_names):
  for category in dichotomy_category_names:
    shape_key_names = shape_key_names_map[category]

    for shape_key_name in shape_key_names:
      shape_key = shape_keys.get(shape_key_name + '.l')
      
      # 存在 .l 则一定存在 .r，说明这个形态键已经被拆分了
      if not shape_key:
        l = mesh.shape_key_add(name = f"{ shape_key_name }.l")
        r = mesh.shape_key_add(name = f"{ shape_key_name }.r")

        # 遍历所有顶点，拆分形态键
        _shape_key = shape_keys.get(shape_key_name)
        for i, vert in enumerate(_shape_key.data):
          co = vert.co

          if co.x > 0:
            l.data[i].co = co
          else:
            r.data[i].co = co

def rename_shape_keys (
  shape_keys, 
  merged_category_names
):
  name_map = {
    '基型': 'basis',
    # phoneme
    'あ': 'phoneme_ah',
    'い': 'phoneme_ch',
    'う': 'phoneme_u',
    'え': 'phoneme_e',
    'お': 'phoneme_oh',
    # mouth
    'にやり': 'mouth_grin',
    'ワ': 'mouth_wa',
    'ん': 'mouth_hmm',
    'い１': 'mouth_ch1',
    'い２': 'mouth_ch2',
    'あ２': 'mouth_ah2',
    'にやり２': 'mouth_grin2',
    'にやり３': 'mouth_grin3',
    'ω': 'mouth_ω',
    'てへぺろ': 'mouth_lick_mouth',
    'ぺろっ': 'mouth_stick_out_tongue',
    '口横広げ': 'mouth_side_widen',
    '口横狭め': 'mouth_side_narrow',
    '舌広げ': 'mouth_tongue_widen',
    '口角上げ': 'mouth_up',
    '口角下げ': 'mouth_down',
    # eyebrow
    '真面目': 'eyebrow_serious',
    '困る': 'eyebrow_worried',
    'にこり': 'eyebrow_cheerful',
    '怒り': 'eyebrow_angry',
    '悲しむ': 'eyebrow_sad',
    '悲しむ左': 'eyebrow_sad.l',
    '悲しむ右': 'eyebrow_sad.r',
    '恥ずかしい': 'eyebrow_ashamed',
    '上': 'eyebrow_upper',
    '下': 'eyebrow_lower',
    '前': 'eyebrow_front',
    '真面目左': 'eyebrow_serious.l',
    '真面目右': 'eyebrow_serious.r',
    '困る左': 'eyebrow_worried.l',
    '困る右': 'eyebrow_worried.r',
    'にこり左': 'eyebrow_cheerful.l',
    'にこり右': 'eyebrow_cheerful.r',
    '怒り左': 'eyebrow_angry.l',
    '怒り右': 'eyebrow_angry.r',
    '恥ずかしい左': 'eyebrow_ashamed.l',
    '恥ずかしい右': 'eyebrow_ashamed.r',
    '上左': 'eyebrow_upper.l',
    '上右': 'eyebrow_upper.r',
    '下左': 'eyebrow_lower.l',
    '下右': 'eyebrow_lower.r',
    '前左': 'eyebrow_front.l',
    '前右': 'eyebrow_front.r',
    # eye
    'まばたき': 'eye_blink',
    '笑い': 'eye_blink_happy',
    'なごみ': 'eye_calm',
    'ウィンク': 'eye_blink_happy.l', # 'eye_wink',
    'ウィンク右': 'eye_blink_happy.r', # 'eye_wink.r',
    'ウィンク２': 'eye_blink.l', # 'eye_wink2',
    'ウィンク２右': 'eye_blink.r', # 'eye_wink2.r',
    'なごみ左': 'eye_calm.l',
    'なごみ右': 'eye_calm.r',
    'びっくり': 'eye_suprised',
    'じと目': 'eye_stare',
    '喜び': 'eye_happy',
    '怒り目': 'eye_angry',
    'ジト目': 'eye_contemptuous',
    '眼角上': 'eye_horn_up',
    '眼角下': 'eye_horn_down',
    '下眼上': 'eye_lower_up',
    '瞳小': 'eye_miosis',
  }
  shape_key_map = defaultdict(list)

  for shape_key in shape_keys:
    shape_key_name = shape_key.name

    if shape_key_name in name_map:
      new_shape_key_name = name_map[shape_key_name]
      shape_key.name = new_shape_key_name

      for category in merged_category_names:
        if (
          new_shape_key_name.startswith(category + '_') and
          not new_shape_key_name.endswith(('.l', '.r'))
        ):
          shape_key_map[category].append(new_shape_key_name)

  return shape_key_map

def gen_shape_key_selector (
  image_dir, 
  overwrite, 
  merged_category_names, 
  dichotomy_category_names, 
  shape_keys, 
  mesh
):
  # TODO: 添加另一种嘴型选择器 https://www.bilibili.com/video/BV1ix4y1R7aw
  shape_key_map = rename_shape_keys(shape_keys, merged_category_names)
  split_shape_keys(shape_keys, mesh, shape_key_map, dichotomy_category_names)
  master_collection_name = 'shape_key_selector'
  # collection.children.link(child_collection)
  camera_collection_name = 'shape_key_cameras'
  text_collection_name = 'shape_key_texts'
  selector_collection_name = 'shape_key_selectors'
  empty_object_collection_name = 'shape_key_empty_objects'
  camera_prefix = 'shape_key_camera_'
  gen_cameras(merged_category_names, camera_collection_name, camera_prefix)
  texts = gen_label_texts(merged_category_names, text_collection_name)
  gen_shape_key_images(
    shape_key_map, 
    shape_keys, 
    image_dir,
    overwrite,
    camera_prefix
  )
  images = import_shape_key_images(shape_key_map, texts, image_dir)
  gen_selectors(merged_category_names, texts, dichotomy_category_names, selector_collection_name)
  freeze_selectors_and_shape_key_images(merged_category_names, images, dichotomy_category_names)
  shape_key_add_driver(shape_key_map, dichotomy_category_names, empty_object_collection_name)

def gen_selectors (merged_category_names, texts, dichotomy_category_names, collection_name):
  def gen_selector (dir, side, z):
    file_path = os.path.join(dir, '..', f'assets/selector{ side }.json')
    name = f'{ selector_prefix }{ category }{ side }'
    model_data = ''

    with open(file_path, 'r') as json_file:
      model_data = json.load(json_file)

    vertices = model_data.get('vertices', [])
    faces = model_data.get('faces', [])
    material_indices = model_data.get('material_indices', [])
    materials = model_data.get('materials', [])
    mesh = get_data().meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    obj = get_data().objects.new(name, mesh)
    # 放入集合
    collection.objects.link(obj)

    for material_data in materials:
      material_name = material_data.get('name', '')
      material = get_material(material_name)

      if not material:
        material = create_material(material_name)
        material.diffuse_color = material_data.get('diffuse_color', [1, 1, 1, 1])  # Default color if not specified
        material.specular_intensity = material_data.get('specular_intensity', 0.0)  # Default to 0.0 if not specified
        obj.data.materials.append(material)
        
    for face_index, material_index in enumerate(material_indices):
      if material_index < len(obj.data.materials):
        obj.data.polygons[face_index].material_index = material_index
    
    text = texts[category]
    obj.parent = text
    obj.matrix_parent_inverse = text.matrix_world.inverted()
    obj.location = (-1, 0, z)
    obj.scale = (9, 9, 9)
    # 设置成常量插值
    # obj.keyframe_insert(data_path="location", index=0, frame=0) 
    # obj.keyframe_insert(data_path="location", index=2, frame=0) 
    # fcurves = obj.animation_data.action.fcurves
    # for fcurve in fcurves:
    #   keyframe_points = fcurve.keyframe_points

    #   for keyframe_point in keyframe_points:
    #     keyframe_point.interpolation = 'CONSTANT'

  dir = os.path.dirname(os.path.abspath(__file__))
  collection = create_collection(collection_name)
  active_collection(collection_name)

  for index, category in enumerate(merged_category_names):
    z = texts[category].location[2]
    # z = z_list[index]

    if category in dichotomy_category_names:
      gen_selector(dir, '.l', z)
      gen_selector(dir, '.r', z)
    else:
      gen_selector(dir, '', z)

def gen_cameras (categories, collection_name, camera_prefix):
  create_collection(collection_name)
  active_collection(collection_name)

  for category in categories:
    get_object().camera_add(rotation = (1.5708, 0, 0))
    camera = get_active_object()
    camera.name = camera_prefix + category

def gen_shape_key_images (
  shape_key_names_map,
  shape_keys, 
  image_dir,
  overwrite,
  camera_prefix
):
  # TODO: 通过 python 进入摄像机视角
  context = get_context()
  filepath = context.scene.render.filepath
  resolution_x = context.scene.render.resolution_x
  resolution_y = context.scene.render.resolution_y
  context.scene.render.resolution_x = 1080
  context.scene.render.resolution_y = 1080

  for category, shape_key_names in shape_key_names_map.items():
    # TODO: 检查相机是否存在
    camera = get_object_(camera_prefix + category)
    context.scene.camera = camera

    for shape_key_name in shape_key_names:
      image_path = f"{ image_dir }{ shape_key_name }.png"
      exists = os.path.exists(image_path)

      if (not exists) or (exists and overwrite):
        context.scene.render.filepath = image_path
        keyblock = shape_keys[shape_key_name]
        keyblock.value = 1
        get_ops().render.opengl(write_still = True)
        keyblock.value = 0

  context = get_context()
  context.scene.render.filepath = filepath
  context.scene.render.resolution_x = resolution_x
  context.scene.render.resolution_y = resolution_y

def before (self, merged_category_names, shape_key_name, shape_keys, dichotomy_category_names, mesh):
  passing = True

  if not shape_keys:
    passing = False
    report_warning(self, f"形态键 { shape_key_name } 不存在")

    return passing

  if not len(merged_category_names):
    passing = False
    report_warning(self, "至少需要一个类别")

    return passing

  # 检查被拆分的类别，要求 .l 和 .r 必须同时存在
  for category in dichotomy_category_names:
    for shape_key in shape_keys:
      shape_key_name = shape_key.name

      if (
        shape_key_name.startswith(category + '_') and 
        shape_key_name.endswith(('.l', '.r'))
      ):
        # 去除 .l 或 .r 后的名字
        base = shape_key_name[:-2]
        # .l 或 .r
        side = shape_key_name[-2:]
        mirror_side = '.l' if side == '.r' else '.r'
        mirror_name = base + mirror_side

        if not shape_keys.get(mirror_name):
          passing = False
          report_warning(self, f"形态键 { mirror_name } 不存在")

          return passing
        
  set_mode('OBJECT')
  active_object_(mesh)
        
  return passing

def merge_category_names (categories):
  merged_category_names = set()
  dichotomy_category_names = set()

  for category in categories:
    category_name = category.name

    if category_name.endswith(('.l', '.r')):
      # 去除 .l 或 .r 后缀
      _category_name = category_name[:-2]
      merged_category_names.add(_category_name)
      dichotomy_category_names.add(_category_name)
    else:
      merged_category_names.add(category_name)

  return merged_category_names, dichotomy_category_names

class OBJECT_OT_shape_key_selector (get_operator()):
  bl_idname = 'object.shape_key_selector'
  bl_label = 'Shape Key Selector'

  def execute(self, context):
    scene = context.scene
    categories = scene.categories
    mesh_name = scene.mesh_name
    shape_key_name = scene.shape_key_name
    overwrite = scene.overwrite
    # for test
    filepath = 'D:\\tmp2\\'
    # filepath = scene.render.filepath

    shape_keys = get_shape_keys(shape_key_name)
    merged_category_names, dichotomy_category_names = merge_category_names(categories)
    mesh = get_object_(mesh_name)
    passing = before(self, merged_category_names, shape_key_name, shape_keys, dichotomy_category_names, mesh)

    if passing:
      gen_shape_key_selector(
        filepath, 
        overwrite, 
        merged_category_names,
        dichotomy_category_names,
        shape_keys,
        mesh
      )

    return {'FINISHED'}
