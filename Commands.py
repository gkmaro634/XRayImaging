# -*- coding: utf-8 -*-

import os
import FreeCADGui as Gui
import FreeCAD
from PySide import QtGui
from libs.FreeCADComponents import ComponentsStore, SubjectStore, Subject, Detector, LightSource, ViewProviderDetector, ViewProviderLightSource

_icondir_ = os.path.join(os.path.dirname(__file__), 'resources')

class ConvertSubjectCommand():
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
            if hasattr(part, "Proxy") and part.Proxy and part.Proxy.Type:
                if part.Proxy.Type == "Subject":
                    FreeCAD.Console.PrintMessage(f"already converted.\n")
                    continue

                elif part.Proxy.Type == "LightSource":
                    FreeCAD.Console.PrintMessage(f"no need to convert.\n")
                    continue

                elif part.Proxy.Type == "Detector":
                    FreeCAD.Console.PrintMessage(f"no need to convert.\n")
                    continue

            # 変換済みのPartを指定した場合は無視
            unique_label = f"s_{part.Label}{part.ID}"
            if FreeCAD.ActiveDocument.getObject(unique_label):
                FreeCAD.Console.PrintMessage(f"already converted.\n")
                continue

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
        return {'Pixmap'  : os.path.join(_icondir_, 'convert.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'ConvertSubject',
                'ToolTip' : 'Convert a part as a subject model.' }               

    def prepare(self):
        self.convertable_parts = []

    def process_object(self, obj):
        if obj.isDerivedFrom("Part::Feature"):
            # FreeCAD.Console.PrintMessage(f"This is convertable.\n")
            self.convertable_parts.append(obj)

        # 子要素を再帰的に処理する
        elif hasattr(obj, 'Group') and obj.Group:
            for child in obj.Group:
                self.process_object(child)

class CreateOpticalSystemCommand():

    def __init__(self) -> None:
        self.lightsource_name = f"LightSource"
        self.detector_name = f"Detector"

    def Activated(self):
        '''Will be called when the feature is executed.'''

        # カスタムPartを生成
        if FreeCAD.ActiveDocument.getObject(self.lightsource_name) is None:
            ls_fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", self.lightsource_name)
            LightSource(ls_fp)
            ViewProviderLightSource(ls_fp.ViewObject)

        if FreeCAD.ActiveDocument.getObject(self.detector_name) is None:
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
        return {'Pixmap'  : os.path.join(_icondir_, 'ls_and_detector.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'CreateOpticalSystem',
                'ToolTip' : 'Create a light source and a detector.' }               

class AcquireXRayImageCommand():
    '''This class will be loaded when the workbench is activated in FreeCAD. You must restart FreeCAD to apply changes in this class'''  

    def __init__(self) -> None:
        pass

    def Activated(self):
        '''Will be called when the feature is executed.'''

        # 出力先フォルダを決める
        folder_path = self.get_folder_path()
        if folder_path == None:
            FreeCAD.Console.PrintMessage(f"Aborted.")
            return

        FreeCAD.Console.PrintMessage(f"Selected folder: {folder_path}.\n")

        # Subjectを探索する
        r = FreeCAD.ActiveDocument.findObjects("Part::FeaturePython")
        subjects = [fp for fp in r if fp.Proxy.Type == "Subject"]
        if len(subjects) <= 0:
            FreeCAD.Console.PrintMessage(f"Subjects are not found.\n")
            return

        # 構成部品をJsonファイル化する
        ls = FreeCAD.ActiveDocument.getObject("LightSource")
        det = FreeCAD.ActiveDocument.getObject("Detector")
        subjectsStore = SubjectStore(subjects)
        componentsStore = ComponentsStore(subjectsStore, ls, det)
        json_path = componentsStore.SaveAsJson(folder_path)

        # X線画像出力部にJsonパスを渡す
        try:
            import libs.gvxrEngine as gvxrEx
            import matplotlib.pyplot as plt
            import numpy as np

            gvxrComponents = gvxrEx.Composition.CreateFromJson(json_path)
            gvxrEngine = gvxrEx.Engine()
            xray_img, screen_img = gvxrEngine.Shot(gvxrComponents)

            xray_fpath = os.path.join(folder_path, "xrayimage.tiff")
            print(f"Save xray image. {xray_fpath}")
            plt.imsave(xray_fpath, xray_img, cmap='gray')
            FreeCAD.Console.PrintMessage(f"Save xray image: {xray_fpath}.\n")

            screen_fpath = os.path.join(folder_path, "screenshot.png")
            print(f"Save screenshot. {screen_fpath}")
            plt.imsave(screen_fpath, np.array(screen_img))
            FreeCAD.Console.PrintMessage(f"Save screenshot image: {screen_fpath}.\n")

        except Exception as ex:
            FreeCAD.Console.PrintMessage(ex)

    def IsActive(self):
        '''Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional.'''
        
        # 
        if FreeCAD.ActiveDocument is None:
            return False
        
        if FreeCAD.ActiveDocument.getObject("LightSource") is None:
            return False

        if FreeCAD.ActiveDocument.getObject("Detector") is None:
            return False
        
        return True
        
    def GetResources(self):
        '''Return the icon which will appear in the tree view. This method is optional and if not defined a default icon is shown.'''
        return {'Pixmap'  : os.path.join(_icondir_, 'acq_image.svg'),
                'Accel' : '', # a default shortcut (optional)
                'MenuText': 'AcquireXRayImage',
                'ToolTip' : 'Acquire an x-ray image' }               
    
    def get_folder_path(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.Directory)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            folder_path = dialog.selectedFiles()[0]
            return folder_path
        else:
            return None
    
Gui.addCommand('CreateOpticalSystem', CreateOpticalSystemCommand())
Gui.addCommand('ConvertSubject', ConvertSubjectCommand())
Gui.addCommand('AcquireXRayImage', AcquireXRayImageCommand())

# デバッグ用 不要になったらコメントアウトする
# import ptvsd
# print("Waiting for debugger attach")
# # 5678 is the default attach port in the VS Code debug configurations
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()