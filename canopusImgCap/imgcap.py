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

# Predefined sizes
SIZES = {
    'small': (640, 480),
    'medium': (1640, 1232),
    'large': (1920, 1080)
}

def parse_size(size_arg):
    """Parse size argument"""
    if size_arg.lower() in SIZES:
        return SIZES[size_arg.lower()]
    
    raise ValueError(f"Invalid size format. Use one of {list(SIZES.keys())}  (e.g., 640x480)")

def run_command(cmd, description=""):
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

def capture_frame(device, width, height, output_dir, filename, show_results):
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

        if not run_command(cmd1, "setting video format"):
            return False

        # Step 2: Capture raw frame
        cmd2 = [
            'v4l2-ctl',
            '--device', device,
            '--stream-mmap',
            f'--stream-to={temp_raw_path}',
            '--stream-count=1'
        ]

        if not run_command(cmd2, "capturing frame"):
            return False

        # Step 3: Convert raw frame to PNG
        final_path = os.path.join(output_dir, filename)
        cmd3 = [
            'convert',
            '-size', f'{width}x{height}',
            '-depth', '8',
            f'gray:{temp_raw_path}',
            final_path
        ]

        if not run_command(cmd3, "converting to PNG"):
            return False

        print(f"Successfully saved image to: {final_path}")

        if show_results == True:
            cmd4 = [
                'weston-image',
                final_path
            ]
            run_command(cmd4, "showing the results on hdmi")

        return True

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_raw_path)
        except OSError:
            pass

def main():
    parser = argparse.ArgumentParser(
        description='Capture video frame using v4l2-ctl',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Size options:
  small   - 640x480  
  medium  - 1640x1232
  large   - 1920x1080

Examples:
  imgcap /dev/video2 --size medium
  imgcap /dev/video2 --size large --filename my_photo.png --output_dir /home/user/photos
  imgcap /dev/video3 --size large --filename custom_name.png 
        """
    )

    parser.add_argument('device', help='Video device path (e.g., /dev/video2)')
    parser.add_argument('--size',type=str, help='Image size (small/medium/large)')
    parser.add_argument('--filename', type=str, nargs='?', default='frame.png',
                       help='Output filename (default: frame.png)')
    parser.add_argument('--output_dir', type=str, nargs='?', default='.',
                       help='Output directory (default: current directory)')
    parser.add_argument('--show_results', type=bool, default=False,
                        help='Show result in hdmi output')

    # Handle case where script is called with sys.argv directly
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    try:
        width, height = parse_size(args.size)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Validate device exists
    if not os.path.exists(args.device):
        print(f"Error: Device {args.device} does not exist")
        sys.exit(1)

    # Ensure filename has .png extension
    filename = args.filename
    if not filename.lower().endswith('.png'):
        filename += '.png'

    print(f"Capturing from device: {args.device}")
    print(f"Size: {width}x{height}")
    print(f"Output: {os.path.join(args.directory, filename)}")
    print("-" * 50)

    success = capture_frame(args.device,
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

if __name__ == '__main__':
    main()
