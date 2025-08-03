import torch
import torch.nn as nn

class CNNBiLSTM(nn.Module):
    def __init__(self, num_classes=7):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(4),

            nn.Conv2d(64, 256, kernel_size=4, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(4)
        )

        self.lstm = nn.LSTM(input_size=768, hidden_size=256, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(512, 128),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.cnn(x)
        x = x.permute(0, 3, 1, 2)  # (B, W, C, H)
        x = x.reshape(x.size(0), x.size(1), -1)  # (B, W, C*H)
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)
