import os
import hashlib

import folder_paths
from nodes import LoadImage
from comfy_extras.nodes_audio import load as load_audio_file
from comfy_api.input_impl import VideoFromFile


class AnyType(str):
    """A special type that compares equal to any other ComfyUI type."""

    def __ne__(self, __value: object) -> bool:
        return False

    def __eq__(self, __value: object) -> bool:
        return True

    def __str__(self) -> str:
        return "*"


ANY = AnyType("*")


class AnyBooleanSwitch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "输入": (ANY,),
                "开关": (
                    "BOOLEAN",
                    {"default": True, "label_on": "开启", "label_off": "关闭"},
                ),
            }
        }

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("输出结果",)
    FUNCTION = "process"
    CATEGORY = "zhang"

    @classmethod
    def VALIDATE_INPUTS(cls, input_types):
        return True

    def process(self, 开关, 输入=None):
        return (输入,) if 开关 else (None,)


class ImageOptionalLoader(LoadImage):
    CATEGORY = "zhang"

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "optional": {
                "image": (sorted(files), {"image_upload": True, "default": ""}),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, image=None):
        if not image:
            return True
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True

    @classmethod
    def IS_CHANGED(cls, image=None):
        if not image:
            return ""
        return super().IS_CHANGED(image)

    def load_image(self, image=None):
        if not image:
            return (None, None)
        return super().load_image(image)


class AudioOptionalLoader:
    CATEGORY = "zhang"
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio_out",)
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        os.makedirs(input_dir, exist_ok=True)
        files = folder_paths.filter_files_content_types(os.listdir(input_dir), ["audio", "video"])
        return {
            "optional": {
                "audio": (sorted(files), {"audio_upload": True, "default": ""}),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, audio=None):
        if not audio:
            return True
        if not folder_paths.exists_annotated_filepath(audio):
            return "Invalid audio file: {}".format(audio)
        return True

    @classmethod
    def IS_CHANGED(cls, audio=None):
        if not audio:
            return ""
        path = folder_paths.get_annotated_filepath(audio)
        hasher = hashlib.sha256()
        with open(path, "rb") as file:
            for block in iter(lambda: file.read(65536), b""):
                hasher.update(block)
        return hasher.hexdigest()

    def execute(self, audio=None):
        if not audio:
            return (None,)
        audio_path = folder_paths.get_annotated_filepath(audio)
        waveform, sample_rate = load_audio_file(audio_path)
        return ({"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate},)


class VideoOptionalLoader:
    CATEGORY = "zhang"
    RETURN_TYPES = ("VIDEO", "IMAGE")
    RETURN_NAMES = ("video_out", "image_out")
    FUNCTION = "execute"

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [name for name in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, name))]
        files = folder_paths.filter_files_content_types(files, ["video"])
        return {
            "optional": {
                "file": (sorted(files), {"video_upload": True, "default": ""}),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, file=None):
        if not file:
            return True
        if not folder_paths.exists_annotated_filepath(file):
            return "Invalid video file: {}".format(file)
        return True

    @classmethod
    def IS_CHANGED(cls, file=None):
        if not file:
            return ""
        return os.path.getmtime(folder_paths.get_annotated_filepath(file))

    def execute(self, file=None):
        if not file:
            return (None, None)
        video = VideoFromFile(folder_paths.get_annotated_filepath(file))
        return (video, video.get_components().images)
