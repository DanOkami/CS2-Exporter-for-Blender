import bpy
import os
import math
import random
import mathutils
import numpy as np

bl_info = {
    "name": "CS2 Modding Suite",
    "author": "DanOkami",
    "version": (1, 8),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > CS2 Suite",
    "description": "Cities Skylines 2 - 3D Modeling Suite: FBX Export, Windows UV and Texture Atlas Baking with Channel Packing",
    "category": "Object"
}

# ==========================================
# MODULE 1: FBX EXPORTER 
# ==========================================
def duplicate_and_prepare_model(original):
    bpy.context.view_layer.objects.active = original
    bpy.ops.object.select_all(action='DESELECT')
    original.select_set(True)
    
    bpy.ops.object.duplicate(linked=False)
    copy = bpy.context.active_object
    copy.name = f"{original.name}_Copy"
    original.name = f"{original.name}_Original"
    return original, copy

def center_model_origin_and_apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    
    if bpy.context.scene.cs2_use_reset_origin:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        obj.location = (0, 0, 0)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    obj.rotation_euler = (math.radians(-90), 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    obj.scale = (100, 100, 100)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if bpy.context.scene.cs2_use_reset_origin:
        obj.location.y = obj.dimensions.y / 2
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def export_model_fbx(obj, file_path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.export_scene.fbx(
        filepath=file_path,
        use_selection=True,
        global_scale=1.0,
        axis_up='Y',
        axis_forward='-Z',
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        object_types={'MESH'},
        use_mesh_modifiers=True,
        add_leaf_bones=False
    )

def clean_up(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.object.delete()

def separate_by_vertex_groups(obj):
    separated_objects = []
    model_name = obj.name.split('_')[0]

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    for group in obj.vertex_groups:
        vg_index = group.index
        has_verts = any(vg_index in [g.group for g in v.groups] for v in obj.data.vertices)
        if not has_verts:
            continue

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate(linked=False)
        new_model = bpy.context.active_object

        if group.name == "Base":
            new_model.name = f'{model_name}'
        else: 
            new_model.name = f'{model_name}_{group.name}'

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.vertex_group_set_active(group=group.name)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='VERT')

        bpy.ops.object.mode_set(mode='OBJECT')
        
        if len(new_model.data.vertices) == 0:
            bpy.data.objects.remove(new_model, do_unlink=True)
        else:
            new_model.vertex_groups.clear()
            separated_objects.append(new_model)
            
        bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.delete()
    return separated_objects

def separate_by_materials(obj):
    separated_objects = []
    model_name = obj.name.split('_')[0]

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    for index, slot in enumerate(obj.material_slots):
        if not slot.material:
            continue

        has_polys = any(p.material_index == index for p in obj.data.polygons)
        if not has_polys:
            continue

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate(linked=False)
        new_model = bpy.context.active_object

        if slot.name == "Base":
            new_model.name = f'{model_name}'
        else: 
            new_model.name = f'{model_name}_{slot.name}'

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        new_model.active_material_index = index
        bpy.ops.object.material_slot_select()
        
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
        
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)

        bpy.ops.object.mode_set(mode='OBJECT')
        
        if len(new_model.data.polygons) == 0:
            bpy.data.objects.remove(new_model, do_unlink=True)
        else:
            separated_objects.append(new_model)
            
        bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.delete()
    return separated_objects

def main_export(scene):
    if bpy.context.mode != "OBJECT":
        print("Mode must be \"OBJECT\"")
        return
    active = bpy.context.active_object
    if not active or active.type != 'MESH':
        print("Select a valid mesh.")
        return

    blend_filepath = bpy.context.blend_data.filepath
    project_directory = os.path.dirname(blend_filepath)
    folder_path = os.path.join(project_directory, active.name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    original, copy = duplicate_and_prepare_model(active)
    center_model_origin_and_apply_transform(copy)
    
    if scene.cs2_export_method == 'MATERIAL':
        separated_objects = separate_by_materials(copy)
    else:
        separated_objects = separate_by_vertex_groups(copy)

    for obj in separated_objects:
        file_path = os.path.join(folder_path, f"{obj.name}.fbx")
        export_model_fbx(obj, file_path)

    clean_up(separated_objects)
    bpy.context.view_layer.objects.active = original
    original.name = original.name.split("_Original")[0]


# ==========================================
# MODULE 2: WINDOWS UV MAP BAKE
# ==========================================
def bakeWindowsUV(operator, context):
    if bpy.context.mode != "OBJECT":
        operator.report({'WARNING'}, "Mode must be \"OBJECT\"")
        return
    active = bpy.context.active_object
    if not active or active.type != 'MESH':
        operator.report({'WARNING'}, "Select a valid mesh")
        return
        
    scene = context.scene
    target_method = scene.cs2_uv_target_method
    target_name = scene.cs2_uv_target_name
    
    target_list = []
    if target_name == 'WIN': target_list = ["Win"]
    elif target_name == 'WIM': target_list = ["Wim"]
    elif target_name == 'BOTH': target_list = ["Win", "Wim"]

    mesh = active.data
    selected_polygons = []

    if target_method == 'VGROUP':
        vg_indices = [vg.index for vg in active.vertex_groups if vg.name in target_list]
        if not vg_indices:
            operator.report({'WARNING'}, f"Vertex group(s) not found: {target_list}")
            return
            
        verts_in_group = {v.index for v in mesh.vertices if any(g.group in vg_indices for g in v.groups)}
        selected_polygons = [poly for poly in mesh.polygons if all(v in verts_in_group for v in poly.vertices)]
        
    else:
        mat_indices = [i for i, slot in enumerate(active.material_slots) if slot.name in target_list]
        if not mat_indices:
            operator.report({'WARNING'}, f"Material(s) not found: {target_list}")
            return
            
        selected_polygons = [poly for poly in mesh.polygons if poly.material_index in mat_indices]

    if not selected_polygons:
        operator.report({'WARNING'}, "No matching polygons found!")
        return

    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        uv_layer = mesh.uv_layers[0]
    uv_layer_data = uv_layer.data 
            
    random.shuffle(selected_polygons)
    
    UV_grid = [[[] for _ in range(5)] for _ in range(5)]
    min_val = scene.cs2_grid_range_min
    max_val = scene.cs2_grid_range_max
    if min_val > max_val:
        min_val, max_val = max_val, min_val

    for poly in selected_polygons:
        cell_index = random.randint(min_val, max_val)
        c = cell_index % 5
        r = 4 - (cell_index // 5) 
        UV_grid[r][c].append(poly)

    for r in range(5):
        for c in range(5):
            polys_in_cell = UV_grid[r][c]
            n = len(polys_in_cell)
            if n == 0:
                continue

            subdiv = math.ceil(n ** 0.5)
            cell_padding = 0.02
            subcell_padding = 0.05
            scale_uv = 0.2
            
            subcell_size = scale_uv / subdiv * (1 - cell_padding)
            cell_offset_u = c * scale_uv + (scale_uv / subdiv) * cell_padding / 2
            cell_offset_v = r * scale_uv + (scale_uv / subdiv) * cell_padding / 2

            for idx, face in enumerate(polys_in_cell):
                row = idx // subdiv
                col = idx % subdiv
                
                normal = face.normal.normalized()
                global_z = mathutils.Vector((0,0,1))
                
                sub_offset_u = cell_offset_u + col * subcell_size + subcell_size * subcell_padding / 2
                sub_offset_v = cell_offset_v + row * subcell_size + subcell_size * subcell_padding / 2
                effective_subcell_size = subcell_size * (1 - subcell_padding)
                
                tangent = -normal.cross(global_z).normalized()
                bitangent = global_z

                verts_2d = []
                for i in range(face.loop_start, face.loop_start + face.loop_total):
                    loop = mesh.loops[i]
                    v_world = active.matrix_world @ mesh.vertices[loop.vertex_index].co
                    local = mathutils.Vector((v_world.dot(tangent), v_world.dot(bitangent)))
                    verts_2d.append(local)

                min_x = min(v.x for v in verts_2d)
                min_y = min(v.y for v in verts_2d)
                max_x = max(v.x for v in verts_2d)
                max_y = max(v.y for v in verts_2d)
                scale_x = max_x - min_x
                scale_y = max_y - min_y

                if scale_x > scale_y:
                    aspect = scale_y / scale_x if scale_x != 0 else 1
                    eff_x = effective_subcell_size
                    eff_y = effective_subcell_size * aspect
                else:
                    aspect = scale_x / scale_y if scale_y != 0 else 1
                    eff_x = effective_subcell_size * aspect
                    eff_y = effective_subcell_size

                for j, v in enumerate(verts_2d):
                    loop_index = face.loop_start + j
                    u = (v.x - min_x) / scale_x if scale_x != 0 else 0
                    v_coord = (v.y - min_y) / scale_y if scale_y != 0 else 0
                    uv_layer_data[loop_index].uv = (
                        sub_offset_u + u * eff_x,
                        sub_offset_v + v_coord * eff_y
                    )


# ==========================================
# MODULE 3: BATCH BAKING ATLAS
# ==========================================
def setup_bake_nodes_for_material(material, prefix):
    if not material or not material.use_nodes:
        return

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return

    loc_x, loc_y = principled.location
    
    target_names = [f"{prefix}_BaseColor", f"{prefix}_Normal", f"{prefix}_MaskMap"]
    img_offset_y = 300
    for t_name in target_names:
        if not any(n.type == 'TEX_IMAGE' and n.image and n.image.name == t_name for n in nodes):
            img_node = nodes.new('ShaderNodeTexImage')
            img_node.image = bpy.data.images.get(t_name)
            img_node.name = f"BAKE_TARGET_{t_name}"
            img_node.location = (loc_x - 300, loc_y + img_offset_y)
            img_offset_y += 300

    if any(n.name == "BAKE_SWITCH" or n.label == "BAKE_SWITCH" for n in nodes):
        return

    base_color_link = principled.inputs['Base Color'].links[0] if principled.inputs['Base Color'].links else None
    roughness_link = principled.inputs['Roughness'].links[0] if principled.inputs['Roughness'].links else None
    metallic_link = principled.inputs['Metallic'].links[0] if principled.inputs['Metallic'].links else None

    rgb_to_bw = nodes.new('ShaderNodeRGBToBW')
    rgb_to_bw.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    
    invert = nodes.new('ShaderNodeInvert')
    invert.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
    
    try:
        combine = nodes.new('ShaderNodeCombineColor')
    except Exception:
        combine = nodes.new('ShaderNodeCombineRGB')

    try:
        bake_switch = nodes.new('GeometryNodeMenuSwitch')
        bake_switch.data_type = 'RGBA'
    except Exception:
        bake_switch = nodes.new('ShaderNodeMix')
        bake_switch.data_type = 'RGBA'
        bake_switch.blend_type = 'MIX'
        
    bake_switch.name = "BAKE_SWITCH"
    bake_switch.label = "BAKE_SWITCH"

    bake_switch.location = (loc_x - 300, loc_y)
    combine.location = (loc_x - 500, loc_y)
    rgb_to_bw.location = (loc_x - 700, loc_y + 100)
    invert.location = (loc_x - 700, loc_y - 100)

    if metallic_link:
        links.new(metallic_link.from_socket, rgb_to_bw.inputs['Color'])
        links.remove(metallic_link)
    principled.inputs['Metallic'].default_value = 0.0

    if roughness_link:
        links.new(roughness_link.from_socket, invert.inputs[1])

    links.new(rgb_to_bw.outputs[0], combine.inputs[0])
    links.new(invert.outputs[0], combine.inputs[2])
    combine.inputs[1].default_value = 0.0

    socket_a = bake_switch.inputs.get('A') or bake_switch.inputs.get('False') or bake_switch.inputs[1]
    socket_b = bake_switch.inputs.get('B') or bake_switch.inputs.get('True') or bake_switch.inputs[2]
    
    links.new(combine.outputs[0], socket_b)
    
    if base_color_link:
        links.new(base_color_link.from_socket, socket_a)

    links.new(bake_switch.outputs[0], principled.inputs['Base Color'])


def set_material_switch(material, state):
    if not material or not material.use_nodes:
        return
    for node in material.node_tree.nodes:
        if node.name == "BAKE_SWITCH" or node.label == "BAKE_SWITCH":
            try:
                if len(node.inputs) > 0 and type(node.inputs[0].default_value) == str:
                    node.inputs[0].default_value = 'A' if state == 0 else 'B'
                elif 'Fac' in node.inputs:
                    node.inputs['Fac'].default_value = float(state)
                elif 'Switch' in node.inputs:
                    node.inputs['Switch'].default_value = bool(state)
                elif 'Menu' in node.inputs:
                    node.inputs['Menu'].default_value = int(state)
                elif len(node.inputs) > 0:
                    node.inputs[0].default_value = int(state)
            except Exception as e:
                print(f"Warning: Cannot change switch on material {material.name}: {e}")

def prepare_nodes_for_bake(objects, target_image_name, switch_state):
    target_image = bpy.data.images.get(target_image_name)
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            set_material_switch(mat, switch_state)
            nodes = mat.node_tree.nodes
            for node in nodes:
                node.select = False
            bake_node = None
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.image == target_image:
                    bake_node = node
                    break
            if not bake_node:
                bake_node = nodes.new('ShaderNodeTexImage')
                bake_node.image = target_image
                bake_node.name = f"BAKE_TARGET_{target_image_name}"
                bake_node.location = (600, 300) 
            bake_node.select = True
            mat.node_tree.nodes.active = bake_node


class OBJECT_OT_cs2_setup_materials(bpy.types.Operator):
    bl_idname = "object.cs2_setup_materials"
    bl_label = "Setup Materials & Textures"
    bl_description = "Generates empty textures and sets up MaskMap nodes for all materials on the object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        prefix = scene.autobake_prefix
        if not prefix:
            self.report({'ERROR'}, "Please enter a Prefix before setup!")
            return {'CANCELLED'}

        size = int(scene.cs2_tex_size)
        
        tex_names = {
            'BASE': f"{prefix}_BaseColor",
            'NORM': f"{prefix}_Normal",
            'MASK': f"{prefix}_MaskMap"
        }

        for tex_type, name in tex_names.items():
            img = bpy.data.images.get(name)
            
            if img and (img.size[0] != size or img.size[1] != size):
                bpy.data.images.remove(img)
                img = None
            
            if not img:
                img = bpy.data.images.new(name, width=size, height=size, alpha=True)
                
                if tex_type == 'NORM':
                    try:
                        img.colorspace_settings.name = 'Non-Color'
                    except Exception:
                        pass
                    pixels = np.empty(size * size * 4, dtype=np.float32)
                    pixels[0::4] = 0.5  # R
                    pixels[1::4] = 0.5  # G
                    pixels[2::4] = 1.0  # B
                    pixels[3::4] = 1.0  # A
                    img.pixels.foreach_set(pixels)
                    img.update()

        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "Textures created (in memory). Select a mesh to apply nodes.")
            return {'FINISHED'}

        nodes_created = 0
        for obj in selected_objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material and slot.material.use_nodes:
                        setup_bake_nodes_for_material(slot.material, prefix)
                        nodes_created += 1

        self.report({'INFO'}, f"Setup complete: {size}x{size} Textures and {nodes_created} materials ready.")
        return {'FINISHED'}


class OBJECT_OT_BatchBakeCS2(bpy.types.Operator):
    bl_idname = "object.batch_bake_cs2"
    bl_label = "Run Batch Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        prefix = scene.autobake_prefix
        if not prefix:
            self.report({'ERROR'}, "Please enter a prefix!")
            return {'CANCELLED'}
            
        tex_base = f"{prefix}_BaseColor"
        tex_norm = f"{prefix}_Normal"
        tex_mask = f"{prefix}_MaskMap"
        
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "Select at least one object!")
            return {'CANCELLED'}
            
        bpy.context.scene.render.engine = 'CYCLES'
        try:
            for obj in selected_objects:
                if obj.type == 'MESH':
                    for slot in obj.material_slots:
                        if slot.material:
                            set_material_switch(slot.material, 0)
                            
            if scene.bake_do_basecolor:
                if not bpy.data.images.get(tex_base):
                    self.report({'ERROR'}, f"Missing texture: '{tex_base}'. Run Setup Materials first.")
                    return {'CANCELLED'}
                prepare_nodes_for_bake(selected_objects, tex_base, 0)
                bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                bpy.context.scene.render.bake.use_pass_direct = False
                bpy.context.scene.render.bake.use_pass_indirect = False
                bpy.context.scene.render.bake.use_pass_color = True
                bpy.ops.object.bake(type='DIFFUSE')
                
            if scene.bake_do_normal:
                if not bpy.data.images.get(tex_norm):
                    self.report({'ERROR'}, f"Missing texture: '{tex_norm}'. Run Setup Materials first.")
                    return {'CANCELLED'}
                prepare_nodes_for_bake(selected_objects, tex_norm, 0)
                bpy.context.scene.cycles.bake_type = 'NORMAL'
                bpy.ops.object.bake(type='NORMAL')
                
            if scene.bake_do_maskmap:
                if not bpy.data.images.get(tex_mask):
                    self.report({'ERROR'}, f"Missing texture: '{tex_mask}'. Run Setup Materials first.")
                    return {'CANCELLED'}
                prepare_nodes_for_bake(selected_objects, tex_mask, 1)
                bpy.context.scene.cycles.bake_type = 'DIFFUSE'
                bpy.context.scene.render.bake.use_pass_direct = False
                bpy.context.scene.render.bake.use_pass_indirect = False
                bpy.context.scene.render.bake.use_pass_color = True
                bpy.ops.object.bake(type='DIFFUSE')

                mask_img = bpy.data.images.get(tex_mask)
                if mask_img:
                    pixels = np.empty(len(mask_img.pixels), dtype=np.float32)
                    mask_img.pixels.foreach_get(pixels)
                    pixels = pixels.reshape(-1, 4)
                    pixels[:, 3] = pixels[:, 2]
                    mask_img.pixels.foreach_set(pixels.ravel())
                    mask_img.update()
                
        except Exception as e:
            self.report({'ERROR'}, f"Bake error: {str(e)}")
            return {'CANCELLED'}
        finally:
            for obj in selected_objects:
                if obj.type == 'MESH':
                    for slot in obj.material_slots:
                        if slot.material:
                            set_material_switch(slot.material, 0)
                            
        self.report({'INFO'}, "Bake completed!")
        return {'FINISHED'}


# ==========================================
# MODULE 4: UI OPERATORS & PANEL
# ==========================================
class OBJECT_OT_cs2_exporter(bpy.types.Operator):
    bl_idname = "object.cs2_exporter"
    bl_label = "Export FBX"
    def execute(self, context):
        main_export(context.scene)
        return {'FINISHED'}

class OBJECT_OT_cs2_bake_windows_uv(bpy.types.Operator):
    bl_idname = "object.cs2_bake_windows_uv"
    bl_label = "Bake Windows UV"
    def execute(self, context):
        bakeWindowsUV(self, context)
        return {'FINISHED'}

class OBJECT_PT_cs2_master_panel(bpy.types.Panel):
    bl_label = "CS2 Modding Suite"
    bl_idname = "OBJECT_PT_cs2_master_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CS2 Suite'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box_export = layout.box()
        box_export.label(text="Export 3D Model", icon='EXPORT')
        box_export.label(text="Separate By:")
        row_method = box_export.row()
        row_method.prop(scene, "cs2_export_method", expand=True)
        box_export.prop(scene, "cs2_use_reset_origin", text="Reset Origin", icon='OBJECT_ORIGIN')
        box_export.operator("object.cs2_exporter", text="Export to FBX", icon='MESH_CUBE')

        layout.separator()

        box_uv = layout.box()
        box_uv.label(text="Bake Windows UV Map", icon='UV')
        box_uv.label(text="Target By:")
        row_uv_method = box_uv.row()
        row_uv_method.prop(scene, "cs2_uv_target_method", expand=True)
        box_uv.label(text="Target Name:")
        row_uv_name = box_uv.row()
        row_uv_name.prop(scene, "cs2_uv_target_name", expand=True)
        row_uv = box_uv.row()
        row_uv.prop(scene, "cs2_grid_range_min", text="Min", icon='LIGHT_SUN')
        row_uv.prop(scene, "cs2_grid_range_max", text="Max", icon='OUTLINER_OB_LIGHT')
        box_uv.operator("object.cs2_bake_windows_uv", text="Generate UV Grid", icon='MOD_UVPROJECT')

        layout.separator()

        # --- SETUP SECTION ---
        box_setup = layout.box()
        box_setup.label(text="Material & Texture Setup", icon='NODE_MATERIAL')
        box_setup.prop(scene, "autobake_prefix", text="Prefix", icon='OUTLINER_DATA_FONT')
        
        row_size = box_setup.row()
        row_size.prop(scene, "cs2_tex_size", expand=True)
        
        box_setup.operator("object.cs2_setup_materials", text="Setup Materials", icon='MOD_BUILD')

        layout.separator()

        # --- BAKE SECTION ---
        box_bake = layout.box()
        box_bake.label(text="Run Baker", icon='SHADING_RENDERED')
        
        row_maps = box_bake.row()
        row_maps.prop(scene, "bake_do_basecolor", text="Base", icon='COLOR')
        row_maps.prop(scene, "bake_do_normal", text="Normal", icon='NORMALS_VERTEX')
        row_maps.prop(scene, "bake_do_maskmap", text="Mask", icon='TEXTURE')
        
        box_bake.operator("object.batch_bake_cs2", text="Bake Atlas", icon='RENDER_STILL')


# ==========================================
# MODULE 5: REGISTRATION
# ==========================================
classes = (
    OBJECT_OT_cs2_exporter,
    OBJECT_OT_cs2_bake_windows_uv,
    OBJECT_OT_cs2_setup_materials,
    OBJECT_OT_BatchBakeCS2,
    OBJECT_PT_cs2_master_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.cs2_export_method = bpy.props.EnumProperty(
        name="Export Method",
        description="Choose how to split the mesh",
        items=[
            ('VGROUP', "Vertex Groups", "", 'GROUP_VERTEX', 1),
            ('MATERIAL', "Materials", "", 'MATERIAL', 2)
        ],
        default='VGROUP'
    )
    
    bpy.types.Scene.cs2_uv_target_method = bpy.props.EnumProperty(
        name="Target Method",
        items=[
            ('VGROUP', "Vertex Groups", "", 'GROUP_VERTEX', 1),
            ('MATERIAL', "Materials", "", 'MATERIAL', 2)
        ],
        default='VGROUP'
    )
    bpy.types.Scene.cs2_uv_target_name = bpy.props.EnumProperty(
        name="Target Name",
        items=[
            ('WIN', "Win", "", 'WINDOW', 1),
            ('WIM', "Wim", "", 'SHADING_TEXTURE', 2),
            ('BOTH', "Both", "", 'FILE_BLEND', 3)
        ],
        default='WIN'
    )
    
    bpy.types.Scene.cs2_tex_size = bpy.props.EnumProperty(
        name="Size",
        description="Resolution of generated textures",
        items=[
            ('512', "512", ""),
            ('1024', "1024", ""),
            ('2048', "2048", ""),
            ('4096', "4096", "")
        ],
        default='2048'
    )
    
    bpy.types.Scene.cs2_use_reset_origin = bpy.props.BoolProperty(name="Reset Origin", default=False)
    bpy.types.Scene.cs2_grid_range_min = bpy.props.IntProperty(name="Brightest", default=0, min=0, max=24)
    bpy.types.Scene.cs2_grid_range_max = bpy.props.IntProperty(name="Darkest", default=24, min=0, max=24)
    bpy.types.Scene.autobake_prefix = bpy.props.StringProperty(name="Prefix", default="")
    bpy.types.Scene.bake_do_basecolor = bpy.props.BoolProperty(name="Color", default=True)
    bpy.types.Scene.bake_do_normal = bpy.props.BoolProperty(name="Normal", default=True)
    bpy.types.Scene.bake_do_maskmap = bpy.props.BoolProperty(name="Mask", default=True)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.cs2_export_method
    del bpy.types.Scene.cs2_uv_target_method
    del bpy.types.Scene.cs2_uv_target_name
    del bpy.types.Scene.cs2_tex_size
    del bpy.types.Scene.cs2_use_reset_origin
    del bpy.types.Scene.cs2_grid_range_min
    del bpy.types.Scene.cs2_grid_range_max
    del bpy.types.Scene.autobake_prefix
    del bpy.types.Scene.bake_do_basecolor
    del bpy.types.Scene.bake_do_normal
    del bpy.types.Scene.bake_do_maskmap

if __name__ == "__main__":
    register()