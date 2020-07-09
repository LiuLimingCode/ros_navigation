#!/usr/bin/env python

'''
This script makes Gazebo less fail by translating gazebo status messages to odometry data.
Since Gazebo also publishes data faster than normal odom data, this script caps the update to 20hz.
Winter Guerra
'''

import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose, Twist, Transform, TransformStamped, Point
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import Header
import numpy as np
import math
import tf2_ros

class OdometryNode:

    def __init__(self):
        # init internals
        self.last_received_pose = Pose()
        self.last_received_twist = Twist()
        self.last_recieved_stamp = None

        self.x_pos = rospy.get_param("~x_pos", 0.0)
        self.y_pos = rospy.get_param("~y_pos", 0.0)
        self.z_pos = rospy.get_param("~z_pos", 0.0)
        self.object_name = rospy.get_param("~object_name", "robot")
        self.update_rate = rospy.get_param("~update_rate", 20)
        self.publish_tf = rospy.get_param("~publish_tf", False)
        self.odom_topic = rospy.get_param("~odom_topic", "odom")
        self.base_frame = rospy.get_param("~base_frame", "base_link")
        self.odom_frame = rospy.get_param("~odom_frame", "odom")

        # Set the update rate
        rospy.Timer(rospy.Duration(1.0 / self.update_rate), self.timer_callback)

        # Set subscribers
        rospy.Subscriber('/gazebo/link_states', LinkStates, self.sub_robot_pose_update)
        self.odomPublisher = rospy.Publisher(self.odom_topic, Odometry, queue_size=1)
        self.tfBroadcaster = tf2_ros.TransformBroadcaster()

    def sub_robot_pose_update(self, msg):
        # Find the index of the racecar
        try:
            arrayIndex = msg.name.index(self.object_name + '::' + self.base_frame)
        except ValueError as e:
            # Wait for Gazebo to startup
            self.last_recieved_stamp = None
        else:
            # Extract our current position information
            temp_pose = msg.pose[arrayIndex]
            temp_pose.position.x -= self.x_pos
            temp_pose.position.y -= self.y_pos
            temp_pose.position.z -= self.z_pos

            self.flag_reading = True
            self.last_received_pose = temp_pose
            self.last_received_twist = msg.twist[arrayIndex]
            self.last_recieved_stamp = rospy.Time.now()
            self.flag_reading = False

    def timer_callback(self, event):
        if self.last_recieved_stamp is None:
            return

        if self.flag_reading is True:
            return

        cmd = Odometry()
        cmd.header.stamp = self.last_recieved_stamp
        cmd.header.frame_id = self.odom_frame
        cmd.child_frame_id = self.base_frame
        cmd.pose.pose = self.last_received_pose
        cmd.twist.twist = self.last_received_twist
        self.odomPublisher.publish(cmd)

        if self.publish_tf:
            tf = TransformStamped(
                header=Header(
                    frame_id=cmd.header.frame_id,
                    stamp=cmd.header.stamp
                ),
                child_frame_id=cmd.child_frame_id,
                transform=Transform(
                    translation=cmd.pose.pose.position,
                    rotation=cmd.pose.pose.orientation
                )
            )
            self.tfBroadcaster.sendTransform(tf)

# Start the node
if __name__ == '__main__':
    rospy.init_node("gazebo_odometry_node")
    node = OdometryNode()
    rospy.spin()