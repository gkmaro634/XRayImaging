# -*- coding: utf-8 -*-

import os
import FreeCADGui as Gui
import FreeCAD
from PySide import QtGui
import Mesh
import json
import Part

_icondir_ = os.path.join(os.path.dirname(__file__), 'resources')

class Subject():
    def __init__(self, fp, base) -> None:
        self.Type = "Subject"
        fp.Proxy = self

        fp.addProperty("App::PropertyLink", "LinkedObject", "Custom", "FreeCAD object to be subject").LinkedObject = base
        # fp.addProperty("App::PropertyString", "UniqueLabel", "Custom", "Label must be unique").UniqueLabel = label
        fp.addProperty("App::PropertyEnumeration", "ElementType", "Custom", "ElementType").ElementType = ["Element", "Compound", "Mixture"]
        fp.addProperty("App::PropertyString", "Element", "Custom", "Element. This property is effective only if the ElementType is Element.").Element = "Fe" # TODO: Selectable from ["Fe", "C",,,and more]
        fp.addProperty("App::PropertyFloat", "Density", "Custom", "Density[g/cm^3]. This property is effective only if the ElementType is Compound or Mixture.").Density = 1.0
        # fp.addProperty("App::PropertyVectorDistance", "Translate", "Base", "Translate").Translate = base.Placement.Base
        # fp.addProperty("App::PropertyRotation", "Rotation", "Base", "Rotation").Rotation = base.Placement.Rotation

        fp.Placement = base.Placement
        fp.ElementType = "Element"
        fp.setPropertyStatus("Placement", "ReadOnly")
        fp.setPropertyStatus("Label", "ReadOnly")
        # fp.setPropertyStatus("UniqueLabel", "Hidden") # set "-Hidden" to visible
        fp.setPropertyStatus("LinkedObject", "ReadOnly")
        # if hasattr(obj, "CustomProperty") == False:
        #     obj.addProperty("App::PropertyString", "CustomProperty", "MyObject", "A custom property.")
        # pass

    def execute(self, obj):
        """
        Called on document recompute
        """
        if obj.ElementType == "Element":
            obj.setPropertyStatus("Density", "ReadOnly")
            obj.setPropertyStatus("Element", "-ReadOnly")
        else:
            obj.setPropertyStatus("Density", "-ReadOnly")
            obj.setPropertyStatus("Element", "ReadOnly")

class LightSource():
    def __init__(self, fp) -> None:
        self.Type = "LightSource"
        fp.Proxy = self

        fp.addProperty("App::PropertyFloat", "Energy", "Custom", "the incident photon energy").Energy = 1.0
        fp.addProperty("App::PropertyEnumeration", "EnergyUnit", "Custom", "the unit of energy corresponding to anEnergy.").EnergyUnit = ["eV", "keV", "MeV"]
        fp.addProperty("App::PropertyInteger", "aNumberOfPhotons", "Custom", "the number of incident photons.").aNumberOfPhotons = 1000

        fp.EnergyUnit = "keV"
        fp.setPropertyStatus("Label", "ReadOnly")

    def execute(self, obj):
        """
        Called on document recompute
        """        
        sphere = Part.makeSphere(1, FreeCAD.Vector(100, 0, 0), FreeCAD.Vector(1, 0, 0))
        obj.Shape = sphere

class Detector():
    def __init__(self, fp) -> None:
        self.Type = "Detector"
        fp.Proxy = self

        fp.addProperty("App::PropertyInteger", "Width", "Custom", "the number of pixels along the X-axis").Width = 60
        fp.addProperty("App::PropertyInteger", "Height", "Custom", "the number of pixels along the Y-axis").Height = 40
        fp.addProperty("App::PropertyFloat", "ColumnPixelSpacing", "Custom", "the pixel size along the X-axis").ColumnPixelSpacing = 1.0
        fp.addProperty("App::PropertyFloat", "RowPixelSpacing", "Custom", "the pixel size along the Y-axis").RowPixelSpacing = 1.0
        fp.addProperty("App::PropertyEnumeration", "UpVectorEdge", "Custom", "UpVectorEdge").UpVectorEdge = ["0", "1"]
        fp.addProperty("App::PropertyEnumeration", "UpVectorDirection", "Custom", "UpVectorDirection").UpVectorDirection = ["Positive", "Negative"]
        fp.addProperty("App::PropertyVector", "UpVector", "Custom", "the orientation of the X-ray detector.").UpVector = FreeCAD.Vector(0, 0, 1)
        # fp.addProperty("App::PropertyLink", "LinkedObject", "Custom", "FreeCAD object to be subject").LinkedObject = base

        # fp.EnergyUnit = "keV"
        fp.UpVectorEdge = "0"
        fp.UpVectorDirection = "Positive"
        fp.setPropertyStatus("Label", "ReadOnly")
        fp.setPropertyStatus("UpVector", "ReadOnly")

    def execute(self, obj):
        """
        Called on document recompute
        """        
        width = obj.Width * obj.ColumnPixelSpacing
        height = obj.Height * obj.RowPixelSpacing
        plane = Part.makePlane(height, width, FreeCAD.Vector(-100, width / 2, -height / 2), FreeCAD.Vector(1, 0, 0))
        obj.Shape = plane

        edges = obj.Shape.Edges
        upvector_edge = edges[int(obj.UpVectorEdge)]

        v1 = upvector_edge.Vertexes[0].Point
        v2 = upvector_edge.Vertexes[1].Point
        vec = v2 - v1 if obj.UpVectorDirection == "Positive"  else  v1 - v2
        print(vec)
        obj.UpVector = FreeCAD.Vector(vec.normalize())

