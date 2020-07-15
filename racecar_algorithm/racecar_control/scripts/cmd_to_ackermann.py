#!/usr/bin/env python

import rospy

from std_msgs.msg import Header
from geometry_msgs.msg import Pose, Twist, Vector3
from ackermann_msgs.msg import AckermannDriveStamped

def Twist_Cmd_Callback(data):

    global ack_publisher

    ack_cmd = AckermannDriveStamped()
    ack_cmd.header.stamp = rospy.Time.now()

    # scheme 1:
    # set cmd_angle_instead_rotvel TRUE in teb_planner and use the origin linear data
    # the speed is very slow, maybe performance can be improved by adjusting the params of teb_local_planner, like weight_max_vel_x, weight_shortest_path...
    #ack_cmd.drive.speed = data.linear.x
    #ack_cmd.drive.steering_angle = data.angular.z 

    # scheme 2:
    # set cmd_angle_instead_rotvel TRUE in teb_planner and use constant linear data
    # it's a simply way to improve speed, but the car cannot finish navigation when speed is fast 
    ack_cmd.drive.speed = 1.5
    ack_cmd.drive.steering_angle = data.angular.z

    # scheme 3:
    # set cmd_angle_instead_rotvel FALSE in teb_planner and use constant linear data
    # because cmd_angle_instead_rotvel is false and move_base will calculate the desired linear data and angular data
    # we can use the ackermann turning model and the params of car model to calcaulate the steering_angle
    # I haven't implemented this scheme yet
    #ack_cmd.drive.speed = 1.5
    #ack_cmd.drive.steering_angle = 

    ack_publisher.publish(ack_cmd)

if __name__ == "__main__":
    rospy.init_node("cmd_to_ackermann_node")

    global ack_publisher

    twist_cmd_topic = rospy.get_param("~twist_cmd_topic", "/cmd_vel")
    ackermann_cmd_topic = rospy.get_param("~ackermann_cmd_topic", "/cmd_ackermann")

    ack_publisher = rospy.Publisher(ackermann_cmd_topic, AckermannDriveStamped, queue_size=1)
    rospy.Subscriber(twist_cmd_topic, Twist, Twist_Cmd_Callback)

    rospy.spin()
