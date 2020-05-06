# still working on some kinks (some issues with the the render window closing - working on that currently), but this 
# will be the format that I use from now on in order to acquire the callback for the lidar and the IMU in order to get in one.

import os, sys
import socket
import numpy as np
import vtk

class VTKPointCloud():
    def __init__(self):
        self.vtkPoints = vtk.vtkPoints()
        self.vtkPolyData = vtk.vtkPolyData()
        self.vtkVertex = vtk.vtkVertexGlyphFilter()
        self.Writer = vtk.vtkXMLPolyDataWriter()
        
        # set up vtk polydata mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.vtkVertex.GetOutput())
        mapper.SetScalarVisibility(True)
        
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.GetProperty().SetPointSize(3)
        self.vtkActor.SetMapper(mapper)
    
    def WriteData(self, filename_str):
        self.Writer.SetFileName(filename_str)
        self.Writer.SetInputData(self.vtkPolyData)
        self.Write()

class HandleVTKCloud():
    def __init__(self, renderer, server='localhost', address=10000, maxDelay=1000, maxNumClouds=1000):
        self.renderer = renderer
        
        # create tcp/ip socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # bind the socket to the port
        self.sock.bind((server, address))
        print(sys.stderr, "Staring On {0}, port {1}".format(server, address))
        
        # open the socket to listen, and wait for a connection
        self.sock.listen(1)
        
        # tracker(s)
        self.count = 0
        self.delay = 0
        self.maxDelay = maxDelay
        self.maxNumClouds = maxNumClouds
        
        # make a pointer to the data
        self.data_recvd = None
        
    def execute(self, obj, event):
        self.count += 1
        if self.count == self.maxNumClouds - 1:
            print("Closing App")
            self.sock.close()
            obj.GetRenderWindow().Finalize()
            obj.TerminateApp()
        
        print(sys.stderr, "Num Cloud %d" % self.count)
        pointCloud = VTKPointCloud()
        self.renderer.AddActor(pointCloud.vtkActor)
        
        print(sys.stderr, "Waiting for a connection")
        connection, client_address = self.sock.accept()
        
        try:
            print(sys.stderr, "connection from", client_address)
            self.data_recvd = connection.recv(16384)
            
            if self.data_recvd:
                data = np.frombuffer(self.data_recvd).reshape(505, 4)
                
                intensity_scalars = vtk.vtkDoubleArray()
                intensity_scalars.SetName("intensity")
                
                for i in data:
                    pointCloud.vtkPoints.InsertNextPoint(i[0:3])
                    intensity_scalars.InsertNextValue(i[-1])
                
                pointCloud.vtkPolyData.SetPoints(pointCloud.vtkPoints)
                pointCloud.vtkPolyData.GetPointData().SetScalars(intensity_scalars)
                
                pointCloud.vtkVertex.SetInputData(pointCloud.vtkPolyData)
                pointCloud.vtkVertex.Update()
                
                obj.GetRenderWindow().Render()
                self.renderer.RemoveActor(pointCloud.vtkActor)
        
        finally:
            # clean up the connection
            connection.close()
        
#        self.delay += 1
#        print(self.delay)
#        
#        if self.delay == self.maxDelay:
#            print(sys.stderr, "No Data has been acquired,\n \
#                closing socket and exiting program!")
#            self.connection.close()
#            self.sock.close()
#            sys.exit()

class KeyBoardInterrupt(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, HandleCloud):
        self.cloudInfo = HandleCloud
    
    def execute(self, obj, event):
        if self.obj.GetKeySym() == 'q':
            print(sys.stderr, "Pressed key: %s" % key)
            self.cloudInfo.sock.close()
            obj.GetRenderWindow().Finalize()
            obj.TerminateApp()

def main():
    camera = vtk.vtkCamera()
    camera.SetPosition(0, 0, 20)
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
    
    handleCloud = HandleVTKCloud(renderer)
    style = KeyBoardInterrupt(handleCloud)
    renderWindowInteractor.SetInteractorStyle(style)
    renderWindowInteractor.AddObserver('TimerEvent', handleCloud.execute)
    renderWindowInteractor.AddObserver('TerminatingEvent', style.execute)
    timerId = renderWindowInteractor.CreateRepeatingTimer(1)
    
    renderWindow.Render()
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()
