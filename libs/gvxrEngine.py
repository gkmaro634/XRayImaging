#!/usr/bin/env python3
import numpy as np
from typing import List, Tuple, Dict
from gvxrPython3 import gvxr
import json
import time

class PointLightSource:
    position = np.r_[0, 0, 0]
    x = 0
    y = 0
    z = 0
    energy = 100
    n_photons = 1000
    lengthUnit = "mm"
    energyUnit = "keV"

    def __init__(self, position, energy, n_photones) -> None:
        self.position = position
        self.energy = energy
        self.n_photons = n_photones
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]

class Detector:
    position = np.r_[0, 0, 0]
    x = 0
    y = 0
    z = 0

    upVector = np.r_[0, 0, 0]
    vx = 0
    vy = 0
    vz = 0

    width = 640# px
    height = 320# px
    colSpacing = 0.5
    rowSpacing = 0.5

    lengthUnit = "mm"

    def __init__(self, position, upVector, width, height, colSpacing, rowSpacing) -> None:
        self.position = position
        self.upVector = upVector
        self.width = width
        self.height = height
        self.colSpacing = colSpacing
        self.rowSpacing = rowSpacing

        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.vx = upVector[0]
        self.vy = upVector[1]
        self.vz = upVector[2]

class Sample:
    label = ""
    elementType = "element"
    element = "Fe"
    density = 1.
    translate = np.r_[0,0,0]
    tx = 0
    ty = 0
    tz = 0
    rotate = np.r_[0,0,1]
    rotateAngle = 0
    rx = 0
    ry = 0
    rz = 1
    scale = np.r_[1,1,1]
    sx = 1.
    sy = 1.
    sz = 1.
    lengthUnit = "mm"
    densityUnit = "g/cm3"

    def __init__(self, label,elementType, element, density) -> None:
        self.label = label
        self.elementType = elementType
        self.element = element
        self.density = density

    def Translate(self, translate) -> None:
        self.translate = translate
        self.tx = translate[0]
        self.ty = translate[1]
        self.tz = translate[2]

    def Rotate(self, rotate, rotateAngle) -> None:
        self.rotate = rotate
        self.rotateAngle = rotateAngle
        self.rx = rotate[0]
        self.ry = rotate[1]
        self.rz = rotate[2]
    
    def Scale(self, scale) -> None:
        self.scale = scale
        self.sx = scale[0]
        self.sy = scale[1]
        self.sz = scale[2]

class Polygon(Sample):
    stlFilePath = ""

    def __init__(self, label, elementType, element, density, stlFilePath) -> None:
        super().__init__(label, elementType, element, density)
        self.stlFilePath = stlFilePath
        pass

class Cylinder(Sample):
    height = 1.
    radius = 0.5
    nSector = 10
    
    def __init__(self, label, elementType, element, density, height, radius) -> None:
        super().__init__(label, elementType, element, density)
        self.height = height
        self.radius = radius
        pass

class Composition:
    lightSource = None
    detector = None
    subjects = None

    def __init__(self, lightSource:PointLightSource, detector:Detector, subjects:List[Sample]) -> None:
        self.lightSource = lightSource
        self.detector = detector
        self.subjects = subjects

    def CreateFromJson(jsonPath:str):
        with open(jsonPath, 'rt', encoding='utf-8-sig') as f:
            # buff = f.readlines()
            d = json.load(f)

        lightSource = PointLightSource(np.array(d['Source']['Position']), d['Source']['Beam']['Energy'], d['Source']['Beam']['PhotonCount'])
        detector = Detector(np.array(d['Detector']['Position']), np.array(d['Detector']['UpVector']), d['Detector']['NumberOfPixels'][0], d['Detector']['NumberOfPixels'][1], d['Detector']['Spacing'][0], d['Detector']['Spacing'][1])
        samples = []
        if 'Cylinders' in d.keys():
            for sampleDict in d['Cylinders']:
                cylinder = Cylinder(sampleDict['Label'], sampleDict['Material']['Type'], sampleDict['Material']['Element'], sampleDict['Material']['Density'], sampleDict['Height'], sampleDict['Radius'])
                cylinder.Translate(np.array(sampleDict['Translate']))
                cylinder.Rotate(np.array(sampleDict['RotateAxis']), sampleDict['RotateAngle'])
                samples.append(cylinder)

        if 'Polygons' in d.keys():
            for sampleDict in d['Polygons']:
                polygon = Polygon(sampleDict['Label'], sampleDict['Material']['Type'], sampleDict['Material']['Element'], sampleDict['Material']['Density'], sampleDict['Path'])
                polygon.Translate(np.array(sampleDict['Translate']))
                polygon.Rotate(np.array(sampleDict['RotateAxis']), sampleDict['RotateAngle'])
                samples.append(polygon)

        composition = Composition(lightSource, detector, samples)
        return composition

        
