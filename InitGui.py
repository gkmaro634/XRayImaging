# -*- coding: utf-8 -*-
__title__ = 'FreeCAD XRayImaging Workbench - Init file'
__author__ = 'Kazuma Goto'
__url__ = ['http://www.freecadweb.org']
__doc__ = 'XRayImaging Workbench workbench'
__version__ = '0.0.1'

import FreeCADGui as Gui
import FreeCAD

class XRayImagingWorkbench (Workbench):
    def __init__(self):
        import os
        import XRayImagingWorkbench
        self.__class__.MenuText = 'XRayImaging'
        self.__class__.ToolTip = 'XRayImaging'
        self.__class__.Icon = os.path.join(XRayImagingWorkbench.get_module_path(), 'template_resource.svg')

    def Initialize(self):
        '''This function is executed when FreeCAD starts'''
        import Commands
        
        self.list = ['Export(stl files)', "CreateSubject"]
        self.menu = self.list
        self.appendToolbar(self.__class__.MenuText, self.list)
        self.appendMenu(self.__class__.MenuText, self.menu)

    def Activated(self):
        '''This function is executed when the workbench is activated'''
        FreeCAD.Console.PrintMessage(f"Activated.\n")
        return

    def Deactivated(self):
        '''This function is executed when the workbench is deactivated'''
        FreeCAD.Console.PrintMessage(f"Deactivated.\n")
        return

    def ContextMenu(self, recipient):
        '''This is executed whenever the user right-clicks on screen'''

    def GetClassName(self):
        # this function is mandatory if this is a full python workbench
        return 'Gui::PythonWorkbench'
    
Gui.addWorkbench(XRayImagingWorkbench())