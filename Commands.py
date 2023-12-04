# -*- coding: utf-8 -*-

import os
import FreeCADGui as Gui
import FreeCAD
from PySide import QtGui
import Mesh
import json

_icondir_ = os.path.join(os.path.dirname(__file__), 'resources')

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

# デバッグ用 不要になったらコメントアウトする
# import ptvsd
# print("Waiting for debugger attach")
# # 5678 is the default attach port in the VS Code debug configurations
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()