"""Wavespeed AI integration — text-to-3D and image-to-3D.

Delegates to storyforge-studio engine.mesh.wavespeed, injecting
Vivify's API key from local config.
"""
import os

from ..config import WAVESPEED_API_KEY as _VIVIFY_KEY

if _VIVIFY_KEY:
    os.environ["WAVESPEED_API_KEY"] = _VIVIFY_KEY

from engine.mesh.wavespeed import (  # noqa: E402
    text_to_3d,
    image_to_3d,
    is_available as _engine_available,
)


def is_available() -> bool:
    return bool(_VIVIFY_KEY)
