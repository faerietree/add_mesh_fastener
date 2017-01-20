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

from .createMesh import *
from .preset_utils import *




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


def iso888_calculate_thread_length(nominal_diameter, length):
    if nominal_diameter <= 125:
        thread_length = 2 * nominal_diameter + 6
    elif nominal_diameter <= 200:
        thread_length = 2 * nominal_diameter + 12
    else:
        thread_length = 2 * nominal_diameter + 25
    # Shank length too small? (also follows iso 888):
    if length - thread_length <= nominal_diameter / 2:
        return length  # fully threaded
    return thread_length


def load_settings_from_preset_cb(self, context):
    # prevent recursive call
    if load_settings_from_preset_cb.level == False:
        load_settings_from_preset_cb.level = True
        settings = self
        print("load_settings_from_preset_cb: ", self)

        if settings.bf_preset != 'custom.py' and (not settings.last_preset or settings.bf_preset != settings.last_preset):
            # If it is not custom,then standards ISO225,888 are respected.
            #print("setting preset: ", settings.bf_preset)
            #print("presetsPath: ", settings.presetsPath)
            update_manually_previous = settings.update_manually
            settings.update_manually = True

            settings.bf_Length = 0.0
            settings.bf_Thread_Length = 0.0
            settings.bf_Shank_Length = 0.0
            setProps(settings, settings.bf_preset, settings.presetsPath)

            # Derive some properties:
            print('Preset Length: ' + str(settings.bf_Length))
            update_lengths(settings, context, force=True)

            # Derive more properties:
            settings.bf_Phillips_Bit_Depth = float(Get_Phillips_Bit_Height(settings.bf_Philips_Bit_Dia))
            #settings.bf_Philips_Bit_Dia = settings.bf_Pan_Head_Dia*(1.82/5.6)
            #settings.bf_Minor_Dia = settings.bf_Major_Dia - (1.082532 * settings.bf_Pitch)

            # Store this preset as previous preset
            settings.last_preset = settings.bf_preset
            settings.update_manually = update_manually_previous
            if not settings.update_manually:
                bpy.ops.mesh.fastener_update()

        load_settings_from_preset_cb.level = False

load_settings_from_preset_cb.level = False


#def is_instance_of_one_or_classes(obj, classes)
#def is_within_properties_to_detect_out_of_sync_of(obj):
#    print(obj.__class__, " ==? ", type(obj))
#    return isinstance(obj, (IntProperty,FloatProperty,StringProperty,EnumProperty,BoolProperty)
#        )
property_keys_to_exclude_from_out_of_sync_detection = [
        'rna'
        ,
        ]

def are_settings_out_of_sync(settings, context):
    #for key,s in settings.__dict__.iteritems():
    prop_keys_candidates = [p_key for p_key in dir(settings) if not p_key.startswith('__') and not p_key.endswith('List') and p_key.startswith("bf_") and not callable(getattr(settings,p_key))]
    is_out_of_sync = False
    # Important: Finish this loop to have checked every property once because else when aborting then the next time this method returns out of sync again while it has been fully synced for sure when the update operator is run!
    prop_keys = []
    for p_key in prop_keys_candidates:
        p_value = getattr(settings, p_key)
        #print("p key: ", p_key, " => ", p_value)
        #print("p type: ", type(p_value))
        #if not is_within_properties_to_detect_out_of_sync_of(p_value):
        if p_value in property_keys_to_exclude_from_out_of_sync_detection:
            print("Property is excluded from out of sync detection. Skipping ...")
            continue
        prop_keys.append(p_key)
        if not p_key in are_settings_out_of_sync.prop_key_to_value_map:
            #print("Not stored yet. Marking for storing.")
            is_out_of_sync = True
        elif are_settings_out_of_sync.prop_key_to_value_map[p_key] != p_value:
            #print("Value changed from %s to %s. Marking for update." % (are_settings_out_of_sync.prop_key_to_value_map[p_key], p_value))
            is_out_of_sync = True
    # Do not store anything if nothing is out of sync:
    if not is_out_of_sync:
        return False
    # Else store all new prop values to be sure:
    for p_key in prop_keys:
        p_value = getattr(settings, p_key)
        if not p_key in are_settings_out_of_sync.prop_key_to_value_map or are_settings_out_of_sync.prop_key_to_value_map[p_key] != p_value:
            #print("storing new property value: ", p_key)
            are_settings_out_of_sync.prop_key_to_value_map[p_key] = p_value
    return True

