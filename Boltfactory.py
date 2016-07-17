# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
import mathutils
from bpy.types import Panel, Operator, Scene, PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       PointerProperty,
                       BoolProperty
                       )

from add_mesh_BoltFactory.createMesh import *
from add_mesh_BoltFactory.preset_utils import *



##------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = mathutils.Matrix.Translation(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
    else:
        rot = mathutils.Matrix()
    align_matrix = loc * rot
    return align_matrix


def update_settings_cb(self, context):
    # annoying workaround for recursive call
    if update_settings_cb.level == False:
        update_settings_cb.level = True
        settings = self

        if not settings.last_preset or settings.bf_preset != settings.last_preset:
            #print("setting preset: ", settings.bf_preset)
            setProps(settings, settings.bf_preset, settings.presetsPath)
            settings.bf_Phillips_Bit_Depth = float(Get_Phillips_Bit_Height(settings.bf_Philips_Bit_Dia))

            settings.last_preset = settings.bf_preset

        #settings.bf_Phillips_Bit_Depth = float(Get_Phillips_Bit_Height(settings.bf_Philips_Bit_Dia))
        #settings.bf_Philips_Bit_Dia = settings.bf_Pan_Head_Dia*(1.82/5.6)
        #settings.bf_Minor_Dia = settings.bf_Major_Dia - (1.082532 * settings.bf_Pitch)


        if not settings.update_manually:
            bpy.ops.mesh.fastener_update()

        update_settings_cb.level = False

update_settings_cb.level = False



