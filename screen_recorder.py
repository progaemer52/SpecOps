import atexit
import os
import re
import signal
import subprocess
import time

from tray_indicator import Icon


class ScreenRecorder:
    def __init__(self, output_dir="./recordings", color='red'):
        # if output_file is None:
        files = os.listdir(output_dir)
        pattern = re.compile(r"output(\d+).*\.mp4$")
        n = max([int(pattern.search(item).group(1)) for item in files if pattern.search(item)], default=0)
        n += 1
        output_file = f"{output_dir}/output{n}.mp4"

        self.process = None
        self.output_file = output_file
        self.display = os.environ.get('DISPLAY', ':0')
        self.primary_display_info = self._get_primary_display_info()
        self.icon = Icon(color)

    def _get_primary_display_info(self):
        """Get information about the primary display using xrandr"""
        try:
            # Run xrandr and get the output
            result = subprocess.run(['xrandr', '--query'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

            # Parse the output to find primary display
            lines = result.stdout.split('\n')
            primary_pattern = r'(\S+) connected primary (\d+)x(\d+)\+(\d+)\+(\d+)'

            for line in lines:
                match = re.search(primary_pattern, line)
                if match:
                    display_name = match.group(1)
                    width = int(match.group(2))
                    height = int(match.group(3))
                    x_offset = int(match.group(4))
                    y_offset = int(match.group(5))

                    return {
                        'name': display_name,
                        'width': width,
                        'height': height,
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }

            # If no primary display found, return None
            return None

        except Exception as e:
            print(f"Error getting display information: {e}")
            return None

    def start_recording(self, framerate=30):
        """Start recording the primary display"""
        if not self.primary_display_info:
            print("Error: Could not detect primary display information")
            return False

        width = self.primary_display_info['width']
        height = self.primary_display_info['height']
        x_offset = self.primary_display_info['x_offset']
        y_offset = self.primary_display_info['y_offset']

        # Build the FFmpeg command
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-video_size', f'{width}x{height}',
            '-framerate', str(framerate),
            '-i', f'{self.display}+{x_offset},{y_offset}',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-qp', '0',
            self.output_file
        ]

        try:
            print(f"Starting recording of primary display ({width}x{height} at position {x_offset},{y_offset})")
            print(f"Output file: {self.output_file}")
            print("Press Ctrl+C to stop recording")

            # Start the FFmpeg process
            self.process = subprocess.Popen(cmd)

            # Register the cleanup function to handle exit
            atexit.register(self.stop_recording)

            self.icon.show_icon()
            return True

        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def stop_recording(self):
        """Stop the recording by properly terminating the FFmpeg process"""
        if self.process:
            try:
                # Send SIGTERM signal to properly finish the recording
                self.process.send_signal(signal.SIGTERM)
                # Wait for the process to terminate
                self.process.wait(timeout=10)
                print(f"\nRecording stopped. Output saved to: {self.output_file}")

                # Deregister the exit handler
                atexit.unregister(self.stop_recording)

                self.process = None
                return True
            except Exception as e:
                print(f"Error stopping recording: {e}")
                # Force kill if termination failed
                self.process.kill()
                self.process = None
                return False
            finally:
                self.icon.hide_icon()
        return False


def main():
    recorder = ScreenRecorder()

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Record the primary screen on Linux using FFmpeg')
    parser.add_argument('-o', '--output', help='Output file name (default: screen_recording.mp4)')
    parser.add_argument('-f', '--framerate', type=int, default=30, help='Framerate (default: 30)')
    args = parser.parse_args()

    output_file = args.output if args.output else "screen_recording.mp4"
    recorder.start_recording(output_file=output_file, framerate=args.framerate)
    time.sleep(10)
    recorder.stop_recording()


if __name__ == "__main__":
    main()