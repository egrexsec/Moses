import torch


def detect_device():
    if torch.cuda.is_available():
        return {
            "device": "cuda",
            "gpu": torch.cuda.get_device_name(0)
        }

    return {
        "device": "cpu",
        "gpu": None
    }