are_settings_out_of_sync.prop_key_to_value_map = {}


# Custom settings
def update_settings_cb(self, context):
    #print("update_settings_cb")
    # prevent recursive call
    if update_settings_cb.level == False:
        if not are_settings_out_of_sync(self, context):
            print("Settings not out of sync. Doing nothing.")
            return
        update_settings_cb.level = True
        settings = self
        #settings.bf_preset = 'custom.py'

        if not settings.update_manually:
            bpy.ops.mesh.fastener_update()

        update_settings_cb.level = False

update_settings_cb.level = False


#
# Two distinct functions because blender Property callbacks require
# exactly two arguments.
#
def update_lengths_cb(self, context):
    update_lengths(self, context)


def update_lengths(self, context, force=False):
    print('update_lengths')
    # prevent recursive call:settings
    if update_lengths.level == False:
        if not force and not are_settings_out_of_sync(self, context):
            print("Settings not out of sync. Doing nothing.")
            return
        print('update_lengths heavy lifting')
        update_lengths.level = True

        settings = self
        update_manually_previous = settings.update_manually
        settings.update_manually = True

        print('Length:' + str(settings.bf_Length))
        if settings.bf_Length != 0:
            # Derive thread, shank lengths
            # ISO 888: Dimensions for thread lengths calculation:
            settings.bf_Thread_Length = iso888_calculate_thread_length(settings.bf_Major_Dia, settings.bf_Length)
            settings.bf_Shank_Length = settings.bf_Length - settings.bf_Thread_Length
        # Support specifying thread, shank lengths instead of overall length:
        else:
            # Derive bf_Length
            if settings.bf_Thread_Length != 0 or settings.bf_Shank_Length != 0:
                # Thread, shank lengths are given
                print("Thread, shank lengths are given in preset '%s'." % (settings.bf_preset))
                settings.bf_Length = settings.bf_Thread_Length + settings.bf_Shank_Length
            else:
                print("Error: Neither thread, shank lengths nor the sum of both (bf_Length) specified in preset '%s'." % (settings.bf_preset))
                # Log but prevent enabling manual update return None

        settings.update_manually = update_manually_previous
        # React on changed thread | shank lengths:
        if not settings.update_manually:
            bpy.ops.mesh.fastener_update()

    update_lengths.level = False

update_lengths.level = False


