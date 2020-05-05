import io
import socket
import sys
import numpy as np
import vtk

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print (sys.stderr, 'starting up on %s port %s' % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

count = 0
while True:
    # Wait for a connection
    print (sys.stderr, 'waiting for a connection')
    connection, client_address = sock.accept()

    try:
        print (sys.stderr, 'connection from', client_address)
        data = connection.recv(16384)
        
        if data:
            data = np.frombuffer(data).reshape(505, 3)
            
        points = vtk.vtkPoints()
        for i in data:
            points.InsertNextPoint(i)
        
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        
        vertex = vtk.vtkVertexGlyphFilter()
        vertex.SetInputData(polydata)
        vertex.Update()
        
        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName("/home/kdean/socket_cloud_{0}.vtp".format(str(count).zfill(4)))
        writer.SetInputData(vertex.GetOutput())
        writer.Write()
        
        count += 1
            
    finally:
        # Clean up the connection
        connection.close()

sock.close()
