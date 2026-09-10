import comfy.utils


class JetImageScale:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": (
                    ["original", "custom", "1:1", "3:2", "4:3", "16:9", "2:3", "3:4", "9:16"],
                    {"default": "original"},
                ),
                "proportional_width": ("INT", {"default": 1, "min": 1, "max": 99999, "step": 1}),
                "proportional_height": ("INT", {"default": 1, "min": 1, "max": 99999, "step": 1}),
                "position": (
                    [
                        "top-left", "top-center", "top-right",
                        "center-left", "center", "center-right",
                        "bottom-left", "bottom-center", "bottom-right",
                    ],
                    {"default": "center"},
                ),
            },
            "optional": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "TUPLE", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "original_size", "width", "height")
    FUNCTION = "crop_image"
    CATEGORY = "zhang"

    @staticmethod
    def _target_aspect_ratio(aspect_ratio, proportional_width, proportional_height, width, height):
        preset_ratios = {
            "1:1": 1.0,
            "3:2": 3.0 / 2.0,
            "4:3": 4.0 / 3.0,
            "16:9": 16.0 / 9.0,
            "2:3": 2.0 / 3.0,
            "3:4": 3.0 / 4.0,
            "9:16": 9.0 / 16.0,
        }
        if aspect_ratio == "custom":
            return proportional_width / proportional_height
        return preset_ratios.get(aspect_ratio, width / height)

    @staticmethod
    def _offset(position, image_width, image_height, crop_width, crop_height):
        if position == "center":
            vertical, horizontal = "center", "center"
        else:
            vertical, horizontal = position.split("-")

        x = 0 if horizontal == "left" else image_width - crop_width if horizontal == "right" else (image_width - crop_width) // 2
        y = 0 if vertical == "top" else image_height - crop_height if vertical == "bottom" else (image_height - crop_height) // 2
        return x, y

    def crop_image(
        self,
        image=None,
        aspect_ratio="original",
        proportional_width=1,
        proportional_height=1,
        position="center",
        mask=None,
    ):
        if image is None:
            return (None, None, None, None, None)

        batch, image_height, image_width, _ = image.shape
        target_aspect = self._target_aspect_ratio(
            aspect_ratio, proportional_width, proportional_height, image_width, image_height
        )
        image_aspect = image_width / image_height

        # Keep the largest rectangle of the requested ratio within the original pixels.
        if image_aspect > target_aspect:
            crop_height = image_height
            crop_width = max(1, int(image_height * target_aspect))
        else:
            crop_width = image_width
            crop_height = max(1, int(image_width / target_aspect))

        x, y = self._offset(position, image_width, image_height, crop_width, crop_height)
        cropped_image = image[:, y:y + crop_height, x:x + crop_width, :]

        if mask is None:
            cropped_mask = image.new_zeros((batch, crop_height, crop_width))
        else:
            if mask.ndim == 2:
                mask = mask.unsqueeze(0)
            if mask.shape[0] == 1 and batch > 1:
                mask = mask.repeat(batch, 1, 1)
            elif mask.shape[0] != batch:
                mask = mask[:batch]
            cropped_mask = mask[:, y:y + crop_height, x:x + crop_width]

        return (cropped_image, cropped_mask, (image_width, image_height), crop_width, crop_height)


class ImageLongSideLimit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "max_long_side": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
            },
            "optional": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "limit_long_side"
    CATEGORY = "zhang"

    def limit_long_side(self, image, max_long_side):
        if image is None:
            return (None,)
        image_height, image_width = image.shape[-3:-1]
        if max(image_width, image_height) <= max_long_side:
            return (image,)

        scale = max_long_side / max(image_width, image_height)
        width = max(1, round(image_width * scale))
        height = max(1, round(image_height * scale))
        resized = comfy.utils.common_upscale(
            image.movedim(-1, 1), width, height, "lanczos", "disabled"
        ).movedim(1, -1)
        return (resized,)


NODE_CLASS_MAPPINGS = {
    "JetImageScale": JetImageScale,
    "ImageLongSideLimit": ImageLongSideLimit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JetImageScale": "Jet Image Crop By Ratio",
    "ImageLongSideLimit": "Image长边限制",
}
