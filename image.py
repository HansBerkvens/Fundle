from dataclasses import dataclass
import requests
import hashlib
import os
import io
from typing import Optional

import torch
from torchvision import transforms
from PIL import Image

from nn_classifier import predict_label

session = requests.session()
transform = transforms.Compose([
    transforms.Resize(256),        # scale short edge to 256
    transforms.CenterCrop(224),    # crop center 224x224
    transforms.ToTensor(),         # → (3, H, W), normalized to [0,1]
])

def url_to_hash(url: str):
    return hashlib.md5(url.encode()).hexdigest()[:10]

@dataclass
class TensorImage:
    listing_id: str
    image_url: str
    hash: str = ''
    tensor: Optional[torch.Tensor] | None = None
    class_prediction: str | None = None
    confidence: float | None = None

    def __post_init__(self):
        self.hash = url_to_hash(self.image_url)
        with session.get(self.image_url, timeout=10) as data:
            b = data.content
        image = Image.open(io.BytesIO(b)).convert("RGB")
        self.tensor = transform(image)

        # import matplotlib.pyplot as plt
        # img = self.tensor.permute(1, 2, 0).numpy()  # (3, H, W) → (H, W, 3)
        # plt.imshow(img)
        # plt.axis("off")
        # manager = plt.get_current_fig_manager()
        # manager.window.state('zoomed')  # Windows
        # plt.show()
        # input('CAN YOU SEE ME NOW?')


        self.class_prediction, self.confidence = predict_label(self.tensor)
        path = os.path.join('images', self.listing_id)
        os.makedirs(path, exist_ok=True)
        torch.save(self.tensor, os.path.join(path, f"{self.hash}.pt"))



