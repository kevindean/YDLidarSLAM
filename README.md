# YDLidarSLAM
plan on utilizing openIMU300RI and YDLidar G2 to perform SLAM operations... this is the beginning

And since this is the beginning of the project. The efforts must start with getting each device to work before properly integrating them together. TODO list:

(1) acquire imu, acquire lidar

(2) get an understanding of how to implement ROS with YDLidar, they have a very nice introduction that was easy to follow, the link I followed is here: http://www.ydlidar.com/Public/upload/files/2020-04-13/YDLIDAR-X4-USER%20Manual.pdf
    * I followed the setup for the Linux ROS integration
    * I am also running Ubuntu 16.04 (will eventually do it with 18.04), but for now, I followed this link in order to get the 
      full ROS desktop environment installed on my PC: http://wiki.ros.org/kinetic/Installation/Ubuntu
    
(3) currently working with python-openimu to get the python driver for the imu to work (still waiting on parts to make a small power supply to turn on the device (I will provide instructions for how I am approaching the problem, as well as the links that I use in order to get the device to work)

(4) The eventual goal is to (possibly using python ros libraries) is to transcribe it to python since both libraries utilize that language.

(5) Once I have completed the tasks of getting the devices to work, preliminary results need to be provided. For example, I will show the IMU according to it's calculated values for roll, pitch, yaw. Utilizing VTK, I can represent the IMU simply as a vtkCubeSource (polydata); with vtkTransform and vtkTransformPolyDataFilter, I can apply the roll, pitch, and yaw values to that transform and show the IMU's placement in real-time. Thus providing a verification that it is not only working, but getting the correct transform values.

(6) the YDLidar shows results in RViz currently; but once again, I would need to show it utilized in python (picture of the lidar working in RViz has already been accomplished - an image is provided)

(7) The next step will be to integrate the two into one single output. It has to be shown that they can work together properly before a simultaneous mapping and localization can be performed. The YDLidar G2 is a single laser triangulation formmula that visualizes 360 degrees. Since it is only a 2 Dimensional representation, in order for a SLAM reconstruction to be accomplished, the IMU is need to change the angle of the point cloud. Thus showing the point cloud transforming in real-time (just a single cloud, not a SLAM)

(8) The final steps will incorporate everything together. However, that is where the "fun" begins; this means that positional tracking (aside from roll, pitch, and yaw calculations) needs to be performed in order to get the proper location of the current cloud going in to the reconstruction.

(9) Visualization will eventually be provided.
