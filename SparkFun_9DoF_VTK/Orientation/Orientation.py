import os, sys
import vtk
import serial
import numpy as np

class IMU():
    def __init__(self, xLength=10, yLength=10, zLength=0.1):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(xLength)
        cube.SetYLength(yLength)
        cube.SetZLength(zLength)
        cube.Update()
        
        arrow = vtk.vtkArrowSource()
        arrow.SetTipResolution(6)
        arrow.SetTipRadius(0.1)
        arrow.SetTipLength(0.35)
        arrow.SetShaftResolution(6)
        arrow.SetShaftRadius(0.03)
        arrow.Update()
        
        transform = vtk.vtkTransform()
        transform.RotateY(-90)
        transform.Update()
        
        transform_pdf = vtk.vtkTransformPolyDataFilter()
        transform_pdf.SetInputData(arrow.GetOutput())
        transform_pdf.SetTransform(transform)
        transform_pdf.Update()
        
        self.imu = vtk.vtkAppendPolyData()
        self.imu.AddInputData(cube.GetOutput())
        self.imu.AddInputData(transform_pdf.GetOutput())
        self.imu.Update()
        
        self.transform = vtk.vtkTransform()
        self.transform_pdf = vtk.vtkTransformPolyDataFilter()
        
        # set up vtk polydata mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.transform_pdf.GetOutput())
        mapper.SetColorModeToDefault()
        
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(mapper)
        

class HandleIMUSerialData():
    def __init__(self, renderer=None, serial_port="/dev/ttyACM0", baudrate=230400):
        self.renderer = renderer
        self.port = serial_port
        self.baud = baudrate
        
        self.serial = serial.Serial(port=self.port, baudrate=self.baud)
        
        self.roll = None
        self.pitch = None
        self.yaw = None
        
    def parseSerialData(self):
        readSerialPort = True
        
        if self.serial.is_open:
            while readSerialPort:
                b = self.serial.readline()
                string = b.decode()
                
                components = string.split(", ")
                self.roll = float(components[3])
                self.pitch = float(components[4])
                self.yaw = -float(components[5])
                print("Roll: {0}, Pitch: {1}, Yaw: {2}".format(self.roll, self.pitch, self.yaw))
                readSerialPort = False
        
    def execute(self, obj, event):
        imu = IMU()
        self.renderer.AddActor(imu.vtkActor)
        
        self.parseSerialData()
        
        if self.roll and self.pitch and self.yaw:
            imu.transform.RotateX(self.roll)
            imu.transform.RotateY(self.pitch)
            imu.transform.RotateZ(self.yaw)
            imu.transform.Update()
            
            imu.transform_pdf.SetInputData(imu.imu.GetOutput())
            imu.transform_pdf.SetTransform(imu.transform)
            imu.transform_pdf.Update()
            
            obj.GetRenderWindow().Render()
            self.renderer.RemoveActor(imu.vtkActor)


class KeyBoardInterrupt(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, HandleIMUSerial):
        self.serialInfo = HandleIMUSerial
    
    def execute(self, obj, event):
        if self.obj.GetKeySym() == 'q':
            print(sys.stderr, "Pressed key: %s" % key)
            self.serialInfo.serial.close()
            obj.GetRenderWindow().Finalize()
            obj.TerminateApp()


def main():
    camera = vtk.vtkCamera()
    camera.SetPosition(0, 0, 45)
    camera.SetFocalPoint(0, 0, 0)
    
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0., 0., 0.)
    renderer.SetActiveCamera(camera)
    
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(1000, 1000)
    
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.Initialize()
    
    axes = vtk.vtkAxesActor()
    orientation = vtk.vtkOrientationMarkerWidget()
    orientation.SetOutlineColor(0.93, 0.57, 0.13)
    orientation.SetOrientationMarker(axes)
    orientation.SetInteractor(renderWindowInteractor)
    orientation.SetViewport(0.0, 0.0, 0.4, 0.4)
    orientation.SetEnabled(True)
    orientation.InteractiveOn()
    
    handleIMUSerial = HandleIMUSerialData(renderer)
    style = KeyBoardInterrupt(handleIMUSerial)
    renderWindowInteractor.SetInteractorStyle(style)
    renderWindowInteractor.AddObserver('TimerEvent', handleIMUSerial.execute)
    renderWindowInteractor.AddObserver('TerminatingEvent', style.execute)
    timerId = renderWindowInteractor.CreateRepeatingTimer(1)
    
    renderWindow.Render()
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()
