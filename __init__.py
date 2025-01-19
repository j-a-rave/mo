import bpy
from bpy.props import *

from mo import mo

capture = None


def stop_capture():
    global capture
    if capture is not None:
        capture.stop()
        ctrl_obj = bpy.context.scene.mo_settings.control_object
        if ctrl_obj is not None:
            ctrl_obj.delta_location = (0, 0, 0)
            ctrl_obj.delta_rotation_euler = (0, 0, 0)
        capture = None


class OMoStartCapture(bpy.types.Operator):
    bl_idname = 'mo.start_capture'
    bl_label = "MO Start Capture"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return capture is None

    def execute(self, context):
        global capture
        capture = mo.MoCaptureManager()
        capture.start()
        return {'FINISHED'}


class OMoStopCapture(bpy.types.Operator):
    bl_idname = 'mo.stop_capture'
    bl_label = "MO Stop Capture"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return capture is not None

    def execute(self, context):
        stop_capture()
        return {'FINISHED'}


class OMoCalibrate(bpy.types.Operator):
    bl_idname = 'mo.calibrate'
    bl_label = "MO Cailbrate"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return capture is not None

    def execute(self, context):
        capture.calibrate()
        return {'FINISHED'}


class PMoMainPanel(bpy.types.Panel):
    bl_label = "MO"
    bl_idname = "MO_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MO"
    bl_context = "objectmode"

    def draw(self, context):
        mo_settings = context.scene.mo_settings

        layout = self.layout
        col = layout.column()

        row = col.row(align=True)
        row.prop(mo_settings, 'control_object', text="Control Object")

        grid = col.grid_flow(columns=4, align=True)
        grid.prop(mo_settings, 'show_camera', icon='VIEW_CAMERA', text='')
        grid.prop(mo_settings, 'track_head', icon='OBJECT_ORIGIN', text='')
        grid.prop(mo_settings, 'track_emotions', icon='MESH_MONKEY', text='')
        grid.prop(mo_settings, 'absolute_position', icon='TRANSFORM_ORIGINS', text='')

        row = col.row(align=True)
        row.prop(mo_settings, 'pos_scale', text="Position Scale")

        row = col.row(align=True)
        row.prop(mo_settings, 'rot_scale', text="Rotation Scale")

        row = col.row(align=True)
        if capture is None:
            row.operator('mo.start_capture', text="Start Capture")
            return
        row.operator('mo.stop_capture', text="Stop Capture")

        row = col.row(align=True)
        row.operator('mo.calibrate', text="Calibrate")


blender_classes = [
    OMoStartCapture,
    OMoStopCapture,
    OMoCalibrate,
    mo.PGMoSettings,
    mo.PGMoData,
    PMoMainPanel,
]


bl_info = {
    "name": "Mo",
    "blender": (4, 0, 0),
    "category": "Tracking"
}


def register():
    for c in blender_classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.mo_settings = PointerProperty(type=mo.PGMoSettings)
    bpy.types.Object.mo_data = PointerProperty(type=mo.PGMoData)


def unregister():
    stop_capture()
    for c in reversed(blender_classes):
        bpy.utils.unregister_class(c)

