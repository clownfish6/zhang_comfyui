from .AnyBooleanSwitch import (
    NODE_CLASS_MAPPINGS as _any_switch_nodes,
    NODE_DISPLAY_NAME_MAPPINGS as _any_switch_names,
)
from .JetImageScale import (
    NODE_CLASS_MAPPINGS as _jet_scale_nodes,
    NODE_DISPLAY_NAME_MAPPINGS as _jet_scale_names,
)

NODE_CLASS_MAPPINGS = {
    **_any_switch_nodes,
    **_jet_scale_nodes,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **_any_switch_names,
    **_jet_scale_names,
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
WEB_DIRECTORY = "./web"
