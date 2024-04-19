#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nodes to facilitate communication using modern web infrastructure.

* REST - POST, GET
* SOCKET
* JSON - Create, filter and convert
* DISCORD - POST image
"""


import cv2
import torch
import requests
import numpy as np
from discord_webhook import DiscordWebhook

import base64
from uuid import uuid1
from typing import Any

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
        logger.error(data.keys())
        logger.exception(f"{response.status_code}, {response.text}")
    return None

# =============================================================================
# === NODE ===
# =============================================================================

class CozyDiscordPost:
    CATEGORY = "comfy-ext"
    RETURN_TYPES = ()
    FUNCTION = "run"
    OUTPUT_NODE = True
    """
    root: https://discord.com/api/webhooks/
    """

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, Any]]:
        return {
            "required": {},
            "optional": {
                "URL": ("STRING", {"default": "", "dynamicPrompts":False}),
                "IMAGE": ("IMAGE",),
            }
        }

    def run(self, **kw) -> None:
        url = kw.get('URL', "")
        image = kw.get('IMAGE', None)
        if image is not None:
            image = tensor2cv(image)
            c = image.shape[:2] if len(image.shape) > 2 else 1
            if c == 1:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif c == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

            webhook = DiscordWebhook(url=url)
            fname = f"{uuid1()}.png"

            image = cv2.imencode('.png', image)[1]
            webhook.add_file(file=image, filename=fname)
            response = webhook.execute()
            # data = {"file": base64.b64encode(cv2.imencode('.png', image)[1]).decode()}
            # dont care about a response?
            # request(url, data)
        return ()

# =============================================================================
# === MAPPING ===
# =============================================================================

NODE_CLASS_MAPPINGS = {
    "CozyDiscordPost": CozyDiscordPost,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CozyDiscordPost": "Post Image on Discord"
}
WEB_DIRECTORY = "./web"
