from .nodes import AnyBooleanSwitch, AudioOptionalLoader, ImageOptionalLoader, VideoOptionalLoader

NODE_CLASS_MAPPINGS = {
    "AnyBooleanSwitch": AnyBooleanSwitch,
    "ImageOptionalLoader": ImageOptionalLoader,
    "AudioOptionalLoader": AudioOptionalLoader,
    "VideoOptionalLoader": VideoOptionalLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AnyBooleanSwitch": "万能开关 (Any Boolean Switch)",
    "ImageOptionalLoader": "Image可选加载 (无则禁用)",
    "AudioOptionalLoader": "Audio可选加载 (无则禁用)",
    "VideoOptionalLoader": "Video可选加载 (无则禁用)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
