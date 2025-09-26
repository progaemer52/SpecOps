import pyautogui
import screeninfo




def screenshot_monitor(primary_monitor):
    screenshot = pyautogui.screenshot(region=(
        primary_monitor.x,
        primary_monitor.y,
        primary_monitor.width,
        primary_monitor.height
    ))
    return screenshot


def get_primary_monitor():
    monitors = screeninfo.get_monitors()
    # Find the primary monitor
    primary_monitor = None
    for monitor in monitors:
        if monitor.is_primary:
            primary_monitor = monitor
            break
    if primary_monitor is None:
        # Fallback to the first monitor if can't determine primary
        primary_monitor = monitors[0]
    return primary_monitor

def screenshot_primary_monitor():
    primary_monitor = get_primary_monitor()
    screenshot = screenshot_monitor(primary_monitor)
    return screenshot