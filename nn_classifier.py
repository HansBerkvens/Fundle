import torch.nn as nn
from torchvision import models
import torch

# SECTION globals
PRETRAINED_MODEL = models.resnet50(weights="IMAGENET1K_V2")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMAGE_CLASSES = [
    "interior_other",
    "interior_bathroom",

    "exterior_other",
    "exterior_house_garden",
    "exterior_balcony",

    "other_map",
    "other_banner",
]
NUM_CLASSES = len(IMAGE_CLASSES)

LABEL_MAP = {label: idx for idx, label in enumerate(IMAGE_CLASSES)}
LABEL_MAP_INV = {idx: label for label, idx in LABEL_MAP.items()}

MODEL_PATH = "image_type_classifier.pth"
model = None

# SECTION functions

def build_model() -> nn.Module:
    """Load pretrained ResNet-18 with a NUM_CLASSES head replacing the original classifier.

    The backbone is fully frozen; only the final linear layer is trainable.

    Returns:
        Model moved to DEVICE.
    """
    model = PRETRAINED_MODEL
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    return model.to(DEVICE)


def load_model() -> nn.Module:
    """Load the saved model checkpoint from MODEL_PATH.

    Returns:
        Model in eval mode on DEVICE.
    """
    model = build_model()
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()
    return model
model = load_model()

def predict_labels(tensors, threshold: float | None = None):
    result = []
    for tensor in tensors:
        tensor = tensor.to(DEVICE)
        probs = torch.softmax(model(tensor), dim=1).squeeze(0)
        pred_idx = int(probs.argmax().item())
        predicted_label = LABEL_MAP_INV[pred_idx]
        confidence = round(probs[pred_idx].item(), 4)
        if confidence is not None and confidence >= threshold:
            result.append([tensor, predicted_label, confidence])
    return result

def predict_label(tensor: torch.Tensor):
    tensor = tensor.unsqueeze(0).to(DEVICE)
    probs = torch.softmax(model(tensor), dim=1).squeeze(0)
    pred_idx = int(probs.argmax().item())
    predicted_label = LABEL_MAP_INV[pred_idx]
    confidence = round(probs[pred_idx].item(), 4)
    return predicted_label, confidence
