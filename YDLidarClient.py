import io
import socket
import sys
import numpy as np
import random
import time
import ydlidar

ydlidar.os_init()
ports = ydlidar.lidarPortList()
port = "/dev/ydlidar"
for key, value in ports.items():
    port = value

laser = ydlidar.CYdLidar()
laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
laser.setlidaropt(ydlidar.LidarPropLidarType, 1)
laser.setlidaropt(ydlidar.LidarPropDeviceType, 0)
laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
laser.setlidaropt(ydlidar.LidarPropFixedResolution, True)
laser.setlidaropt(ydlidar.LidarPropInverted, True)
laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
laser.setlidaropt(ydlidar.LidarPropIntenstiy, True) # required for G2B
laser.setlidaropt(ydlidar.LidarPropMaxAngle, 180.0)
laser.setlidaropt(ydlidar.LidarPropMinAngle, -180.0)
    
ret = laser.initialize()
if ret:
    ret = laser.turnOn()
    scan = ydlidar.LaserScan()
    
    time.sleep(5)
    
    count = 0
    while ret and ydlidar.os_isOk() and count <= 1000:
        r = laser.doProcessSimple(scan)
        if r:
            print("Scan received[", scan.stamp, "]:",
                  scan.points.size(), "ranges is [",
                  1.0 / scan.config.scan_time, "]Hz")
        else :
            print("Failed to get Lidar Data")
            sys.exit()
        
        pts = []
        
        for point in scan.points:
            x = point.range * np.cos(point.angle)
            y = point.range * np.sin(point.angle)
            z = 0.0
            pts.append([x, y, z])
        
        message = np.array(pts)

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the port where the server is listening
        server_address = ('localhost', 10000)
        print (sys.stderr, 'connecting to %s port %s' % server_address)
        sock.connect(server_address)
        
        try:
            sock.sendall(message.tobytes())
        finally:
            print (sys.stderr, 'closing socket')
            sock.close()
        
        count += 1

laser.turnOff()
laser.disconnecting()
