"""
This script allows you to paste images when using claude code through the wsl.

!! >> THIS SCRIPT IS DESIGNED TO RUN ON WINDOWS ONLY << !!
!! >> I RECOMMEND YOU RUN THIS SCRIPT WITH ADMIN PRIVILEGES. << !!

How to use it ?
1. Install python
2. Create a virtual environment
```
python -m venv .venv
```
3. Activate the virtual environment
Windows:
```
.venv\Scripts\activate
```
Linux:
```
source .venv/bin/activate
```
4. Install the dependencies
```
pip install -r requirements.txt
```
5. Run the script
```
python wsl-paste-workaround.py /path/to/your/project
```

How does it work ?

Basically you provide it the path you are working in. If the path doesn't end with 'sharedclaude',
it will automatically create a 'sharedclaude' subdirectory. Images are saved there and it will
auto paste the @sharedclaude/{filename}.png into the terminal.

Hotkeys:
- Shift+Insert: paste the shorthand path `@sharedclaude/{filename}.png`
- Ctrl+Shift+Insert: paste the full absolute file path to the saved image
"""


import io
import os
import random
import signal
import string
import sys
import threading
import time
import ctypes
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from ctypes import wintypes

try:
    import win32clipboard
    import win32con
    from PIL import Image
except ImportError:
    print("Missing required packages. Please install them with:")
    print("pip install pywin32 pillow")
    sys.exit(1)


def convert_to_wsl_path(windows_path):
    """Convert Windows path to WSL path format.
    
    Args:
        windows_path (str): Windows-style path (e.g., C:\\Users\\...)
        
    Returns:
        str: WSL-style path (e.g., /mnt/c/Users/...)
    """
    path = Path(windows_path).resolve()
    
    if path.drive:
        drive_letter = path.drive[0].lower()
        relative_path = str(path)[2:].replace('\\', '/')
        return f"/mnt/{drive_letter}{relative_path}"
    
    return str(path).replace('\\', '/')

parser = argparse.ArgumentParser(description='Clipboard Image Saver with WSL path support')
parser.add_argument('path', nargs='?', help='Directory path for saving images')
parser.add_argument('--wsl', action='store_true', help='Use WSL/Linux path format instead of Windows format')

args = parser.parse_args()

if args.path:
    base_path = args.path
else:
    base_path = input("Provide the directory path: ")

if not os.path.exists(base_path):
    print(f"Path does not exist: {base_path}")
    exit(0)

USE_WSL_PATHS = args.wsl

normalized_base_path = base_path.rstrip('/\\')
if not normalized_base_path.endswith('sharedclaude'):
    SAVE_DIR = os.path.join(base_path, 'sharedclaude')
else:
    SAVE_DIR = base_path

CLEANUP_INTERVAL = 30
IMAGE_LIFETIME = 5 * 60
HOTKEY_ID = 1
HOTKEY_ID_FULL = 2

shutdown_flag = threading.Event()

MOD_SHIFT = 0x0004
MOD_CONTROL = 0x0002
VK_INSERT = 0x2D
WM_HOTKEY = 0x0312

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


def setup_directory():
    """Create save directory if it doesn't exist."""
    Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)
    print(f"Images will be saved to: {SAVE_DIR}")


def generate_random_name():
    """Generate random filename similar to Node.js version."""
    part1 = "".join(random.choices(string.ascii_lowercase + string.digits, k=13))
    part2 = "".join(random.choices(string.ascii_lowercase + string.digits, k=13))
    return f"{part1}{part2}"


def get_clipboard_image():
    """Get image from Windows clipboard."""
    try:
        win32clipboard.OpenClipboard()

        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
            data = win32clipboard.GetClipboardData(win32con.CF_DIB)
            win32clipboard.CloseClipboard()

            img_buffer = io.BytesIO(data)
            img_buffer.seek(40)

            try:
                image = Image.open(img_buffer)
                return image
            except Exception as e:
                print(f"Error converting clipboard data to image: {e}")
                return None

        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
            win32clipboard.CloseClipboard()
            return get_clipboard_image_alternative()
        else:
            win32clipboard.CloseClipboard()
            return None

    except Exception as e:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        print(f"Error accessing clipboard: {e}")
        return None


def get_clipboard_image_alternative():
    """Alternative method to get clipboard image using PIL directly."""
    try:
        from PIL import ImageGrab

        image = ImageGrab.grabclipboard()
        return image
    except Exception as e:
        print(f"Error with alternative clipboard method: {e}")
        return None


def set_clipboard_text(text):
    """Set text to Windows clipboard.
    Args:
        text (str): The text to set in the clipboard.
    Returns:
        bool: True if the text was successfully set, False otherwise.
    """
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        print(f"Error setting clipboard text: {e}")
        return False