MAX_INPUT_NUMBER = 500
class FastenerSettings(PropertyGroup):
    """Parameters of the fastener"""  # Tooltip

    update_manually = BoolProperty(
            name="Update manually"
            ,description="If enabled apply settings manually instead of realtime update."
            ,default=False
            ,update=update_settings_cb
    )

    # Model Types
    bf_Model_Type_List = [('bf_Model_Bolt','BOLT',"Bolt Model"),
                        ('bf_Model_Nut','NUT',"Nut Model")]
    bf_Model_Type = EnumProperty( attr='bf_Model_Type',
            name="Model",
            description="Choose a type of model",
            items = bf_Model_Type_List, default = 'bf_Model_Bolt'
            ,update=update_settings_cb
            )
    # Head Types
    bf_Head_Type_List = [('bf_Head_Hex','HEX','Hex Head'),
                        ('bf_Head_Cap','CAP','Cap Head'),
                        ('bf_Head_Dome','DOME','Dome Head'),
                        ('bf_Head_Pan','PAN','Pan Head'),
                        ('bf_Head_CounterSink','COUNTER SINK','Counter Sink Head')]
    bf_Head_Type = EnumProperty( attr='bf_Head_Type',
            name='Head Type',
            description='Type of Head',
            items = bf_Head_Type_List, default = 'bf_Head_Hex'
            ,update=update_settings_cb
            )

    # Bit Types
    Bit_Type_List = [('bf_Bit_None','NONE','No Bit Type'),
                    ('bf_Bit_Allen','ALLEN','Allen Bit Type'),
                    ('bf_Bit_Philips','PHILLIPS','Phillips Bit Type')]
    bf_Bit_Type = EnumProperty( attr='bf_Bit_Type',
            name='Bit Type',
            description='Type of bit',
            items = Bit_Type_List, default = 'bf_Bit_None'
            ,update=update_settings_cb
            )

    # Nut Types
    Nut_Type_List = [('bf_Nut_Hex','HEX','Hex Nut'),
                    ('bf_Nut_Lock','LOCK','Lock Nut')]
    bf_Nut_Type = EnumProperty( attr='bf_Nut_Type',
            name='Nut Type',
            description='Type of nut',
            items = Nut_Type_List, default = 'bf_Nut_Hex'
            ,update=update_settings_cb
            )

    # Shank Types
    bf_Shank_Length = FloatProperty(
            name='Shank Length', default = 0,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank'
            ,update=update_settings_cb
            )

    bf_Shank_Dia = FloatProperty(attr='bf_Shank_Dia',
            name='Shank Dia', default = 3,
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the shank'
            ,update=update_settings_cb
            )

    bf_Phillips_Bit_Depth = FloatProperty(attr='bf_Phillips_Bit_Depth',
            name='Bit Depth', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Phillips Bit'
            ,update=update_settings_cb
            )

    bf_Allen_Bit_Depth = FloatProperty(attr='bf_Allen_Bit_Depth',
            name='Bit Depth', default = 1.5,
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Allen Bit'
            ,update=update_settings_cb
            )

    bf_Allen_Bit_Flat_Distance = FloatProperty( attr='bf_Allen_Bit_Flat_Distance',
            name='Flat Dist', default = 2.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Allen Bit'
            ,update=update_settings_cb
            )

    bf_Hex_Head_Height = FloatProperty( attr='bf_Hex_Head_Height',
            name='Head Height', default = 2,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Hex Head'
            ,update=update_settings_cb
            )

    bf_Hex_Head_Flat_Distance = FloatProperty( attr='bf_Hex_Head_Flat_Distance',
            name='Flat Dist', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Hex Head'
            ,update=update_settings_cb
            )

    bf_CounterSink_Head_Dia = FloatProperty(
            name='Head Dia', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Diameter of the Counter Sink Head'
            ,update=update_settings_cb
            )

    bf_Cap_Head_Height = FloatProperty( attr='bf_Cap_Head_Height',
            name='Head Height', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Cap Head'
            ,update=update_settings_cb
            )

    bf_Cap_Head_Dia = FloatProperty( attr='bf_Cap_Head_Dia',
            name='Head Dia', default = 3,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Diameter of the Cap Head'
            ,update=update_settings_cb
            )

    bf_Dome_Head_Dia = FloatProperty( attr='bf_Dome_Head_Dia',
            name='Dome Head Dia', default = 5.6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank'
            ,update=update_settings_cb
            )

    bf_Pan_Head_Dia = FloatProperty( attr='bf_Pan_Head_Dia',
            name='Pan Head Dia', default = 5.6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Diameter of the Pan Head'
            ,update=update_settings_cb
            )

    bf_Philips_Bit_Dia = FloatProperty(attr='bf_Philips_Bit_Dia',
            name='Bit Dia', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the Philips Bit'
            ,update=update_settings_cb
            )

    bf_Thread_Length = FloatProperty( attr='bf_Thread_Length',
            name='Thread Length', default = 6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Length of the Thread'
            ,update=update_settings_cb
            )

    bf_Major_Dia = FloatProperty( attr='bf_Major_Dia',
            name='Major Dia', default = 3,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Outside diameter of the Thread'
            ,update=update_settings_cb
            )

    bf_Pitch = FloatProperty( attr='bf_Pitch',
            name='Pitch', default = 0.35,
            min = 0.1, soft_min = 0.1, max = 30.0,
            description='Pitch of the thread'
            ,update=update_settings_cb
            )

    bf_Minor_Dia = FloatProperty( attr='bf_Minor_Dia',
            name='Minor Dia', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Inside diameter of the Thread'
            ,update=update_settings_cb
            )

    bf_Crest_Percent = IntProperty( attr='bf_Crest_Percent',
            name='Crest Percent', default = 10,
            min = 1, soft_min = 1, max = 90,
            description='Percent of the pitch that makes up the Crest'
            ,update=update_settings_cb
            )

    bf_Root_Percent = IntProperty( attr='bf_Root_Percent',
            name='Root Percent', default = 10,
            min = 1, soft_min = 1, max = 90,
            description='Percent of the pitch that makes up the Root'
            ,update=update_settings_cb
            )

    bf_Hex_Nut_Height = FloatProperty( attr='bf_Hex_Nut_Height',
            name='Hex Nut Height', default = 2.4,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Hex Nut')

    bf_Hex_Nut_Flat_Distance = FloatProperty( attr='bf_Hex_Nut_Flat_Distance',
            name='Hex Nut Flat Dist', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat distance of the Hex Nut'
            ,update=update_settings_cb
            )

    presets, presetsPath = getPresets()

    bf_preset = EnumProperty(attr='bf_preset',
            name='Preset',
            description="Use Preset from File",
            default='M3.py',
            items=presets
            ,update=update_settings_cb
            )

    last_preset = None



class OBJECT_PT_Fastener(Panel):
    bl_label = "Fastener settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        scene = context.scene
        obj = context.active_object
        settings = obj.fastener_settings


        #ENUMS
        col.prop(settings, 'bf_Model_Type')
        col.prop(settings, 'bf_preset')
        col.separator()

        #Bit
        if settings.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(settings, 'bf_Bit_Type')
            if settings.bf_Bit_Type == 'bf_Bit_None':
                pass
            elif settings.bf_Bit_Type == 'bf_Bit_Allen':
                col.prop(settings, 'bf_Allen_Bit_Depth')
                col.prop(settings, 'bf_Allen_Bit_Flat_Distance')
            elif settings.bf_Bit_Type == 'bf_Bit_Philips':
                col.prop(settings, 'bf_Phillips_Bit_Depth')
                col.prop(settings, 'bf_Philips_Bit_Dia')
            col.separator()

        #Head
        if settings.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(settings, 'bf_Head_Type')
            if settings.bf_Head_Type == 'bf_Head_Hex':
                col.prop(settings, 'bf_Hex_Head_Height')
                col.prop(settings, 'bf_Hex_Head_Flat_Distance')
            elif settings.bf_Head_Type == 'bf_Head_Cap':
                col.prop(settings, 'bf_Cap_Head_Height')
                col.prop(settings, 'bf_Cap_Head_Dia')
            elif settings.bf_Head_Type == 'bf_Head_Dome':
                col.prop(settings, 'bf_Dome_Head_Dia')
            elif settings.bf_Head_Type == 'bf_Head_Pan':
                col.prop(settings, 'bf_Pan_Head_Dia')
            elif settings.bf_Head_Type == 'bf_Head_CounterSink':
                col.prop(settings, 'bf_CounterSink_Head_Dia')
            col.separator()
        #Shank
        if settings.bf_Model_Type == 'bf_Model_Bolt':
            col.label(text='Shank')
            col.prop(settings, 'bf_Shank_Length')
            col.prop(settings, 'bf_Shank_Dia')
            col.separator()
        #Nut
        if settings.bf_Model_Type == 'bf_Model_Nut':
            col.prop(settings, 'bf_Nut_Type')
            col.prop(settings, 'bf_Hex_Nut_Height')
            col.prop(settings, 'bf_Hex_Nut_Flat_Distance')
        #Thread
        col.label(text='Thread')
        if settings.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(settings, 'bf_Thread_Length')
        col.prop(settings, 'bf_Major_Dia')
        col.prop(settings, 'bf_Minor_Dia')
        col.prop(settings, 'bf_Pitch')
        col.prop(settings, 'bf_Crest_Percent')
        col.prop(settings, 'bf_Root_Percent')

        col.separator()
        col.prop(settings, "update_manually")
        if settings.update_manually:
            col.operator("mesh.fastener_update", icon='FILE_TICK', text="Update fastener")



class MESH_OT_add_fastener(bpy.types.Operator):
    """"""
    bl_idname = "mesh.fastener_add"
    bl_label = "Add fastener"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "Generate fasteners like bolts, screws, nuts."


    ##### POLL #####
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene != None


    ##### EXECUTE #####
    def execute(self, context):
        #print('EXECUTING...')
        scene = context.scene

        # Create new object
        name = "Fastener"
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene.
        scene.objects.link(obj)
        scene.objects.active = obj
        scene.objects.active.select

        return bpy.ops.mesh.fastener_update()



class MESH_OT_update_fastener(bpy.types.Operator):
    """"""
    bl_idname = "mesh.fastener_update"
    bl_label = "Update fastener"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Update fasteners like bolts, screws, nuts."


    ##### PROPERTIES
    align_matrix = mathutils.Matrix()


    ##### METHODS
    @classmethod
    def poll(cls, context):
        scene = context.scene
        obj_active = scene.objects.active
        return scene != None and obj_active != None


    def execute(self, context):
        #print('EXECUTING...')
        obj = context.scene.objects.active
        settings = obj.fastener_settings

        # Place the object at the 3D cursor location.
        # apply viewRotaion
        obj.matrix_world = self.align_matrix

        Create_New_Mesh(settings, context, self.align_matrix)

        return {'FINISHED'}


    def invoke(self, context, event):
        #print("\n___________START_____________")
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}

