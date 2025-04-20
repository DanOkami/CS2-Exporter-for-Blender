import bpy
import os
import math

# == Addon Info ==

bl_info = {
    "name": "CS2 Exporter",
    "author": "DanOkami",
    "version": (1, 0),
    "blender": (3, 5, 0),
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
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0, 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    obj.rotation_euler = (math.radians(-90), 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    obj.scale = (100, 100, 100)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
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

import bpy

class OBJECT_OT_cs2_exporter(bpy.types.Operator):
    bl_idname = "object.cs2_exporter"
    bl_label = "Export"

    def execute(self, context):
        main()
        self.report({'INFO'}, "Export started")
        return {'FINISHED'}

class OBJECT_PT_simple_panel(bpy.types.Panel):
    bl_label = "CS2 FBX Exporter"
    bl_idname = "OBJECT_PT_simple_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CS2 Exporterer'

    def draw(self, context):
        layout = self.layout

        layout.label(text="Select the object that you")
        layout.label(text="want to export, then")
        layout.label(text="click the button below.")
        layout.label(text="The model will be exported")
        layout.label(text="in the same folder")
        layout.label(text="as your Blender file.")

        layout.operator("object.cs2_exporter")

def register():
    bpy.utils.register_class(OBJECT_OT_cs2_exporter)
    bpy.utils.register_class(OBJECT_PT_simple_panel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_cs2_exporter)
    bpy.utils.unregister_class(OBJECT_PT_simple_panel)

if __name__ == "__main__":
    register()
