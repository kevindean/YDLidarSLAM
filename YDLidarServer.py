import os
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
delay, max_delay = 0, 10000
while True:
    # Wait for a connection
    print (sys.stderr, 'waiting for a connection')
    connection, client_address = sock.accept()

    try:
        print (sys.stderr, 'connection from', client_address)
        # create a large enough buffer to make sure all points from client are received
        data = connection.recv(16384)
        
        if data:
            # change the message into a numpy array
            data = np.frombuffer(data).reshape(505, 3)
            
            # save the data to a vtk polydata file in order to visualize in ParaView
            points = vtk.vtkPoints()
            for i in data:
                points.InsertNextPoint(i)
            
            # generate a polydata and fill in the points
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            
            # generate a vertex filter to fill in cells and vertices
            vertex = vtk.vtkVertexGlyphFilter()
            vertex.SetInputData(polydata)
            vertex.Update()
            
            # write the file
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(os.getenv("HOME") + "/socket_cloud_{0}.vtp".format(str(count).zfill(4)))
            writer.SetInputData(vertex.GetOutput())
            writer.Write()
            
            count += 1
        else:
            delay += 1
        
        if delay == max_delay:
            connection.close()
            sock.close()
            sys.exit("No Data coming across Socket\nExiting!")
            
    finally:
        # Clean up the connection
        connection.close()
