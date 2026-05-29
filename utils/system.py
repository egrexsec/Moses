import torch


def detect_device():
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

        return {
            "device": "cuda",
            "cuda": True,
            "name": gpu_name,
            "gpu": gpu_name,
        }

    return {
        "device": "cpu",
        "cuda": False,
        "name": "CPU Only",
        "gpu": None,
    }
