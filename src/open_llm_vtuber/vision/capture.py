import base64
import mss
import mss.tools
from loguru import logger
from typing import Optional


class ScreenCapture:
    """
    Handles screen capture functionality using mss.
    """

    def __init__(self):
        self.sct = mss.mss()
        logger.info("ScreenCapture initialized.")

    def capture_screen(self, monitor_index: int = 1) -> Optional[str]:
        """
        Captures the specified monitor and returns the image as a base64 encoded string.

        Args:
            monitor_index (int): The index of the monitor to capture. 1 is usually the primary.

        Returns:
            Optional[str]: Base64 encoded JPEG image string, or None if capture fails.
        """
        try:
            # Check if monitor index is valid
            if monitor_index > len(self.sct.monitors) - 1:
                logger.warning(f"Monitor index {monitor_index} out of range. Using primary (1).")
                monitor_index = 1
            
            monitor = self.sct.monitors[monitor_index]
            
            # Grab the data
            sct_img = self.sct.grab(monitor)
            
            # Convert to PIL Image
            from PIL import Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # Resize if too large (e.g. max dimension 768 for PNG size control)
            max_size = 768
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
            # Convert to PNG bytes
            from io import BytesIO
            buffered = BytesIO()
            # optimize=True for PNG might be slow, but compresses better
            img.save(buffered, format="PNG", optimize=True)
            
            # Encode to base64
            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Return with data URI prefix
            return f"data:image/png;base64,{base64_str}"

        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
