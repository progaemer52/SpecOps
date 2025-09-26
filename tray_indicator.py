#!/usr/bin/env python3
import pystray
from PIL import Image
import threading
import time

class Icon:
    def __init__(self, color='red'):
        self.indicator = None
        self.color = color




    # Function to show the icon
    def show_icon(self):
        self.indicator = pystray.Icon("script_running")
        self.indicator.icon = Image.new('RGB', (22, 22), self.color)
        self.indicator.title = "Script Running"

        # Run in a separate thread so it doesn't block
        threading.Thread(target=self.indicator.run, daemon=True).start()
        print("Icon is now showing in the top bar")


    # Function to hide the icon
    def hide_icon(self):
        if self.indicator:
            self.indicator.stop()
            print("Icon removed from top bar")


# Example of your main script
def main():
    # Show the icon
    icon = Icon()
    icon.show_icon()

    # Your actual script runs here
    print("Your script is running...")
    time.sleep(10)  # Simulating your script running for 10 seconds
    print("Your script has finished")

    # Hide the icon when done
    icon.hide_icon()

if __name__ == "__main__":
    main()