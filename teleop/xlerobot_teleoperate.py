# !/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import numpy as np
import cv2
import serial
import logging
import serial.tools.list_ports

from lerobot.teleoperators.bi_so100_leader.config_bi_so100_leader import BiSO100LeaderConfig
from lerobot.teleoperators.bi_so100_leader.bi_so100_leader import BiSO100Leader
from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.robots.xlerobot import XLerobotClientConfig, XLerobotClient
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data
from lerobot.cameras.configs import CameraConfig, Cv2Rotation, ColorMode
from lerobot.cameras.realsense import RealSenseCamera, RealSenseCameraConfig

from phone_server import PhoneServer

class XlerobotPedalTeleop:
    def __init__(self, vid = 1155, pid = 22336, baudrate = 115200, timeout = 0.1):
        self.vid = vid
        self.pid = pid
        self.baudrate = baudrate
        self.timeout = timeout
        self.pedal_mapping = {
            '3': 'forward',
            '2': 'backward',
            '1': 'left',
            '0': 'right',
        }

    def connect(self):
        self.port = self.__find_and_open_port()

    def get_action(self):
        self.port.reset_input_buffer()

        # try:
        #     if self.port.in_waiting > 0:
        #         data = self.port.read(self.port.in_waiting)
        # except:
        #     print("No data available!")

        data = self.port.read(1)
        if not data:
            return []
        
        data = data[0]
        pressed_pedals = []
        for i in range(len(self.pedal_mapping)):
            if data >> i & 1:
                pressed_pedals.append(self.pedal_mapping[str(i)])
        return pressed_pedals

    def __find_device_by_vid_pid(self):
        """
        Searches for a device with the given VID and PID.

        :return: The device port name (e.g., 'COM3' or '/dev/ttyUSB0'), or None if not found.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == self.vid and port.pid == self.pid:
                return port.device
        logging.error("No device found")
        return None

    def __find_and_open_port(self):
        """
        Finds the device by VID/PID and opens the serial port.

        :return: A serial.Serial object or None if the device is not found.
        """
        device_port = self.__find_device_by_vid_pid()
        if device_port:
            logging.info(f"Device found on port: {device_port}")
            try:
                port = serial.Serial(
                    device_port, baudrate=self.baudrate, timeout=self.timeout
                )
                if port.isOpen():
                    logging.info(f"Port {device_port} opened successfully")
                    return port
            except Exception as e:
                logging.error(f"Failed to open port {device_port}: {e}")
        logging.error("No device found")
        return None

def transform_arm_keys(original_dict: dict) -> dict:

    transformed = {}
    
    for key, value in original_dict.items():
        if key.startswith('left_'):
            new_key = key.replace('left_', 'left_arm_', 1)
        elif key.startswith('right_'):
            new_key = key.replace('right_', 'right_arm_', 1)
        else:
            new_key = key  # Оставляем без изменений
            
        transformed[new_key] = value
    
    return transformed

def main():

    import argparse
    
    parser = argparse.ArgumentParser(description='Xlerobot teleoperate')
    parser.add_argument('--use-keyboard', action='store_true', help='Use keyboard teleoperation for head and base')
    parser.add_argument('--visualize', action='store_true', help='Visualize the teleoperation')
    
    args = parser.parse_args()

    use_keyboard = args.use_keyboard
    visualize = args.visualize
    FPS = 30

    camera_config = {
                "head": RealSenseCameraConfig(
                serial_number_or_name="141722076677",  # Replace with camera SN
                fps=30,
                width=1280,
                height=720,
                color_mode=ColorMode.BGR, # Request BGR output
                rotation=Cv2Rotation.NO_ROTATION,
                use_depth=False
            )
    }

    follower_config = XLerobotClientConfig(remote_ip = '192.168.31.138', cameras=camera_config)

    leader_config = BiSO100LeaderConfig(left_arm_port="/dev/ttyACM0", right_arm_port="/dev/ttyACM1", id="leader_arm")

    # Initialize the robot and teleoperator
    leader = BiSO100Leader(leader_config)
    follower = XLerobotClient(follower_config)

    #Init the keyboard instance
    keyboard_config = KeyboardTeleopConfig()
    keyboard = KeyboardTeleop(keyboard_config)
    keyboard.connect()

    # Init pedals and headset server
    if not use_keyboard:
        headset_server = PhoneServer()
        headset_server.run()
        pedals = XlerobotPedalTeleop()
        pedals.connect()

    # Connect to the robot and teleoperator
    follower.connect()
    leader.connect()
    

    # Init rerun viewer
    if visualize:
        init_rerun(session_name="xlerobot_teleop")

    print("Starting teleop loop...")
    while True:
        t0 = time.perf_counter()
        # Get observation
        obs = follower.get_observation()
        if not use_keyboard:
            headset_server.update_frame(obs['head'])
            head_angles = headset_server.get_angles()
            head_action = {}
            head_action["head_motor_1.pos"] = 1.1*head_angles['yaw'] + follower.head_base_pose["head_motor_1.pos"]
            head_action["head_motor_2.pos"] = 2*head_angles['roll'] + follower.head_base_pose["head_motor_2.pos"]

        # Get teleop action
        action = leader.get_action()
        action = transform_arm_keys(action)

        pressed_keys = set(keyboard.get_action().keys())
        keyboard_keys = np.array(list(pressed_keys))
        if use_keyboard:
            base_action = follower._from_keyboard_to_base_action(keyboard_keys)
            head_action = follower._from_keyboard_to_head_action(keyboard_keys)
        else:
            pressed_pedals = pedals.get_action()
            base_action = follower._from_pedals_to_base_action(pressed_pedals, keyboard_keys)
            if 'c' in pressed_pedals:
                headset_server.recalibrate()

        action = {**action, **base_action, **head_action}
        
        # Send processed action to robot (robot_action_processor.to_output should return dict[str, Any])
        _ = follower.send_action(action)
        # Visualize
        if visualize:
            obs['head'] = cv2.cvtColor(obs['head'], cv2.COLOR_BGR2RGB)
            log_rerun_data(observation=obs, action=action)

        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))


if __name__ == "__main__":
    main()