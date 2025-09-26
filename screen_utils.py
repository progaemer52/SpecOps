import time

import pyautogui
import screeninfo
from rapidfuzz.distance import Levenshtein
from rapidfuzz.fuzz import partial_ratio_alignment
import easyocr
import numpy as np
import textdistance
import pyperclip




def get_text_coord(bbox, primary_monitor, text, text_to_find):
    _, start, end, _, _ =partial_ratio_alignment(text, text_to_find.lower())
    mid = (start + end) // 2
    x_diff = bbox[2][0] - bbox[0][0]
    x = int(bbox[0][0] + x_diff * mid / len(text)) + primary_monitor.x
    y = int((bbox[0][1] + bbox[2][1]) / 2) + primary_monitor.y
    return x, y


def get_edit_distance(text, text_to_find):
    if len(text_to_find) > len(text):
        return textdistance.levenshtein(text_to_find.lower(), text.lower())
    score,ss, se, ds, de = partial_ratio_alignment(text, text_to_find)
    total_len = se + de - ss - ds
    n_match = round(total_len * score / 200)
    return len(text_to_find) - n_match


def click_on_text(text_to_find, single_click, vertical=None, horizontal=None ):
    """
    Finds and clicks on text visible on the primary monitor.

    Args:
        text_to_find (str): The text to search for on screen
        single_click (bool): True for single click, False for double click
        horizontal (str, optional): Preferred horizontal position ('left', 'mid', 'right')
        vertical (str, optional): Preferred vertical position ('top', 'mid', 'bottom')

    Returns:
        dict: Status and message about the operation result
    """
    if not text_to_find.isascii():
        return {
            "status": "error",
            "message": f"Text '{text_to_find}' contains non-ASCII characters, which is not supported. Try clicking on different text or use keyboard shortcuts."
        }

    try:
        # Get information about all monitors
        primary_monitor = get_primary_monitor()

        # Take screenshot of only the primary monitor
        screenshot = screenshot_monitor(primary_monitor)
        screenshot_np = np.array(screenshot)

        # Perform OCR on the screenshot
        reader = easyocr.Reader(['en'])
        results = reader.readtext(screenshot_np,
                                  width_ths=1,
                                  # text_threshold=0.5, low_text=0.35,
                                  canvas_size=5000, paragraph=True, y_ths=0.4)

        # Filter results by confidence threshold and edit distance
        matches = []
        min_edit_distance = float('inf')

        # Calculate Levenshtein distance for each potential match
        for bbox, text in results:
            edit_distance = get_edit_distance(text.lower(), text_to_find.lower())
            edit_dist_2 = Levenshtein.distance(text.lower(), text_to_find.lower())

            max_err = round(len(text_to_find) / 10)
            if len(text_to_find) <= 7:
                max_err = 0
            if edit_distance <= max_err:
                matches.append((bbox, text, edit_distance, edit_dist_2))
                # Track the smallest edit distance found
                min_edit_distance = min(min_edit_distance, edit_distance)

        # Filter to keep only matches with the smallest edit distance
        best_matches = [match for match in matches if match[2] == min_edit_distance]

        # Handle no matches
        if len(best_matches) == 0:
            # find_best_alignment(whole_text.lower(), text_to_find.lower())
            return {
                "status": "error",
                "message": f"Text '{text_to_find}' not found on primary display"
            }

        best_matches.sort(key=lambda x: x[3])
        min_edit_dist_2 = best_matches[0][3]
        best_matches = [match for match in best_matches if match[3] == min_edit_dist_2]
        # if best_matches[0][1] == "Search Google or type a URL":
        #     best_matches = best_matches[:1]

        # Handle multiple best matches with position preferences
        if len(best_matches) > 1 and (horizontal is not None or vertical is not None):
            # Calculate the center point for each match
            match_positions = []
            for match in best_matches:
                bbox = match[0]
                # Get center coordinates
                center_x = (bbox[0][0] + bbox[2][0]) / 2
                center_y = (bbox[0][1] + bbox[2][1]) / 2
                match_positions.append((match, center_x, center_y))

            # Filter matches based on horizontal preference
            if horizontal is not None:
                if horizontal == 'left':
                    match_positions.sort(key=lambda x: x[1])  # Sort by x-coordinate (ascending)
                elif horizontal == 'right':
                    match_positions.sort(key=lambda x: -x[1])  # Sort by x-coordinate (descending)
                elif horizontal == 'mid':
                    # Sort by distance from horizontal center
                    center_x = primary_monitor.width / 2
                    match_positions.sort(key=lambda x: abs(x[1] - center_x))

                # If only horizontal is specified, take the best match
                if vertical is None:
                    best_matches = [match_positions[0][0]]

            # Filter matches based on vertical preference
            if vertical is not None:
                if vertical == 'top':
                    match_positions.sort(key=lambda x: x[2])  # Sort by y-coordinate (ascending)
                elif vertical == 'bottom':  # Note: Request had 'right' but contextually should be 'bottom'
                    match_positions.sort(key=lambda x: -x[2])  # Sort by y-coordinate (descending)
                elif vertical == 'mid':
                    # Sort by distance from vertical center
                    center_y = primary_monitor.height / 2
                    match_positions.sort(key=lambda x: abs(x[2] - center_y))

                # Take the best match
                best_matches = [match_positions[0][0]]

        # Handle multiple best matches (if position preferences didn't resolve)
        if len(best_matches) > 1:
            return {
                "status": "error",
                "message": f"Text '{text_to_find}' found in multiple locations ({len(best_matches)}) with identical edit distance ({min_edit_distance}). "
                           f"Please be more specific or use position preferences (horizontal/vertical)."
            }

        # Get the single match
        match = best_matches[0]
        bbox = match[0]

        # Calculate center point of the bounding box
        # center_x, center_y = get_center(bbox, primary_monitor)
        center_x, center_y = get_text_coord(bbox, primary_monitor, match[1], text_to_find.lower())

        # Move mouse and click
        pyautogui.moveTo(center_x, center_y, duration=0.5)
        if single_click:
            pyautogui.click()
        else:
            pyautogui.doubleClick()

        # print(f"(edit distance: {match[3]})")
        return {
            "status": "success",
            "message": f"Successfully clicked on '{match[1]}' at position ({center_x}, {center_y}) on primary display"
        }

    except Exception as e:
        print(e)
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

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


