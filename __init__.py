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

from uuid import uuid1
from typing import Any
from pathlib import Path

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
                "VHS": ("VHS_FILENAMES", {"default": "", "dynamicPrompts":False}),
                "IMAGE": ("IMAGE",),
                "FILE": ("STRING", {"default": "", "dynamicPrompts":False}),
                "URL": ("STRING", {"default": "", "dynamicPrompts":False}),
            }
        }

    def run(self, **kw) -> None:
        url = kw.get('URL', "")
        fpath = None
        output, files = kw.get('VHS', (False, []))
        if output:
            fpath = files[1]
        image = kw.get('IMAGE', None)
        if image is None and fpath is None:
            fpath = kw.get('FILE', "")
        webhook = DiscordWebhook(url=url)
        if fpath is not None and (fpath := Path(fpath)).is_file():
            # upload this file instead of the thing plugged into image.
            with open(fpath, "rb") as f:
                webhook.add_file(file=f.read(), filename=fpath.name)
            webhook.execute()
            return ()

        if len(image.shape) > 3:
            image = [i for i in image]
        else:
            image = [image]
        for img in image:
            if img is None:
                continue
            img = tensor2cv(img)
            c = img.shape[:2] if len(img.shape) > 2 else 1
            if c == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif c == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            #
            fname = f"{uuid1()}.png"
            img = cv2.imencode('.png', img)[1]
            webhook.add_file(file=img, filename=fname)
            response = webhook.execute()
        return ()

# =============================================================================
# === MAPPING ===
# =============================================================================

NODE_CLASS_MAPPINGS = {
    "CozyDiscordPost": CozyDiscordPost,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CozyDiscordPost": "Post to Discord"
}
WEB_DIRECTORY = "./web"
