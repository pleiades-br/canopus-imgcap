# imgcap

A command-line tool for capturing video frames using v4l2-ctl (Video4Linux2).

## Description

imgcap is a simple utility that allows you to capture still images from video devices on Linux systems. It uses the v4l2-ctl command-line tool to interface with Video4Linux2 compatible devices such as webcams, USB cameras, and other video capture devices.

## Features

- Support for multiple predefined image sizes
- Customizable output filename and directory
- Simple command-line interface
- Built on top of the reliable v4l2-ctl utility

## Prerequisites

- Linux operating system with Video4Linux2 support
- `v4l2-utils` package installed
- Python 3.x
- Video capture device (webcam, USB camera, etc.)

### Installing v4l2-utils

On Ubuntu/Debian:
```bash
sudo apt-get install v4l2-utils
```

On CentOS/RHEL/Fedora:
```bash
sudo yum install v4l2-utils  # CentOS/RHEL
sudo dnf install v4l2-utils  # Fedora
```

## Installation

1. Clone this repository or download the script
2. Make the script executable:
```bash
chmod +x imgcap.py
```
3. Optionally, create a symlink to use it system-wide:
```bash
sudo ln -s /path/to/imgcap.py /usr/local/bin/imgcap
```

## Usage

```bash
imgcap <device> [options]
```

### Arguments

- `device`: Video device path (e.g., `/dev/video0`, `/dev/video2`)

### Options

- `--size`: Image size preset (small/medium/large)
- `--filename`: Output filename (default: frame.png)
- `--output_dir`: Output directory (default: current directory)
- `--show_results`: Show result in HDMI output (default: False)

### Size Presets

| Size   | Resolution  |
|--------|-------------|
| small  | 640x480     |
| medium | 1640x1232   |
| large  | 1920x1080   |

## Examples

### Basic usage
Capture a frame from video device with default settings:
```bash
imgcap /dev/video0
```

### Specify image size
Capture a medium-sized frame:
```bash
imgcap /dev/video2 --size medium
```

### Custom filename and output directory
```bash
imgcap /dev/video2 --size large --filename my_photo.png --output_dir /home/user/photos
```

### Custom filename only
```bash
imgcap /dev/video3 --size large --filename custom_name.png
```

## Finding Your Video Device

To list available video devices on your system:
```bash
ls /dev/video*
```

To get detailed information about a video device:
```bash
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

## Troubleshooting

### Permission Denied
If you get permission errors, make sure your user is in the `video` group:
```bash
sudo usermod -a -G video $USER
```
Then log out and log back in.

### Device Busy
If the device is busy, make sure no other applications (like browsers, video conferencing apps) are using the camera.

### Unsupported Resolution
If a size preset doesn't work with your device, check supported resolutions:
```bash
v4l2-ctl --device=/dev/video0 --list-framesizes=MJPG
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

This project is licensed under the MIT License - see the LICENSE file for details.