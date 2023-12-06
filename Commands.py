# -*- coding: utf-8 -*-

import os
import FreeCADGui as Gui
import FreeCAD
from PySide import QtGui
import Mesh
import json

_icondir_ = os.path.join(os.path.dirname(__file__), 'resources')

class Subject():
    def __init__(self, fp, base) -> None:
        self.Type = "Subject"
        fp.addProperty("App::PropertyLink", "LinkedObject", "Custom", "FreeCAD object to be subject").LinkedObject = base
        # fp.addProperty("App::PropertyString", "UniqueLabel", "Custom", "Label must be unique").UniqueLabel = label
        fp.addProperty("App::PropertyEnumeration", "ElementType", "Custom", "ElementType").ElementType = ["Element", "Compound", "Mixture"]
        fp.addProperty("App::PropertyString", "Element", "Custom", "Element. This property is effective only if the ElementType is Element.").Element = "Fe" # TODO: Selectable from ["Fe", "C",,,and more]
        fp.addProperty("App::PropertyFloat", "Density", "Custom", "Density[g/cm^3]. This property is effective only if the ElementType is Compound or Mixture.").Density = 1.0
        # fp.addProperty("App::PropertyVectorDistance", "Translate", "Base", "Translate").Translate = base.Placement.Base
        # fp.addProperty("App::PropertyRotation", "Rotation", "Base", "Rotation").Rotation = base.Placement.Rotation

        fp.Placement = base.Placement
        fp.setPropertyStatus("Placement", "ReadOnly")
        fp.setPropertyStatus("Label", "ReadOnly")
        # fp.setPropertyStatus("UniqueLabel", "Hidden") # set "-Hidden" to visible
        fp.setPropertyStatus("LinkedObject", "ReadOnly")
        fp.Proxy = self
        # self.original_object = obj
        # if hasattr(obj, "CustomProperty") == False:
        #     obj.addProperty("App::PropertyString", "CustomProperty", "MyObject", "A custom property.")
        # pass

    def execute(self, obj):
        """
        Called on document recompute
        """        
        print("Hoge")

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

# デバッグ用 不要になったらコメントアウトする
# import ptvsd
# print("Waiting for debugger attach")
# # 5678 is the default attach port in the VS Code debug configurations
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()