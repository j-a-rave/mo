import bpy
from bpy.types import Menu
from bpy.props import *

from mo import mo

capture = None


def stop_capture():
    global capture
    if capture is not None:
        capture.stop()
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


def update_show_camera(prop, context):
    print("huh")
    capture.set_show_camera(prop.get('show_camera'))


def update_track_head(prop, context):
    capture.set_track_head(prop.get('track_head'))


def update_track_emotions(prop, context):
    capture.set_track_emotions(prop.get('track_emotions'))


class PGMoSettings(bpy.types.PropertyGroup):
    show_camera: bpy.props.BoolProperty(name="Show Camera",
                                        default=True,
                                        update=update_show_camera)
    track_head: bpy.props.BoolProperty(name="Track Head",
                                       default=True,
                                       update=update_track_head)
    track_emotions: bpy.props.BoolProperty(name="Track Emotions",
                                           default=True,
                                           update=update_track_emotions)


class PMoMainPanel(bpy.types.Panel):
    bl_label = "MO"
    bl_idname = "MO_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MO"
    bl_context = "objectmode"

    def draw(self, context):
        obj = context.active_object
        mo_settings = context.scene.mo_settings

        layout = self.layout
        col = layout.column()
        row = col.row(align=True)
        row.label(text="MO Test")
        row = col.row(align=True)
        if capture is None:
            row.operator('mo.start_capture', text="Start Capture")
            return
        row.operator('mo.stop_capture', text="Stop Capture")

        row = col.row(align=True)
        row.operator('mo.calibrate', text="Calibrate")

        grid = col.grid_flow(columns=3, align=True)
        grid.prop(mo_settings, 'show_camera', icon='VIEW_CAMERA', text='')
        grid.prop(mo_settings, 'track_head', icon='OBJECT_ORIGIN', text='')
        grid.prop(mo_settings, 'track_emotions', icon='FUND', text='')


blender_classes = [
    OMoStartCapture,
    OMoStopCapture,
    OMoCalibrate,
    PGMoSettings,
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

    bpy.types.Scene.mo_settings = PointerProperty(type=PGMoSettings)


def unregister():
    stop_capture()
    for c in reversed(blender_classes):
        bpy.utils.unregister_class(c)