class ViewProviderLightSource:

    def __init__(self, obj):
        """
        Set this object to the proxy object of the actual view provider
        """

        obj.Proxy = self

    def attach(self, obj):
        """
        Setup the scene sub-graph of the view provider, this method is mandatory
        """
        return

    def updateData(self, fp, prop):
        """
        If a property of the handled feature has changed we have the chance to handle this here
        """
        return

    def getDisplayModes(self,obj):
        """
        Return a list of display modes.
        """
        return []

    def getDefaultDisplayMode(self):
        """
        Return the name of the default display mode. It must be defined in getDisplayModes.
        """
        return "Shaded"

    def setDisplayMode(self,mode):
        """
        Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done.
        This method is optional.
        """
        return mode

    def onChanged(self, vp, prop):
        """
        Print the name of the property that has changed
        """

        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def getIcon(self):
        """
        Return the icon in XMP format which will appear in the tree view. This method is optional and if not defined a default icon is shown.
        """

        return

    def __getstate__(self):
        """
        Called during document saving.
        """
        return None

    def __setstate__(self,state):
        """
        Called during document restore.
        """
        return None

class ViewProviderDetector:

    def __init__(self, obj):
        """
        Set this object to the proxy object of the actual view provider
        """

        obj.Proxy = self

    def attach(self, obj):
        """
        Setup the scene sub-graph of the view provider, this method is mandatory
        """
        return

    def updateData(self, fp, prop):
        """
        If a property of the handled feature has changed we have the chance to handle this here
        """
        return

    def getDisplayModes(self,obj):
        """
        Return a list of display modes.
        """
        return []

    def getDefaultDisplayMode(self):
        """
        Return the name of the default display mode. It must be defined in getDisplayModes.
        """
        return "Shaded"

    def setDisplayMode(self,mode):
        """
        Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done.
        This method is optional.
        """
        return mode

    def onChanged(self, vp, prop):
        """
        Print the name of the property that has changed
        """

        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def getIcon(self):
        """
        Return the icon in XMP format which will appear in the tree view. This method is optional and if not defined a default icon is shown.
        """

        return

    def __getstate__(self):
        """
        Called during document saving.
        """
        return None

    def __setstate__(self,state):
        """
        Called during document restore.
        """
        return None

