import torch
from torch.nn import (
    Sequential,
    Linear,
    ReLU,
    Conv2d,
    MaxPool2d,
    BatchNorm2d,
    Flatten,
    Module,
)

from dataset import label2string, image_transform
from PIL import Image
from io import BytesIO


class Net(Module):
    def __init__(self):
        super(Net, self).__init__()

        self.cnn_layers = Sequential(
            Conv2d(1, 16, 3, 1, padding="same"),
            BatchNorm2d(16),
            ReLU(inplace=True),
            Conv2d(16, 16, 1, 1, padding="same"),
            BatchNorm2d(16),
            ReLU(inplace=True),
            MaxPool2d(2, 2),
            Conv2d(16, 64, 3, 1, padding="same"),
            BatchNorm2d(64),
            ReLU(inplace=True),
            Conv2d(64, 64, 1, 1, padding="same"),
            BatchNorm2d(64),
            ReLU(inplace=True),
            MaxPool2d(2, 2),
            Conv2d(64, 128, 3, 1, padding="same"),
            BatchNorm2d(128),
            ReLU(inplace=True),
            Conv2d(128, 128, 1, 1, padding="same"),
            BatchNorm2d(128),
            ReLU(inplace=True),
            MaxPool2d(3, 3),
            Conv2d(128, 256, 3, 1, padding="same"),
            BatchNorm2d(256),
            ReLU(inplace=True),
            MaxPool2d(5, 5),
            Flatten(),
        )

        self.output1 = Sequential(Linear(512, 36))
        self.output2 = Sequential(Linear(512, 36))
        self.output3 = Sequential(Linear(512, 36))
        self.output4 = Sequential(Linear(512, 36))
        self.output5 = Sequential(Linear(512, 36))
        self.output6 = Sequential(Linear(512, 36))

    def forward(self, x):
        x = self.cnn_layers(x)
        return (
            self.output1(x),
            self.output2(x),
            self.output3(x),
            self.output4(x),
            self.output5(x),
            self.output6(x),
        )

    def predict(self, x):
        if type(x) == torch.Tensor:
            result = self.forward(x)
        elif type(x) == str:
            result = self.forward(
                torch.reshape(image_transform(Image.open(x)), (1, 1, 60, 150))
            )
        elif type(x) == bytes:
            result = self.forward(
                torch.reshape(
                    image_transform(Image.open(BytesIO(x))),
                    (1, 1, 60, 150),
                )
            )
        else:
            raise Exception("unknown image format")
        return label2string([torch.argmax(i[0]) for i in result])