MAX_INPUT_NUMBER = 500
class FastenerSettings(PropertyGroup):
    """Parameters of the fastener"""  # Tooltip

    update_manually = BoolProperty(
            default = False
            ,description = "If enabled apply settings manually instead of realtime update."
            ,name = "Update manually"
            #,update = update_settings_cb
    )

    # Model Types
    bf_Model_Type_List = [
            ('bf_Model_Bolt','BOLT',"Bolt Model")
            ,('bf_Model_Nut','NUT',"Nut Model")
            ]
    bf_Model_Type = EnumProperty(
            default = 'bf_Model_Bolt'
            ,description = "Choose a type of model"
            ,items = bf_Model_Type_List
            ,name = "Model"
            ,update = update_settings_cb
            )
    # Head Types
    bf_Head_Type_List = [
            ('bf_Head_Hex','HEX','Hex Head')
            ,('bf_Head_Cap','CAP','Cap Head')
            ,('bf_Head_Dome','DOME','Dome Head')
            ,('bf_Head_Pan','PAN','Pan Head')
            ,('bf_Head_Square','SQUARE','Square Head')
            ,('bf_Head_CounterSink','COUNTER SINK','Counter Sink Head')
            ]
    bf_Head_Type = EnumProperty(
            default = 'bf_Head_Hex'
            ,description = 'Type of Head'
            ,items = bf_Head_Type_List
            ,name = 'Head Type'
            ,update = update_settings_cb
            )

    # Bit Types
    Bit_Type_List = [
            ('bf_Bit_None','NONE','No Bit Type')
            ,('bf_Bit_Allen','ALLEN','Allen Bit Type')
            ,('bf_Bit_Philips','PHILLIPS','Phillips Bit Type')
            ]
    bf_Bit_Type = EnumProperty(
            default = 'bf_Bit_None'
            ,description = 'Type of bit'
            ,items = Bit_Type_List
            ,name = 'Bit Type'
            ,update = update_settings_cb
            )

    # Nut Types
    Nut_Type_List = [
            ('bf_Nut_Hex','HEX','Hex Nut')
            ,('bf_Nut_Square','SQUARE','Square Nut')
            ,('bf_Nut_Lock','LOCK','Lock Nut')
            ]
    bf_Nut_Type = EnumProperty(
            default = 'bf_Nut_Hex'
            ,description = 'Type of nut'
            ,items = Nut_Type_List
            ,name = 'Nut Type'
            ,update = update_settings_cb
            )

    # Shank Types
    #TODO Support reduced shanks in createMesh, then add type select to GUI.
    Shank_Type_List = [
            ('bf_Shank_Full', 'FULL', 'Full')
            ,('bf_Shank_Reduced', 'REDUCED', 'Reduced')
            ,('bf_Shank_Reduced_Conically', 'REDUCED_CONICALLY', 'Conically reduced')
            ]
    bf_Shank_Type = EnumProperty(
            default = 'bf_Shank_Full'
            ,description = 'Type of shank'
            ,items = Shank_Type_List
            ,name = 'Shank Type'
            ,update = update_settings_cb
            )


    # Parameters:
    # Head
    bf_Hex_Head_Height = FloatProperty(
            default = 2
            ,description = 'Height of the Hex Head'
            ,name = 'Head Height'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,update = update_settings_cb
            )
    bf_Hex_Head_Flat_Distance = FloatProperty(
            default = 5.5
            ,description = 'Flat Distance of the Hex Head'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Flat Dist'
            ,update = update_settings_cb
            )
    bf_CounterSink_Head_Dia = FloatProperty(
            default = 5.5
            ,description = 'Diameter of the Counter Sink Head'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Head Dia'
            ,update = update_settings_cb
            )
    bf_Cap_Head_Height = FloatProperty(
            default = 5.5
            ,description = 'Height of the Cap Head'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Head Height'
            ,update = update_settings_cb
            )
    bf_Cap_Head_Dia = FloatProperty(
            default = 3
            ,description = 'Diameter of the Cap Head'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Head Dia'
            ,update = update_settings_cb
            )
    bf_Dome_Head_Dia = FloatProperty(
            default = 5.6
            ,description = 'Diameter of the Dome Head'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Dome Head Dia'
            ,update = update_settings_cb
            )
    bf_Pan_Head_Dia = FloatProperty(
            default = 5.6
            ,description = 'Diameter of the Pan Head'
            ,min = 0,soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Pan Head Dia'
            ,update = update_settings_cb
            )

    # Bit
    bf_Phillips_Bit_Depth = FloatProperty(
            default = 0 #set in execute
            ,description = 'Depth of the Phillips Bit'
            ,min = 0, soft_min = 0,max = MAX_INPUT_NUMBER
            ,name = 'Bit Depth'
            ,options = {'HIDDEN'} #gets calculated in execute
            ,update = update_settings_cb
            )
    bf_Allen_Bit_Depth = FloatProperty(
            default = 1.5
            ,description = 'Depth of the Allen Bit'
            ,min = 0, soft_min = 0,max = MAX_INPUT_NUMBER
            ,name = 'Bit Depth'#
            ,update = update_settings_cb
            )
    bf_Allen_Bit_Flat_Distance = FloatProperty(
            default = 2.5
            ,description = 'Flat Distance of the Allen Bit'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Flat Dist'
            ,update = update_settings_cb
            )
    bf_Philips_Bit_Dia = FloatProperty(
            default = 0 #set in execute
            ,description = 'Diameter of the Philips Bit'
            ,min = 0, soft_min = 0,max = MAX_INPUT_NUMBER
            ,name = 'Bit Dia'
            ,options = {'HIDDEN'} #gets calculated in execute
            ,update = update_settings_cb
            )

    # Shank
    bf_Length = FloatProperty(
            default = 0
            ,description = 'Shank length + Thread length'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Length l'
            ,update = update_lengths_cb
            )
    bf_Shank_Length = FloatProperty(
            default = 0
            ,description = 'Length of the unthreaded shank'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Shank Length'
            ,update = update_settings_cb
            )
    bf_Shank_Dia = FloatProperty(
            default = 3
            ,description = 'Diameter of the shank'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Shank Dia'
            ,update = update_settings_cb
            )
    bf_Thread_Length = FloatProperty(
            default = 6
            ,description = 'Length of the Thread'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Thread Length'
            ,update = update_settings_cb
            )

    # Thread
    bf_Major_Dia = FloatProperty(
            default = 3
            ,description = 'Outside diameter of the Thread'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Major Dia'
            ,update = update_settings_cb
            )
    bf_Pitch = FloatProperty(
            default = 0.35
            ,description = 'Pitch of the thread'
            ,min = 0.1, soft_min = 0.1, max = 30.0
            ,name = 'Pitch'
            ,update = update_settings_cb
            )
    bf_Minor_Dia = FloatProperty(
            default = 0 #set in execute
            ,description = 'Inside diameter of the Thread'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Minor Dia'
            ,options = {'HIDDEN'} #gets calculated in execute
            ,update = update_settings_cb
            )
    bf_Crest_Percent = IntProperty(
            default = 10
            ,description = 'Percent of the pitch that makes up the Crest'
            ,min = 1, soft_min = 1, max = 90
            ,name = 'Crest Percent'
            ,update = update_settings_cb
            )
    bf_Root_Percent = IntProperty(
            default = 10
            ,description = 'Percent of the pitch that makes up the Root'
            ,min = 1, soft_min = 1, max = 90
            ,name = 'Root Percent'
            ,update = update_settings_cb
            )

    # Nut
    bf_Hex_Nut_Height = FloatProperty(
            default = 2.4
            ,description = 'Height of the Hex Nut'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Hex Nut Height'
            ,update = update_settings_cb
            )
    bf_Hex_Nut_Flat_Distance = FloatProperty(
            default = 5.5
            ,description = 'Flat distance of the Hex Nut'
            ,min = 0, soft_min = 0, max = MAX_INPUT_NUMBER
            ,name = 'Hex Nut Flat Dist'
            ,update = update_settings_cb
            )

    # preset
    presets, presetsPath = getPresets()

    bf_preset = EnumProperty(
            default = 'M06.py'
            ,description = "Use Preset from File"
            ,items = presets
            ,name = 'Preset'
            ,update = load_settings_from_preset_cb
            )

    last_preset = None



