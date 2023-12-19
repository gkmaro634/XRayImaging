# -*- coding: utf-8 -*-
import FreeCAD
import Part
import Mesh
import os
import json
import numpy as np

class ComponentsStore():
    def __init__(self, subjectsStore, lightSource, detector) -> None:
        self.subjectsStore = subjectsStore
        self.lightSource = lightSource
        self.detector = detector

    def SaveAsJson(self, dirpath):
        d = {}

        # condition
        d['WindowSize'] = [512, 512]

        # LightSource
        d['Source'] = self._get_lightsource_dict(self.lightSource)

        # Detector
        d['Detector'] = self._get_detector_dict(self.detector)

        # Subjects
        d['Polygons'] = []
        filepath_d = self.subjectsStore.SaveAsStl(dirpath)
        for fpath, subject in filepath_d.items():
            subject_d = self._get_subject_dict(fpath, subject)
            d['Polygons'].append(subject_d)

        json_fpath = os.path.join(dirpath, "converted.json")
        with open(json_fpath, "w") as f:
            json.dump(d, f)
        return json_fpath

    def _get_subject_dict(self, fpath, subject):
        d = {}
        d['SampleType'] = 'Polygon'
        d['Label'] = subject.Label
        d['Path'] = fpath
        d['LengthUnit'] = 'mm'
        d['Material'] = {}
        d['Material']['Type'] = subject.ElementType
        d['Material']['Element'] = subject.Element
        d['Material']['Density'] = subject.Density
        d['Type'] = 'inner'
        pos = subject.LinkedObject.Placement.Base
        d['Translate'] = [pos.x, pos.y, pos.z]
        axis = subject.LinkedObject.Placement.Rotation.Axis
        d['RotateAxis'] = [axis.x, axis.y, axis.z]
        angle_rad = subject.LinkedObject.Placement.Rotation.Angle
        d['RotateAngle'] = np.rad2deg(angle_rad)
        return d

    def _get_lightsource_dict(self, lightsource):
        d = {}
        pos = lightsource.Shape.CenterOfGravity
        d["Position"] = [pos.x, pos.y, pos.z]
        d["LengthUnit"] = "mm"
        d["Shape"] = "PointSource"
        d["Beam"] = {}
        d["Beam"]["Energy"] = lightsource.Energy
        d["Beam"]["Unit"] = lightsource.EnergyUnit
        d["Beam"]["PhotonCount"] = lightsource.aNumberOfPhotons
        return d

    def _get_detector_dict(self, detector):
        d = {}
        pos = detector.Shape.CenterOfGravity
        d["Position"] = [pos.x, pos.y, pos.z]
        d["LengthUnit"] = "mm"
        vec = detector.UpVector
        d["UpVector"] = [vec.x, vec.y, vec.z]
        col = int(detector.Width / detector.ColumnPixelSpacing)
        row = int(detector.Height / detector.RowPixelSpacing)
        d["NumberOfPixels"] = [col, row]
        d["Spacing"] = [detector.ColumnPixelSpacing, detector.RowPixelSpacing]
        return d


class SubjectStore():
    def __init__(self, subjects) -> None:
        self.subjects = subjects

    def SaveAsStl(self, dirpath):
        # PartごとにSTLに変換してファイル出力し、Subjectとファイスパスの辞書を返す
        filepath_d = {}
        file_index = 0
        for subject in self.subjects:
            stl_fname = f'{file_index:02}.stl'
            stl_fpath = os.path.join(dirpath, stl_fname)
            try:
                self.export_as_stl(subject.LinkedObject, stl_fpath)
                filepath_d[stl_fpath] = subject
                file_index += 1
            except Exception as ex:
                FreeCAD.Console.PrintMessage(f"{ex}\n")
        return filepath_d

    def export_as_stl(self, part, filepath):
        try:
            mesh = Mesh.Mesh()
            mesh.addFacets(part.Shape.tessellate(0.1))
            mesh.write(filepath)
            FreeCAD.Console.PrintMessage(f"Convertion successful. Save to {filepath}.\n")
        except Exception as ex:
            raise ex

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
