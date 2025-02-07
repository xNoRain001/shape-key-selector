import os
import json

from ..const import selector_prefix, ref_image_prefix
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
  get_active_collection
)

def rename_shape_keys (key_blocks, categories, shape_keys, new_names):
  def gen_list ():
    merged_shape_key_names_with_category = {}
    separate_mark = {}
    shape_key_names_with_category = {}

    for category in categories:
      shape_key_names_with_category[category] = []
      separate_mark[category] = []
      merged_shape_key_names_with_category[category] = []

    return [
      merged_shape_key_names_with_category,
      separate_mark,
      shape_key_names_with_category
    ]

  (
    merged_shape_key_names_with_category,
    separate_mark,
    shape_key_names_with_category
  ) = gen_list()

  for key_block in key_blocks:
    old_name = key_block.name
    
    if old_name in shape_keys:
      new_name = shape_keys[old_name]
      key_block.name = new_name

      # 一个形状键有 .l 和 .r 说明这个形状键是被拆分的，不需要添加驱动器，拆分后的
      # .l 和 .r 才需要添加
      separated = f'{ new_name }.l' in new_names and f'{ new_name }.r' in new_names
      
      if new_name.startswith('phoneme'):
        if separated:
          # 被拆分，驱动器不添加，拍照添加
          merged_shape_key_names_with_category['phoneme'].append(new_name)
          separate_mark['phoneme'].append(separated)
        else:
          # 这里可能是未被拆分的形态键或者拆分后的 .l(r)
          if not (new_name.endswith('.l') or new_name.endswith('.r')):
            # 未被拆分的添加进拍照
            merged_shape_key_names_with_category['phoneme'].append(new_name)
            separate_mark['phoneme'].append(separated)

          # 未被拆分的或者拆分后的添加进驱动器
          shape_key_names_with_category['phoneme'].append(new_name)
      elif new_name.startswith('mouth'):
        if separated:
          merged_shape_key_names_with_category['mouth'].append(new_name)
          separate_mark['mouth'].append(separated)
        else:
          if not (new_name.endswith('.l') or new_name.endswith('.r')):
            merged_shape_key_names_with_category['mouth'].append(new_name)
            separate_mark['mouth'].append(separated)

          shape_key_names_with_category['mouth'].append(new_name)
      elif new_name.startswith('eyebrow'):
        if separated:
          merged_shape_key_names_with_category['eyebrow'].append(new_name)
          separate_mark['eyebrow'].append(separated)
        else:
          if not (new_name.endswith('.l') or new_name.endswith('.r')):
            merged_shape_key_names_with_category['eyebrow'].append(new_name)
            separate_mark['eyebrow'].append(separated)

          shape_key_names_with_category['eyebrow'].append(new_name)
      elif new_name.startswith('eye'):
        if separated:
          merged_shape_key_names_with_category['eye'].append(new_name)
          separate_mark['eye'].append(separated)
        else:
          if not (new_name.endswith('.l') or new_name.endswith('.r')):
            merged_shape_key_names_with_category['eye'].append(new_name)
            separate_mark['eye'].append(separated)

          shape_key_names_with_category['eye'].append(new_name)

  return [
    shape_key_names_with_category, 
    merged_shape_key_names_with_category, 
    separate_mark
  ]

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

def import_shape_key_images (merged_shape_key_names_with_category, texts, image_dir):
  images = []
  z = 0
  z_list = []

  for category, shape_key_names in merged_shape_key_names_with_category.items():
    files = []
    text = texts[category]
    text.location = (-1, 0, z)
    z_list.append(z)

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

  return [images, z_list]

def freeze_frame (target, axis):
  # 0 表示 x 轴
  param = 0

  if axis == 'y':
    param = 1
  elif axis == 'z':
    param = 2

  # 添加驱动器
  driver = target.driver_add("location", param).driver
  # 设置驱动器类型
  driver.type = 'SCRIPTED'
  # 添加变量
  var = driver.variables.new()
  var.name = 'var'
  var.type = 'TRANSFORMS'
  _target = var.targets[0]
  _target.id = target
  _target.transform_type = f'LOC_{ axis.upper() }'
  _target.transform_space = 'TRANSFORM_SPACE'
  driver.expression = 'round(var)'
  # round(var * 2) / 2

def freeze_selectors_and_shape_key_images(categories, images, separate_mark):
  for category in categories:
    separated = any(separate_mark[category])
    selectors = [
      get_object_(f'{ selector_prefix }{ category }.l'), 
      get_object_(f'{ selector_prefix }{ category }.r')] if separated else [get_object_(f'{ selector_prefix }{ category }')]
    
    for selector in selectors:
      # selector.location[1] = -0.01
      # 锁定 y 轴
      selector.lock_location[1] = True
      freeze_frame(selector, 'x')
      freeze_frame(selector, 'z')

  for image in images:
    image.lock_location[1] = True
    freeze_frame(image, 'x')
    freeze_frame(image, 'z')

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

