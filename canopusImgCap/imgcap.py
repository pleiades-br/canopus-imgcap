#!/usr/bin/env python3
"""
Simple video capture tool using v4l2-ctl and ImageMagick convert
Usage: python video_capture.py <device> <size> [filename] [directory]
"""

import sys
import os
import subprocess
import argparse
import tempfile
import signal


class ImageCapture:
    def __init__(self):
        self.interrupted = False

    def signal_handler(self, signum, frame):
        """Handle keyboard interrupts and other signals gracefully"""
        signal_names = {
            signal.SIGINT: "SIGINT (Ctrl+C)",
            signal.SIGTERM: "SIGTERM",
        }

        signal_name = signal_names.get(signum, f"Signal {signum}")
        print(f"\n\nReceived {signal_name}. Exiting gracefully...")

        self.interrupted = True
        sys.exit(0)

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)


    def validate_device(self, device_path):
        """Validate that the video device exists and is accessible"""
        if not os.path.exists(device_path):
            raise FileNotFoundError(f"Video device {device_path} not found")

        if not os.access(device_path, os.R_OK):
            raise PermissionError(f"No read permission for device {device_path}")

        # Test if v4l2-ctl can access the device
        try:
            result = subprocess.run(
                ['v4l2-ctl', '--device', device_path, '--list-formats'],
                check=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"Cannot access device {device_path}: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout while accessing device {device_path}")
        except FileNotFoundError:
            raise RuntimeError("v4l2-ctl not found. Please install v4l2-utils package")

    def get_resolution(self, size_arg):
        """Parse size argument"""

        size_map = {
            'small': (640,480),
            'large': (1920,1080)
        }
        if size_arg.lower() in size_map:
            return size_map[size_arg.lower()]

        raise ValueError(f"Invalid size format. Use one of {list(size_map.keys())}  (e.g., 640x480)")

    def run_command(self, cmd, description=""):
        """Run a shell command and handle errors"""
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error {description}: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr.strip()}")
            return False
        except FileNotFoundError:
            print(f"Command not found: {cmd[0]}. Make sure it's installed and in PATH.")
            return False

    def capture_frame(self, device, width, height, output_dir, filename, show_results):
        """Capture a frame using v4l2-ctl and convert it to PNG"""

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Use temporary file for raw frame data
        with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as temp_file:
            temp_raw_path = temp_file.name

        try:
            # Step 1: Set video format
            cmd1 = [
                'v4l2-ctl',
                '--device', device,
                f'--set-fmt-video=width={width},height={height},pixelformat=RGGB'
            ]

            if not self.run_command(cmd1, "setting video format"):
                return False

            cmd2 = [
                'v4l2-ctl'
                '--device', device,
                '-c',
                'alpha_component=128'
            ]

            if not self.run_command(cmd2, "setting video format"):
                return False

            # Step 2: Capture raw frame
            cmd3 = [
                'v4l2-ctl',
                '--device', device,
                '--stream-mmap',
                f'--stream-to={temp_raw_path}',
                '--stream-count=1'
            ]

            if not self.run_command(cmd3, "capturing frame"):
                return False

            # Step 3: Convert raw frame to PNG
            final_path = os.path.join(output_dir, filename)
            cmd4 = [
                'convert',
                '-size', f'{width}x{height}',
                '-depth', '8',
                f'gray:{temp_raw_path}',
                final_path
            ]

            if not self.run_command(cmd4, "converting to PNG"):
                return False

            print(f"Successfully saved image to: {final_path}")

            if show_results is True:
                cmd5 = [
                    'weston-image',
                    final_path
                ]
                self.run_command(cmd5, "showing the results on hdmi")

            return True

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_raw_path)
            except OSError:
                pass

def main():
    """Main function"""
    # Create capture instance
    capture = ImageCapture()

    # Set up signal handlers for graceful shutdown
    capture.setup_signal_handlers()

    parser = argparse.ArgumentParser(
        description='Capture video frame using v4l2-ctl',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Size options:
  small   - 640x480  
  large   - 1920x1080

Examples:
  imgcap /dev/video2 --size medium
  imgcap /dev/video2 --size large --filename my_photo.png --output_dir /home/user/photos
  imgcap /dev/video3 --size large --filename custom_name.png 
        """
    )

    parser.add_argument('device', help='Video device path (e.g., /dev/video2)')
    parser.add_argument('--size',type=str, help='Image size (small/medium/large)')
    parser.add_argument('--filename', type=str, default='frame.png',
                       help='Output filename (default: frame.png)')
    parser.add_argument('--output_dir', type=str, default='.',
                       help='Output directory (default: current directory)')
    parser.add_argument('--show_results', action='store_true',
                        help='Show result in hdmi output')

    # Handle case where script is called with sys.argv directly
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)

#    try:

    args = parser.parse_args()

    width, height = capture.get_resolution(args.size)

    capture.validate_device(args.device)

    # Ensure filename has .png extension
    filename = args.filename
    if not filename.lower().endswith('.png'):
        filename += '.png'

    print(f"Capturing from device: {args.device}")
    print(f"Size: {width}x{height}")
    print(f"Output: {os.path.join(args.output_dir, filename)}")
    print("-" * 50)

    success = capture.capture_frame(args.device,
                            width,
                            height,
                            args.output_dir,
                            filename,
                            args.show_results)
    if success:
        print("Capture completed successfully!")
        sys.exit(0)
    else:
        print("Capture failed!")
        sys.exit(1)

#    except KeyboardInterrupt:
#        print("\n\nOperation cancelled by user")
#        sys.exit(0)
#    except Exception as e:
#        print(f"\n✗ Unexpected error: {e}")
#        sys.exit(1)

if __name__ == '__main__':
    main()
