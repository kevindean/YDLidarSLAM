import os, sys
import socket
import numpy as np
import time
import ydlidar

class YdLidar():
    def __init__(self, serial_port="/dev/ydlidar"):
        ydlidar.os_init()
        ports = ydlidar.lidarPortList()
        port = serial_port
        
        for key, value in ports.items():
            port = value
        
        self.laser = ydlidar.CYdLidar()
        
        self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
        self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
        self.laser.setlidaropt(ydlidar.LidarPropLidarType, 1)
        self.laser.setlidaropt(ydlidar.LidarPropDeviceType, 0)
        self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
        self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
        self.laser.setlidaropt(ydlidar.LidarPropFixedResolution, True)
        self.laser.setlidaropt(ydlidar.LidarPropInverted, True)
        self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
        self.laser.setlidaropt(ydlidar.LidarPropIntenstiy, True) # required for G2B
        self.laser.setlidaropt(ydlidar.LidarPropMaxAngle, 180.0)
        self.laser.setlidaropt(ydlidar.LidarPropMinAngle, -180.0)
    
    def StopScanning(self):
        print("Turning off & Disconnecting Laser")
        self.laser.turnOff()
        self.laser.disconnecting()

def main(maxScans=1000, serial_port="/dev/ydlidar", address='localhost', port=10000):
    Laser = YdLidar(serial_port=serial_port)
    
    ret = Laser.laser.initialize()
    if ret:
        ret = Laser.laser.turnOn()
        scan = ydlidar.LaserScan()
        
        # Wait a few seconds
        print("Waiting 3 seconds before acquiring data")
        time.sleep(3)
        
        curScanIndex = 0
        while ret and ydlidar.os_isOk() and curScanIndex <= maxScans:
            r = Laser.laser.doProcessSimple(scan)
            
            if r:
                pts = []
                for point in scan.points:
                    x = point.range * np.cos(point.angle)
                    y = point.range * np.sin(point.angle)
                    z = 0.0
                    intensity = point.intensity
                    
                    # append calculated points to the pts list
                    pts.append([x, y, z, intensity])
                
                socketMessage = np.asarray(pts)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                server_address = (address, port)
                print(sys.stderr, "Connecting to %s port %s" % server_address)
                
                try:
                    sock.connect(server_address)
                except (TimeoutError, ConnectionRefusedError) as e:
                    print("Terminating\nClosing Socket")
                    sock.close()
                    
                    print("Turning Off Laser")
                    Laser.StopScanning()
                    
                    sys.exit("Exiting Program")
                
                try:
                    sock.sendall(socketMessage.tobytes())
                finally:
                    print(sys.stderr, 'closing socket')
                    sock.close()
                
                curScanIndex += 1
            else:
                print(sys.stderr, "didn't acquire data,\nExiting")
                Laser.StopScanning()
                sys.exit()
    
    Laser.StopScanning()

if __name__ == "__main__":
    main()
