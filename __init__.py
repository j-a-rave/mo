import bpy
from bpy.types import Menu
from bpy.props import *

from mo import mo

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
        global capture
        capture.stop()
        capture = None
        return {'FINISHED'}


class PMoMainPanel(bpy.types.Panel):
    bl_label = "MO"
    bl_idname = "MO_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MO"
    bl_context = "objectmode"

    def draw(self, context):
        obj = context.active_object

        layout = self.layout
        col = layout.column()
        row = col.row(align=True)
        row.label(text="MO Test")
        row = col.row(align=True)
        if capture is None:
            row.operator('mo.start_capture', text="Start Capture")
        else:
            row.operator('mo.stop_capture', text="Stop Capture")
            for key, value in capture.get_data().items():
                row = col.row(align=True)
                row.label(text=str(key) + ": " + str(value))


blender_classes = [
    OMoStartCapture,
    OMoStopCapture,
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


def unregister():
    for c in reversed(blender_classes):
        bpy.utils.unregister_class(c)

