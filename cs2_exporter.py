import bpy
import os
import math
import random
import mathutils

# == Addon Info ==

bl_info = {
    "name": "CS2 Exporter",
    "author": "DanOkami",
    "version": (1, 2),
    "blender": (4, 5, 1),
    "location": "View3D > Sidebar > CS2 Exporter",
    "description": "Esporta automaticamente mesh separate per vertex group in FBX per Cities Skylines II",
    "category": "Object"
}

# == Functions ==
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

    print("Reset Origin:", bpy.context.scene.cs2_use_reset_origin)

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

    model_name = f'{obj.name}'
    model_name = obj.name.split('_')[0]

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    for group in obj.vertex_groups:

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects[obj.name].select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate(linked=False)
        new_model = bpy.context.active_object

        if group.name == "Base":
            new_model.name = f'{model_name}'
        else: new_model.name = f'{model_name}_{group.name}'

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.vertex_group_set_active(group=group.name)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='VERT')

        bpy.ops.object.mode_set(mode='OBJECT')
        new_model.vertex_groups.clear()
        separated_objects.append(new_model)
        bpy.ops.object.select_all(action='DESELECT')

    print(f"\nSeparated Objects:\n{separated_objects}")
    obj.select_set(True)
    bpy.ops.object.delete()
    return separated_objects

# === BAKING WINDOWS UV MAP == #
def bakeWindowsUV(operator, context):
    operator.report({'INFO'}, "Starting to bake right now")
    
    if bpy.context.mode != "OBJECT":
        operator.report({'WARNING'}, "Mode must be \"OBJECT\"")
        return
    
    active = bpy.context.active_object
    if not active or active.type != 'MESH':
        operator.report({'WARNING'}, "Select a valid mesh")
        return

    if "Win" not in [vg.name for vg in active.vertex_groups]:
        operator.report({'WARNING'}, "Vertex group Win not found")
        return
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    vg_index = active.vertex_groups["Win"].index
    mesh = active.data
    
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        uv_layer = mesh.uv_layers[0]

    uv_layer_data = uv_layer.data 
    
    verts_in_group = {v.index for v in mesh.vertices if vg_index in [g.group for g in v.groups]}
    
    for v in mesh.vertices:
        v.select = False
        
    for v in mesh.vertices:
        if vg_index in [g.group for g in v.groups]:
            v.select = True
            
    for poly in mesh.polygons:
        poly.select = False
        
    for poly in mesh.polygons:
        if all(mesh.vertices[v].select for v in poly.vertices):
            poly.select = True
            
    selected_polygons = [poly for poly in mesh.polygons if poly.select]
    
    random.shuffle(selected_polygons)
    
    UV_grid = [[[] for _ in range(5)] for _ in range(5)]
    
    for poly in selected_polygons:
        r = random.randint(0, 4)
        c = random.randint(0, 4)
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

                # 🔹 Mantieni il rapporto d’aspetto
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


# === MAIN ===
def main():
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

    separated_objects = separate_by_vertex_groups(copy)

    print(f"\nObjects Separated!!!\n{separated_objects}")

    for obj in separated_objects:
        file_path = os.path.join(folder_path, f"{obj.name}.fbx")
        export_model_fbx(obj, file_path)

    clean_up(separated_objects)
    bpy.context.view_layer.objects.active = original
    original.name = original.name.split("_Original")[0]

# == Plugin HUD ==

# == RESET ORIGIN BUTTON ==
bpy.types.Scene.cs2_use_reset_origin = bpy.props.BoolProperty(
    name="Reset Origin",
    description="Reset the origin if not needed",
    default=False
)

bpy.types.Scene.cs2_simple_asset_export = bpy.props.BoolProperty(
    name="Simple Export",
    description="Exports simple Assets, not complex ones like buildings",
    default=False
)

# == FBX EXPORTER ==
class OBJECT_OT_cs2_exporter_experimental(bpy.types.Operator):
    bl_idname = "object.cs2_exporter"
    bl_label = "Export"
    def execute(self, context):
        main()
        self.report({'INFO'}, "Export started")
        return {'FINISHED'}

# == WINDOWS UV BAKE ==
bpy.types.Scene.cs2_grid_range_min = bpy.props.IntProperty(
    name="Min Range",
    description="Range of lights",
    default=1,
    min=1,
    max=25
)

bpy.types.Scene.cs2_grid_range_max = bpy.props.IntProperty(
    name="Max Range",
    description="Range of lights",
    default=25,
    min=1,
    max=25
)

class OBJECT_OT_cs2_bake_windows_uv(bpy.types.Operator):
    bl_idname = "object.cs2_bake_windows_uv"
    bl_label = "Bake Windows UV"
    def execute(self, context):
        bakeWindowsUV(self, context)
        self.report({'INFO'}, "Baking finished")
        return {'FINISHED'}

# == PANEL ==
class OBJECT_PT_simple_panel(bpy.types.Panel):
    bl_label = "CS2 FBX Exporter - Experimental"
    bl_idname = "OBJECT_PT_simple_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CS2 Exporterer - Experimental'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("object.cs2_exporter")
        layout.label(text="Enable if you want to reset the origin")
        layout.prop(scene, "cs2_use_reset_origin", toggle=True)
        
        layout.label(text="Windows settings")
        layout.operator("object.cs2_bake_windows_uv")

def register():
    bpy.utils.register_class(OBJECT_OT_cs2_exporter_experimental)
    bpy.utils.register_class(OBJECT_PT_simple_panel)
    bpy.utils.register_class(OBJECT_OT_cs2_bake_windows_uv)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_cs2_exporter_experimental)
    bpy.utils.unregister_class(OBJECT_PT_simple_panel)
    bpy.utils.unregister_class(OBJECT_OT_cs2_bake_windows_uv)
    del bpy.types.Scene.cs2_use_reset_origin

if __name__ == "__main__":
    register()