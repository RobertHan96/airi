from pydantic import Field
from typing import Dict, ClassVar
from .i18n import I18nMixin, Description


class VisionConfig(I18nMixin):
    """
    Configuration for vision/screen capture capabilities.
    """

    enabled: bool = Field(default=False, alias="enabled")
    capture_interval: float = Field(default=5.0, alias="capture_interval")
    prompt: str = Field(
        default="Comment on this screen state naturally.", alias="prompt"
    )

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "enabled": Description(
            en="Enable screen capture vision loop", zh="启用屏幕捕捉视觉循环"
        ),
        "capture_interval": Description(
            en="Interval in seconds between screen captures", zh="屏幕捕捉之间的时间间隔（秒）"
        ),
        "prompt": Description(
            en="Prompt to send to the AI along with the screen capture",
            zh="发送给AI的提示词（附带屏幕截图）",
        ),
    }