def shape_key_add_driver (shape_key_names_with_category, separate_mark, key_blocks):
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

  for category, shape_key_names in shape_key_names_with_category.items():
    separated = any(separate_mark[category])

    for shape_key_name in shape_key_names:
      key_block = key_blocks[shape_key_name]
      driver_options = {
        'target': key_block,
        'prop': 'value',
        'type': 'SCRIPTED',
        'vars': [{ 'var_name': 'var', 'var_type': 'LOC_DIFF' }],
        'targets': [],
        'expression': '1 - var'
      }
      selector = get_object_(f'{ selector_prefix }{ category }')
      selector_l = get_object_(f'{ selector_prefix }{ category }.l')
      selector_r = get_object_(f'{ selector_prefix }{ category }.r')
      l = shape_key_name.endswith('.l')
      r = shape_key_name.endswith('.r')
      image = get_object_(ref_image_prefix + (shape_key_name[:-2] if l or r else shape_key_name))
      
      if l:
        init_targets(driver_options, selector_l, image)
      elif r:
        init_targets(driver_options, selector_r, image)
      elif separated:
        # 是未分割的形态键，但是所在的组有其他形态键被分割过
        init_targets(driver_options, selector_l, image)
        driver_options['vars'].append({ 'var_name': 'var2', 'var_type': 'LOC_DIFF' })
        init_targets(driver_options, selector_r, image)
        driver_options['expression'] = '1 - (var + var2) / 2'
      else:
        # 所在的组所有形态键都未被分割过
        init_targets(driver_options, selector, image)

      add_driver(driver_options)

def gen_tip_texts (categories, collection_name):
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

def check_shape_key_names (shape_keys):
  shape_key_names = {}

  for value in shape_keys.values():
    shape_key_names[value] = None

  for new_name in shape_key_names.keys():
    if (
      (f'{ new_name }.l' in shape_key_names) ^ 
      (f'{ new_name }.r' in shape_key_names)
    ):
      print('形状键命名不符合规范')

      return False
    
  return [True, shape_key_names]

def gen_shape_key_selector (image_dir, overwrite, categories, self, shape_key):
  # for test
  # image_dir = 'D:\\tmp2\\'

  # TODO: 添加另一种嘴型选择器 https://www.bilibili.com/video/BV1ix4y1R7aw
  shape_keys = {
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
  key_blocks = get_shape_keys(shape_key)

  if not key_blocks:
    self.report({'WARNING'}, "形状键不存在")

    return
  
  passing, shape_key_names = check_shape_key_names(shape_keys)

  if not passing:
    self.report({'WARNING'}, "形状键命名不符合规范")

    return
  
  collection_names = [
    'shape_key_cameras', 
    'shape_key_texts', 
    # 图片会和文本进行父子绑定
    # 'shape_key_ref_images',
    'shape_key_selectors',
  ]
  camera_prefix = 'shape_key_camera_'
  gen_collections(collection_names)
  gen_cameras(categories, collection_names[0], camera_prefix)
  (
    shape_key_names_with_category, 
    merged_shape_key_names_with_category, 
    separate_mark
  ) = rename_shape_keys(key_blocks, categories, shape_keys, shape_key_names)
  texts = gen_tip_texts(categories, collection_names[1])
  gen_shape_key_images(
    merged_shape_key_names_with_category, 
    key_blocks, 
    image_dir,
    overwrite,
    camera_prefix
  )
  images, z_list = import_shape_key_images(
    merged_shape_key_names_with_category, 
    texts, 
    image_dir
  )
  gen_selectors(categories, texts, separate_mark, z_list, collection_names[2])
  freeze_selectors_and_shape_key_images(categories, images, separate_mark)
  shape_key_add_driver(shape_key_names_with_category, separate_mark, key_blocks)

def gen_selectors (categories, texts, separate_mark, z_list, collection_name):
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
    get_context().scene.collection.objects.link(obj)

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
    obj.location = (0, 0, z)
    obj.scale = (9, 9, 9)

  dir = os.path.dirname(os.path.abspath(__file__))
  active_collection(collection_name)

  for index, category in enumerate(categories):
    separated = any(separate_mark[category])
    z = z_list[index]

    if separated:
      gen_selector(dir, '.l', z)
      gen_selector(dir, '.r', z)
    else:
      gen_selector(dir, '', z)

def gen_cameras (categories, collection_name, camera_prefix):
  active_collection(collection_name)

  for category in categories:
    get_object().camera_add(rotation = (1.5708, 0, 0))
    camera = get_active_object()
    camera.name = camera_prefix + category

def gen_shape_key_images (
  merged_shape_key_names_with_category,
  key_blocks, 
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

  for category, shape_key_names in merged_shape_key_names_with_category.items():
    # TODO: 检查相机是否存在
    camera = get_object_(camera_prefix + category)
    context.scene.camera = camera

    for shape_key_name in shape_key_names:
      image_path = f"{ image_dir }{ shape_key_name }.png"
      exists = os.path.exists(image_path)

      if (not exists) or (exists and overwrite):
        context.scene.render.filepath = image_path
        keyblock = key_blocks[shape_key_name]
        keyblock.value = 1
        get_ops().render.opengl(write_still = True)
        keyblock.value = 0

  context = get_context()
  context.scene.render.filepath = filepath
  context.scene.render.resolution_x = resolution_x
  context.scene.render.resolution_y = resolution_y

def before (self, category_collections):
  passing = True
  categories = []

  if not len(category_collections):
    passing = False
    self.report({'WARNING'}, "至少需要一个类别")
  else:
    for category_collection in category_collections:
      categories.append(category_collection.name)

    set_mode('OBJECT')

  return [passing, categories]

class Shape_Key_Selector (get_operator()):
  bl_idname = 'object.shape_key_selector'
  bl_label = 'Shape Key Selector'

  def execute(self, context):
    scene = context.scene
    category_collections = scene.my_properties
    [passing, categories] = before(self, category_collections)

    if passing:
      gen_shape_key_selector(
        scene.render.filepath, 
        scene.overwrite, 
        categories, 
        self,
        scene.shape_key
      )

    return {'FINISHED'}
