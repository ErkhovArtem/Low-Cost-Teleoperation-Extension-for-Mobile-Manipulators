## Overview

This repo contains code and other supplementary materials for the paper [Low-Cost Teleoperation Extension for Mobile Manipulators](https://arxiv.org/abs/2603.07672) presented on **The 21st ACM/IEEE International Conference on Human-Robot Interaction** Workshop.

Teleoperation of mobile bimanual manipulators requires simultaneous control of high-dimensional systems, often necessitating expensive specialized equipment. We present an open-source teleoperation framework that enables intuitive whole body control using readily available commodity hardware. Our system combines smartphone-based head tracking for camera control, leader arms for bilateral manipulation, and foot pedals for hands-free base navigation. Using a standard smartphone with IMU and display, we eliminate the need for costly VR helmets while maintaining immersive visual feedback. The modular architecture integrates seamlessly with the XLeRobot framework, but can be easily adapted to other types of mobile manipulators. We validate our approach through user studies that demonstrate improved task performance and reduced cognitive load compared to keyboard-based control.

## Demo

![Demo](demo.gif)

## Install LeRobot 🤗

To install LeRobot, follow the [official Installation Guide](https://huggingface.co/docs/lerobot/installation)

```{note}
It's recommended to use `pip install -e .` for a more convenient file transfer.
```

Configure the motors for [SO101 arms](https://huggingface.co/docs/lerobot/so101#configure-the-motors) and [other motors](https://xlerobot.readthedocs.io/en/latest/hardware/getting_started/assemble.html#configure-motors) if you haven't done so.


## Move XLeRobot files 

Open the installed lerobot folder and:

- Move xlerobot robot folder the /robots folder.

- Move all content from /teleop folder to /example folder.

## Configure robot and teleoperation

### Robot Side Configuration

Edit the `xlerobot/config_xlerobot.py` file and configure the `XLerobotConfig` class:

1. **Camera Configuration**: Uncomment and configure the camera settings in the `xlerobot_cameras_config()` function. For example:
   ```python
   "head": RealSenseCameraConfig(
       serial_number_or_name="141722076677",  # Replace with your camera serial number
       fps=30,
       width=1280,
       height=720,
       color_mode=ColorMode.BGR,
       rotation=Cv2Rotation.NO_ROTATION,
       use_depth=False
   )
   ```
   Or use OpenCV camera:
   ```python
   "head": OpenCVCameraConfig(
       index_or_path="/dev/video0",  # Adjust to your camera device
       fps=30,
       width=640,
       height=480,
       rotation=Cv2Rotation.NO_ROTATION
   )
   ```

2. **Serial Ports**: Set the serial ports for the motor buses:
   ```python
   port1: str = "/dev/ttyACM0"  # Port for SO101 + head camera bus
   port2: str = "/dev/ttyACM1"  # Port for the other bus
   ```
   Adjust these paths according to your system's USB device mapping.

3. **Robot ID**: Set a unique identifier for the robot:
   ```python
   id: str = "xlerobot_follower"  # Must match the name of your robot calibration file
   ```

### Teleoperator Side Configuration

Edit the `teleop/xlerobot_teleoperate.py` file:

1. **XLerobotClientConfig**: Configure the connection to the robot:
   ```python
   follower_config = XLerobotClientConfig(
       remote_ip='10.16.116.22',  # Replace with robot's IP address
       cameras=camera_config  # Match camera configuration with robot side
   )
   ```
   - Set `remote_ip` to the IP address of the robot computer
   - Configure `cameras` dictionary to match the camera setup on the robot side (same serial numbers or device paths)

2. **BiSO100LeaderConfig**: Configure the leader arms (teleoperator's arms):
   ```python
   leader_config = BiSO100LeaderConfig(
       left_arm_port="/dev/ttyACM0",   # Serial port for left leader arm
       right_arm_port="/dev/ttyACM1",  # Serial port for right leader arm
       id="leader_arm"                  # Unique identifier for leader arms
   )
   ```
   Adjust the serial ports to match your leader arm devices.

## Run

### Starting the Robot Host

On the robot side, run the host script:

```bash
python xlerobot/xlerobot_host.py
```

The host will:
- Connect to the robot hardware via the configured serial ports
- Start listening for commands on ZMQ ports (default: 5555 for commands, 5556 for observations)
- Stream camera observations to the teleoperator
- Execute commands received from the teleoperator

Wait for the message "Waiting for commands..." before starting the teleoperator side.

### Starting the Teleoperator

On the teleoperator side, run the teleoperation script:

```bash
python teleop/xlerobot_teleoperate.py
```

**Optional arguments:**
- `--use-keyboard`: Use keyboard control for head and base instead of phone/pedals
- `--visualize`: Enable visualization with Rerun viewer

### Using Phone for Head Control

By default, the teleoperator uses a phone-based VR interface for head control:

1. When you start `xlerobot_teleoperate.py`, a web server will automatically start
2. Look for a console message like:
   ```
   📱 Mobile Device: Open browser and go to:
      https://<IP_ADDRESS>:8443
   ```
3. Open this URL on your mobile device (iOS Safari or Android Chrome/Firefox)
4. Grant permission for device orientation when prompted
5. Click "Start Streaming" to begin head control
6. The phone's orientation will control the robot's head movement

**Note**: The first time you run the server, it will create a self-signed SSL certificate. You may need to accept the security warning in your browser.

### Using Keyboard Control

To use keyboard control for both head and base instead of phone/pedals:

```bash
python teleop/xlerobot_teleoperate.py --use-keyboard
```

**Keyboard controls:**
- `i` / `k`: Move forward/backward
- `j` / `l`: Move left/right
- `u` / `o`: Rotate left/right
- `w` / `s`: Head motor 2 up/down
- `a` / `d`: Head motor 1 left/right
- `n` / `m`: Speed up/down
- `b`: Quit teleoperation


## Citation

Please cite the following if you found our work useful:

```
@article{belov2026lowcostteleoperationextensionmobile,
      title={Low-Cost Teleoperation Extension for Mobile Manipulators}, 
      author={Danil Belov and Artem Erkhov and Yaroslav Savotin and Tatiana Podladchikova and Pavel Osinenko and Dzmitry Tsetserukou},
      year={2026},
      eprint={2603.07672},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2603.07672}, 
}
```