def send_paste():
    """Send Ctrl+V using Windows API.
    Returns:
        bool: True if the paste was successful, False otherwise.
    """
    try:
        user32.keybd_event(0x11, 0, 0, 0)
        user32.keybd_event(0x56, 0, 0, 0)
        user32.keybd_event(0x56, 0, 2, 0)
        user32.keybd_event(0x11, 0, 2, 0)
        return True
    except Exception as e:
        print(f"Error sending paste: {e}")
        return False


def cleanup_old_images():
    """Remove images older than IMAGE_LIFETIME."""
    try:
        save_path = Path(SAVE_DIR)
        if not save_path.exists():
            return

        now = datetime.now()
        cutoff_time = now - timedelta(seconds=IMAGE_LIFETIME)

        for file_path in save_path.glob("*.png"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        print(f"Cleaned up old image: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")

    except Exception as e:
        print(f"Error during cleanup: {e}")


def cleanup_worker():
    """Background thread worker for cleanup."""
    while not shutdown_flag.is_set():
        shutdown_flag.wait(CLEANUP_INTERVAL)
        if not shutdown_flag.is_set():
            cleanup_old_images()


def process_clipboard_image(use_full_path: bool = False):
    """Main function to process clipboard image.

    Args:
        use_full_path (bool): When True, paste the absolute file path. When False,
            paste the shorthand `@sharedclaude/{filename}`.
    """
    try:
        print("Processing clipboard...")

        image = get_clipboard_image()
        if image is None:
            print("No image found in clipboard")
            return

        filename = f"{generate_random_name()}.png"
        filepath = Path(SAVE_DIR) / filename

        if image.mode in ("RGBA", "LA"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(
                image, mask=image.split()[-1] if image.mode == "RGBA" else None
            )
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        image.save(filepath, "PNG")
        print(f"Image saved: {filepath}")

        text_to_paste = (
            str(filepath.resolve()) if use_full_path else f"@sharedclaude/{filename}"
        )
        
        if USE_WSL_PATHS and use_full_path:
            text_to_paste = convert_to_wsl_path(text_to_paste)

        if set_clipboard_text(text_to_paste):
            print(f"Clipboard updated with path: {text_to_paste}")

            time.sleep(0.15)
            if send_paste():
                print("Pasted file path")
            else:
                print("Failed to paste file path")
        else:
            print("Failed to update clipboard")

    except Exception as e:
        print(f"Error processing clipboard image: {e}")


def setup_hotkey():
    """Register global hotkeys.
    - Shift+Insert for shorthand path paste
    - Ctrl+Shift+Insert for full absolute path paste

    Returns:
        bool: True if at least one hotkey was successfully registered, False otherwise.
    """
    registered_any = False

    if user32.RegisterHotKey(None, HOTKEY_ID, MOD_SHIFT, VK_INSERT):
        registered_any = True
    else:
        print("Failed to register Shift+Insert. It may be in use by another application.")

    if user32.RegisterHotKey(None, HOTKEY_ID_FULL, MOD_SHIFT | MOD_CONTROL, VK_INSERT):
        registered_any = True
    else:
        print(
            "Failed to register Ctrl+Shift+Insert. It may be in use by another application."
        )

    return registered_any


def cleanup_hotkey():
    """Unregister global hotkeys."""
    user32.UnregisterHotKey(None, HOTKEY_ID)
    user32.UnregisterHotKey(None, HOTKEY_ID_FULL)


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully.
    Args:
        signum (int): The signal number.
        frame (frame): The current stack frame.
    """
    print("\nReceived interrupt signal. Shutting down...")
    shutdown_flag.set()
    cleanup_hotkey()
    sys.exit(0)


def main():
    """Main application loop."""
    print("Clipboard Image Saver (Python Version)")
    print("=" * 40)

    signal.signal(signal.SIGINT, signal_handler)

    setup_directory()

    if not setup_hotkey():
        sys.exit(1)

    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

    print("Images will be auto-deleted after 5 minutes")
    print("Press Shift+Insert to paste @sharedclaude/<filename>")
    if USE_WSL_PATHS:
        print("Press Ctrl+Shift+Insert to paste full WSL path (Linux format)")
    else:
        print("Press Ctrl+Shift+Insert to paste full Windows path")
    print("Press Ctrl+C to stop")
    print()

    msg = MSG()
    try:
        while not shutdown_flag.is_set():
            bRet = user32.PeekMessageA(ctypes.byref(msg), None, 0, 0, 1)

            if bRet:
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    print("Shift+Insert detected!")
                    threading.Thread(
                        target=process_clipboard_image, daemon=True
                    ).start()
                elif msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID_FULL:
                    print("Ctrl+Shift+Insert detected!")
                    threading.Thread(
                        target=process_clipboard_image, args=(True,), daemon=True
                    ).start()
                elif msg.message == 0x0012:
                    break

                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageA(ctypes.byref(msg))

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping hotkey monitor...")
    finally:
        shutdown_flag.set()
        cleanup_hotkey()
        print("Hotkey unregistered. Exiting.")


if __name__ == "__main__":
    main()