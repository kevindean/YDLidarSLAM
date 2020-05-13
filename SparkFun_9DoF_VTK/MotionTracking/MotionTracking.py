# there are still some drift issues to take into account... for instance, when the IMU is at a specific orientation,
# it should not be able to calculate a dx, dy, dz (should be 0 for each -> this is where a neural network given the 
# correct gyro / accelerometer input data could come into affect to determine the "true" dx, dy, dz

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
        
        self.t0 = None
        self.ax = None
        self.ay = None
        self.az = None
        
        self.ax0 = 0
        self.ay0 = 0
        self.az0 = 0
        
        self.ax_offset = -0.00419
        self.ay_offset = -0.049625999999999997
        self.az_offset = 1.0251899999999998
        
        self.vx_offset = 0.0002568599999999679
        self.vy_offset = 0.0033434800000000054
        self.vz_offset = -0.0005150200000000538
        
        self.dx = None
        self.dy = None
        self.dz = None
        
        self.x = 0
        self.y = 0
        self.z = 0
        
    def parseSerialData(self):
        readSerialPort = True
        
        if self.serial.is_open:
            while readSerialPort:
                b = self.serial.readline()
                string = b.decode()
                components = string.split(", ")
                
                self.ax = float(components[0]) - self.ax_offset
                self.ay = float(components[1]) - self.ay_offset
                self.az = float(components[2]) - self.az_offset
                time_ = float(components[6])
                
                if self.t0 == None:
                    self.t0 = time_
                
                vx = (self.ax - self.ax0)*(time_ - self.t0) - self.vx_offset
                vy = (self.ay - self.ay0)*(time_ - self.t0) - self.vy_offset
                vz = (self.az - self.az0)*(time_ - self.t0) - self.vz_offset
                
                self.dx = vx*(time_ - self.t0) + 0.5*self.ax*(time_ - self.t0)**2
                self.dy = vy*(time_ - self.t0) + 0.5*self.ay*(time_ - self.t0)**2
                self.dz = vz*(time_ - self.t0) + 0.5*self.az*(time_ - self.t0)**2
                
                self.ax0, self.ay0, self.az0 = self.ax, self.ay, self.az
                self.t0 = time_
                
                self.x = self.x + (np.round(self.dx, 3) * 1000)
                self.y = self.y + (np.round(self.dy, 3) * 1000)
                self.z = self.z + (np.round(self.dz, 3) * 1000)
                
                self.roll = float(components[3])
                self.pitch = float(components[4])
                self.yaw = -float(components[5])
                print("Roll: {0},\tPitch: {1},\tYaw: {2}".format(self.roll, self.pitch, self.yaw))
                readSerialPort = False
        
    def execute(self, obj, event):
        imu = IMU()
        self.renderer.AddActor(imu.vtkActor)
        
        self.parseSerialData()
        
        if self.roll and self.pitch and self.yaw:
            imu.transform.Translate(self.x, self.y, self.z)
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
    camera.SetPosition(0, 0, 75)
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