class OBJECT_PT_Fastener(Panel):
    bl_label = "Fastener settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    def draw(self, context):
        global shank_length_row
        global thread_length_row
        global length_row

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
        #Nut
        if settings.bf_Model_Type == 'bf_Model_Nut':
            col.prop(settings, 'bf_Nut_Type')
            col.prop(settings, 'bf_Hex_Nut_Height')
            col.prop(settings, 'bf_Hex_Nut_Flat_Distance')
            col.separator()
        #Thread
        col.label(text='Thread')
        col.prop(settings, 'bf_Major_Dia')
        col.prop(settings, 'bf_Minor_Dia')
        col.prop(settings, 'bf_Pitch')
        col.prop(settings, 'bf_Crest_Percent')
        col.prop(settings, 'bf_Root_Percent')
        if settings.bf_Model_Type == 'bf_Model_Bolt':
            thread_length_row = col.row()
            thread_length_row.prop(settings, 'bf_Thread_Length')
            thread_length_row.active = True
            col.separator()
            #Shank
            col.label(text='Shank')
            col.prop(settings, 'bf_Shank_Dia')
            shank_length_row = col.row()
            shank_length_row.prop(settings, 'bf_Shank_Length')
            shank_length_row.active = True
            if settings.bf_preset != 'custom.py':
                length_row = col.row()
                length_row.prop(settings, 'bf_Length')
                length_row.active = True
                shank_length_row.active = False
                thread_length_row.active = False

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


    ##### PROPERTIES
    align_matrix = mathutils.Matrix()


    ##### POLL #####
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene != None


    ##### EXECUTE #####
    def execute(self, context):
        print('EXECUTING add fastener ...')
        scene = context.scene

        # Create new object
        name = "Fastener"
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene.
        scene.objects.link(obj)
        scene.objects.active = obj
        scene.objects.active.select

        # Place the object at the 3D cursor location.
        # apply viewRotation
        obj.matrix_world = self.align_matrix
        # Apply location of new object after having set the view's align matrix.
        scene.update()

        return bpy.ops.mesh.fastener_update()


    def invoke(self, context, event):
        print("\n___________INVOKE Fastener add_____________")
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}



class MESH_OT_update_fastener(bpy.types.Operator):
    """"""
    bl_idname = "mesh.fastener_update"
    bl_label = "Update fastener"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Update fasteners like bolts, screws, nuts."


    ##### METHODS
    @classmethod
    def poll(cls, context):
        scene = context.scene
        obj_active = scene.objects.active
        return scene != None and obj_active != None


    def execute(self, context):
        print('EXECUTING update fastener ...')
        obj = context.scene.objects.active
        settings = obj.fastener_settings

        Create_New_Mesh(settings, context)

        return {'FINISHED'}



