#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nodes to facilitate communication using modern web infastructre.

* REST - POST, GET
* SOCKET
* JSON - Create, filter and convert
* DISCORD - POST image
"""

from typing import Any
import cv2
import torch
import numpy as np

import json
import base64
import requests

from loguru import logger

# =============================================================================
# === SUPPORT ===
# =============================================================================

def tensor2cv(tensor: torch.Tensor) -> np.ndarray:
    return np.clip(tensor.squeeze().cpu().numpy() * 255, 0, 255).astype(np.uint8)

def request(url:str, data:dict=None, header:dict=None, files:dict=None, post:bool=True) -> requests.Response | None:
    """Make a generic REST request to a service.

    Args:
        url: The URL of the service.
        data: Optional data to send with the request.
        header: Optional headers for the request.
        files: Optional files to send with the request.
        post: Use the default http POST request or GET

    Returns:
        The response object if the request is successful, otherwise None.
    """
    cmd = requests.post if post else requests.get
    try:
        response = cmd(url, files=files, headers=header, json=data)
        if response.status_code == 200:
            return response
    except Exception as e:
        logger.error(e)

    # 503 means we are maybe in spin up mode...
    if response.status_code == 503:
        data = json.loads(response.content)
        if (t := data.get('estimated_time', None)):
            logger.warning(f"[SERVICE] 503 -- estimated start time: {t}")
        logger.warning(data)
    elif response.status_code > 299:
        logger.exception(f"{response.status_code}, {response.text}")
        logger.error(data)
    return None

# =============================================================================
# === NODE ===
# =============================================================================

class ExtNodePostDiscord:
    CATEGORY = "comfy-ext"
    RETURN_TYPES = ()
    FUNCTION = "run"
    OUTPUT_NODE = True

    """
    root: https://discord.com/api/webhooks/
    test route: 1231006315514433650/8-WfatatkgqWIYeniZeuPmYs9TDZ9ucLRyWLWryolMlACcDCe_F3Ho_2ltG4m0HCgIb9
    """

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "optional": {
                "URL": ("STRING", {"default": "", "dynamicPrompts":False}),
                "TITLE": ("STRING", {"default": "title", "dynamicPrompts":False}),
                "DESC": ("STRING", {"default": "description", "dynamicPrompts":False}),
                "COLOR": ("STRING", {"default": "#66FF22", "dynamicPrompts":False}),
                "IMAGE": ("IMAGE",),
            }
        }

    def run(self, **kw) -> None:
        url = kw.get('URL', "")
        url = f"https://discord.com/api/webhooks/{url}"
        image = kw.get('IMAGE', None)
        if image is not None:
            image = tensor2cv(image)
            data = {"image": base64.b64encode(cv2.imencode('.png', image)[1]).decode()}
            request(url, data)

# =============================================================================
# === MAPPING ===
# =============================================================================

NODE_CLASS_MAPPINGS = {
    "ExtNodePostDiscord": ExtNodePostDiscord,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ExtNodePostDiscord": "Post Image on Discord"
}
WEB_DIRECTORY = "./web"