class Engine:
    windowId = 0

    def __init__(self) -> None:
        self.windowId = 0
        pass

    def Shot(self, composition:Composition):
        return self._shot(composition.lightSource, composition.detector, composition.subjects)

    def _shot(self, lightSource:PointLightSource, detector:Detector, samples:List[Sample]):
        self.windowId += 1
        gvxr.createOpenGLContext(self.windowId)

        gvxr.clearDetectorEnergyResponse()
        gvxr.removePolygonMeshesFromSceneGraph()
        gvxr.removePolygonMeshesFromXRayRenderer()

        # light source
        gvxr.setSourcePosition(lightSource.x, lightSource.y, lightSource.z, lightSource.lengthUnit)
        gvxr.usePointSource()
        gvxr.setMonoChromatic(lightSource.energy, lightSource.energyUnit, lightSource.n_photons)

        # detector
        gvxr.setDetectorPosition(detector.x, detector.y, detector.z, detector.lengthUnit)
        gvxr.setDetectorUpVector(detector.vx, detector.vy, detector.vz)
        gvxr.setDetectorNumberOfPixels(detector.width, detector.height)
        gvxr.setDetectorPixelSize(detector.colSpacing, detector.rowSpacing, detector.lengthUnit)

        for sample in samples:
            if isinstance(sample, Polygon):
                self._setPolygon(sample)
            elif isinstance(sample, Cylinder):
                self._setCylinder(sample)
                pass

            # 平行移動、回転、拡大縮小
            gvxr.translateNode(sample.label, sample.tx, sample.ty, sample.tz, sample.lengthUnit)
            if np.linalg.norm(sample.rotate) > 0:
                gvxr.rotateNode(sample.label, sample.rotateAngle, sample.rx, sample.ry, sample.rz)
            gvxr.scaleNode(sample.label, sample.sx, sample.sy, sample.sz)

            if sample.elementType.upper() == "ELEMENT":
                # 単一元素の場合
                gvxr.setElement(sample.label, sample.element)
            elif sample.elementType.upper() == "COMPOUND":
                # 分子の場合
                gvxr.setCompound(sample.label, sample.element)
                gvxr.setDensity(sample.label, sample.density, sample.densityUnit)
            elif sample.elementType.upper() == "MIXTURE":
                # 合金の場合
                gvxr.setMixture(sample.label, sample.element)
                gvxr.setDensity(sample.label, sample.density, sample.densityUnit)
            else:
                gvxr.setCompound(sample.label, "H2O")
                gvxr.setDensity(sample.label, 1.0, sample.densityUnit)

        # compute xray image
        xrayimage = gvxr.computeXRayImage()

        gvxr.setWindowBackGroundColour(0.25, 0.25, 0.25, self.windowId)
        gvxr.displayScene(False, self.windowId)
        gvxr.displayScene(False, self.windowId)
        screenshot = gvxr.takeScreenshot(self.windowId)
        gvxr.destroyWindow(self.windowId)

        return (xrayimage, screenshot)
    
    def Close(self):
        gvxr.destroyAllWindows()
        return

    def _setPolygon(self, polygon:Polygon):
        # STLからメッシュを読み込む場合
        gvxr.loadMeshFile(polygon.label, polygon.stlFilePath, polygon.lengthUnit)
        gvxr.moveToCenter(polygon.label)
        pass

    def _setCylinder(self, cylinder:Cylinder):
        gvxr.makeCylinder(cylinder.label, cylinder.nSector, cylinder.height, cylinder.radius, cylinder.lengthUnit)
        gvxr.addPolygonMeshAsInnerSurface(cylinder.label)
        gvxr.moveToCenter(cylinder.label)
        pass