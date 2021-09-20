import torch

from model import Net


class Predictor:
    def __init__(self) -> None:
        self.model = Net()
        self.model.load_state_dict(
            torch.load("model.pth", map_location=torch.device("cpu"))
        )
        self.model.eval()

    def predict(self, x):
        return self.model.predict(x)