class CreateSubjectCommand():
    '''This class will be loaded when the workbench is activated in FreeCAD. You must restart FreeCAD to apply changes in this class'''  
    convertable_parts = []

    def __init__(self) -> None:
        self.prepare()

    def Activated(self):
        '''Will be called when the feature is executed.'''
        self.prepare()

        objects = Gui.Selection.getSelection()
        for obj in objects:
            self.process_object(obj)

        for part in self.convertable_parts:
            # カスタムPartを指定した場合は無視
            if hasattr(part, "Proxy"):
                if part.Proxy and part.Proxy.Type and part.Proxy.Type == "Subject":
                    FreeCAD.Console.PrintMessage(f"already converted.\n")
                    continue

            # 変換済みのPartを指定した場合は無視
            unique_label = f"s_{part.Label}{part.ID}"
            if FreeCAD.ActiveDocument.getObject(unique_label):
                FreeCAD.Console.PrintMessage(f"already converted.\n")

            # カスタムPartを生成
            fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", unique_label)
            Subject(fp, part)

        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        '''Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional.'''
        if FreeCAD.ActiveDocument is None:
            return False
        
        if Gui.Selection.getSelection() is None:
            return False
        
        return True
        
    def GetResources(self):
        '''Return the icon which will appear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return {'Pixmap'  : os.path.join(_icondir_, 'template_resource.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'Convert',
                'ToolTip' : 'Convert as a subject model.' }               

    def prepare(self):
        self.convertable_parts = []

    def process_object(self, obj):
        if obj.isDerivedFrom("Part::Feature"):
            FreeCAD.Console.PrintMessage(f"This is convertable.\n")
            self.convertable_parts.append(obj)
            # if hasattr(obj, "Hoge") == False:
            #     obj.addProperty("App::PropertyFloat", "Hoge", "Fuga", "Bar")

        # 子要素を再帰的に処理する
        elif hasattr(obj, 'Group') and obj.Group:
            for child in obj.Group:
                self.process_object(child)

class CreateLightSourceCommand():

    def __init__(self) -> None:
        self.lightsource_name = f"LightSource"
        self.detector_name = f"Detector"

    def Activated(self):
        '''Will be called when the feature is executed.'''

        # カスタムPartを生成
        ls_fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", self.lightsource_name)
        LightSource(ls_fp)
        ViewProviderLightSource(ls_fp.ViewObject)

        det_fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", self.detector_name)
        Detector(det_fp)
        ViewProviderDetector(det_fp.ViewObject)

        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        '''Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional.'''
        if FreeCAD.ActiveDocument is None:
            return False
        
        if FreeCAD.ActiveDocument.getObject(self.lightsource_name):
            # FreeCAD.Console.PrintMessage(f"already created.\n")
            return False
        
        return True
        
    def GetResources(self):
        '''Return the icon which will appear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return {'Pixmap'  : os.path.join(_icondir_, 'template_resource.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'LightSource',
                'ToolTip' : 'Create a light source.' }               

class ExportAsStlFilesCommand():
    '''This class will be loaded when the workbench is activated in FreeCAD. You must restart FreeCAD to apply changes in this class'''  
    convertable_parts = []
    file_index = 0
    converted_files = []

    def __init__(self) -> None:
        self.prepare()

    def Activated(self):
        '''Will be called when the feature is executed.'''

        # キャッシュ初期化
        self.prepare()

        # 出力先フォルダを決める
        folder_path = self.get_folder_path()
        if folder_path == None:
            FreeCAD.Console.PrintMessage(f"Aborted.")
            return

        FreeCAD.Console.PrintMessage(f"Selected folder: {folder_path}.\n")

        # 選択されたPartを特定する
        objects = Gui.Selection.getSelection()
        for obj in objects:
            self.process_object(obj)
        
        if len(self.convertable_parts) <= 0:
            FreeCAD.Console.PrintMessage(f"Convertable parts are not found.\n")
            return

        # PartごとにSTLに変換してファイル出力する
        for part in self.convertable_parts:
            stl_fname = f'{self.file_index:02}.stl'
            stl_fpath = os.path.join(folder_path, stl_fname)
            try:
                self.export_as_stl(part, stl_fpath)
                self.converted_files.append(stl_fpath)
                self.file_index += 1
            except Exception as ex:
                FreeCAD.Console.PrintMessage(f"{ex}\n")

        # 出力したファイルパスをJsonでファイル出力する
        d = {}
        d['Polygons'] = []
        for fpath in self.converted_files:
            stl_d = {}
            stl_d['SampleType'] = 'Polygon'
            stl_d['Label'] = 'unknown'
            stl_d['Path'] = fpath
            stl_d['LengthUnit'] = 'mm'
            # more properties...
            d['Polygons'].append(stl_d)

        json_fpath = os.path.join(folder_path, "converted.json")
        with open(json_fpath, "w") as f:
            json.dump(d, f)

    def IsActive(self):
        '''Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional.'''
        if FreeCAD.ActiveDocument and Gui.Selection.getSelection():
            return(True)
        else:
            return(False)
        
    def GetResources(self):
        '''Return the icon which will appear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return {'Pixmap'  : os.path.join(_icondir_, 'template_resource.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'Export(stl files)',
                'ToolTip' : 'Export pars as stl files.' }               
    
    def prepare(self):
        self.convertable_parts = []
        self.file_index = 0
        self.converted_files = []

    def process_object(self, obj):

        if obj.isDerivedFrom("Part::Feature"):
            # STLに変換して保存する
            FreeCAD.Console.PrintMessage(f"This is convertable.\n")
            self.convertable_parts.append(obj)

        # 子要素を再帰的に処理する
        elif hasattr(obj, 'Group') and obj.Group:
            for child in obj.Group:
                self.process_object(child)

    def get_folder_path(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            folder_path = dialog.selectedFiles()[0]
            return folder_path
        else:
            return None
    
    def export_as_stl(self, part, filepath):
        mesh = Mesh.Mesh()
        mesh.addFacets(part.Shape.tessellate(0.1))
        mesh.write(filepath)
        FreeCAD.Console.PrintMessage(f"Convertion successful. Save to {filepath}.\n")

Gui.addCommand('Export(stl files)', ExportAsStlFilesCommand())
Gui.addCommand('CreateSubject', CreateSubjectCommand())
Gui.addCommand('CreateLightSource', CreateLightSourceCommand())

# デバッグ用 不要になったらコメントアウトする
# import ptvsd
# print("Waiting for debugger attach")
# # 5678 is the default attach port in the VS Code debug configurations
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()