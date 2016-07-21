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

bl_info = {
    "name": "Fastener Factory",
    "author": "Aaron Keith, worlddevelopment",
    "version": (3, 9),
    "blender": (2, 6, 3),
    "location": "View3D > Add > Mesh",
    "description": "Add a fastener",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Add_Mesh/BoltFactory",
    "tracker_url": "http://github.com/faerietree/add_mesh_fastener",
    "category": "Add Mesh"}

if "bpy" in locals():
    import imp
    imp.reload(Boltfactory)
else:
    from . import Boltfactory
    #sys.modules[__name__] for properties or something like glob

import bpy
from bpy.props import (
                       PointerProperty,
                       )


################################################################################
##### REGISTER #####

def add_mesh_bolt_button(self, context):
    self.layout.operator(Boltfactory.MESH_OT_add_fastener.bl_idname, text="Bolt", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_mesh_add.append(add_mesh_bolt_button)
    #bpy.types.VIEW3D_PT_tools_objectmode.prepend(add_mesh_bolt_button) #just for testing
    bpy.types.Object.fastener_settings = PointerProperty(type=Boltfactory.FastenerSettings)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_mesh_add.remove(add_mesh_bolt_button)
    #bpy.types.VIEW3D_PT_tools_objectmode.remove(add_mesh_bolt_button) #just for testing

    del bpy.types.Object.fastener_settings


if __name__ == "__main__":
    register()
