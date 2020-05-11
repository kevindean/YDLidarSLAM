import os, sys
import vtk
import serial
import numpy as np

accel_offset = [-1.477229773462783, 0.3782006472491909, -0.3691974110032362]
gyro_offset = [-169.23784466019418, 25.974271844660194, -31.406990291262137]
mag_offset = [38.42743042071198, 6.023100323624595, -60.78293203883496]


class IMU():
    def __init__(self, xLength=10, yLength=10, zLength=1):
        self.imu = vtk.vtkCubeSource()
        self.imu.SetXLength(xLength)
        self.imu.SetYLength(yLength)
        self.imu.SetZLength(zLength)
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
        accel, gyro, mag = [], [], []
        readSerialPort = True
        
        if self.serial.is_open:
            while readSerialPort:
                b = self.serial.readline()
                string = b.decode()
                
                if len(string.split("Accel:")) == 2:
                    components = string.split(" ")
                    accel.append([float(components[1].split(',')[0]),
                                  float(components[2].split(',')[0]),
                                  float(components[3].split(',')[0])])
                
                if len(string.split("Gyro:")) == 2:
                    components = string.split(" ")
                    gyro.append([float(components[1].split(',')[0]),
                                 float(components[2].split(',')[0]),
                                 float(components[3].split(',')[0])])
                
                if len(string.split("Mag:")) == 2:
                    components = string.split(" ")
                    mag.append([float(components[1].split(',')[0]),
                                float(components[2].split(',')[0]),
                                float(components[3].split(',')[0])])
                
                if accel and gyro and mag:
                    accel[0][0] /= accel_offset[0]
                    accel[0][1] /= accel_offset[1]
                    accel[0][2] /= accel_offset[2]
                    
                    mag[0][0] /= mag_offset[0]
                    mag[0][1] /= mag_offset[1]
                    mag[0][2] /= mag_offset[2]
                    
                    self.pitch = 180 * np.arctan2(accel[0][1], np.sqrt(accel[0][0]**2 + accel[0][2]**2)) / np.pi
                    self.roll = 180 * np.arctan2(accel[0][0], np.sqrt(accel[0][1]**2 + accel[0][2]**2)) / np.pi
                    
                    magX = mag[0][0]*np.cos(self.pitch) + \
                           mag[0][1]*np.sin(self.roll)*np.sin(self.pitch) + \
                           mag[0][2]*np.cos(self.roll)*np.sin(self.pitch)
                    magY = mag[0][1]*np.cos(self.roll) - mag[0][2]*np.sin(self.roll)
                    
                    self.yaw = 180 * np.arctan2(-magX, magY) / np.pi
                                        
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
