from typing import Iterable
from torchvision import transforms

labels = "0123456789abcdefghijklmnopqrstuvwxyz"
labels_reverse = {v: k for k, v in enumerate(labels)}

image_transform = transforms.Compose(
    [
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        lambda x: x > 0.5,
        lambda x: x.float(),
    ]
)


def label2string(label: Iterable):
    return "".join(map(lambda x: labels[x], label))