def type_text(text, cmd):
    if cmd:
        pyautogui.typewrite(text)
        return {
            "status": "success",
            "message": f"Pressed keyboard keys corresponding to {text}"
        }
    try:
        success = False

        pyautogui.typewrite(text)
        time.sleep(2)
        original_clipboard = pyperclip.paste()
        print(f"Original clipboard: {original_clipboard}")
        pyperclip.copy("")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        new_clipboard = pyperclip.paste()
        print(f"New clipboard: {new_clipboard}")
        if text.strip() in new_clipboard and len(new_clipboard) <= 2*len(text):
            print("Success")
            time.sleep(0.5)
            pyautogui.press('right')
            success = True
        else:
            print("Failed")
            if new_clipboard:
                pyautogui.hotkey('ctrl', 'shift', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('esc')
                # pyautogui.hotkey('esc')
            success = False

        pyperclip.copy(original_clipboard)
        if success:
            return {
                "status": "success",
                "message": f"Successfully typed text {text}"
            }
        else:
            return {
                "status": "error",
                "message": f"Keyboard buttons pressed, but text didn't appear on screen. Please select input field and try again."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

def hot_key(keys, repeat):
    try:
        keys_arr = keys.split("+")
        keys_arr = [key.strip() for key in keys_arr]
        keys_arr = [item if item == "_" else item.replace("_", "").lower() for item in keys_arr]

        for key in keys_arr:
            if key not in pyautogui.KEYBOARD_KEYS:
                raise ValueError(f"Invalid key: {key}")

        # if not isinstance(repeat, int):
        repeat = int(repeat)

        for i in range(repeat):
            pyautogui.hotkey(*keys_arr)
        return {
            "status": "success",
            "message": f"Successfully pressed {keys} {repeat} number of times"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

def wait(time_seconds):
    try:
        time.sleep(float(time_seconds))
        return {
            "status": "success",
            "message": f"Successfully waited for {time_seconds} seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

def get_screenshot():
    try:
        return {
            "status": "success",
            "message": "Successfully taken screenshot",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }


def screenshot_primary_monitor():
    primary_monitor = get_primary_monitor()
    screenshot = screenshot_monitor(primary_monitor)
    return screenshot