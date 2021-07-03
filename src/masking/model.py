import torch
import torch.nn as nn
import torch.optim as optim
import time

from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, models, transforms


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


class ImageClassifierDataset(Dataset):
        
    def __init__(self, image_urls, image_classes):
        self.images = []
        self.labels = []
        
        self.classes = list(set(image_classes))
        self.class_to_label = {c: i for i, c in enumerate(self.classes)}
        
        self.image_size = 224
        self.transforms = transforms.Compose([
            transforms.Resize(self.image_size),
            transforms.CenterCrop(self.image_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        
        for image_url, image_class in zip(image_urls, image_classes):
            image = self._get_image_from_url(image_url)
            transformed_image = self.transforms(image)
            self.images.append(transformed_image)
            
            label = self.class_to_label[image_class]
            self.labels.append(label)
            
    def _get_image_from_url(self, url):
        pass
    
    def __getitem__(self, index):
        return self.images[index], self.labels[index]
    
    def __len__(self):
        return len(self.images)


#### next class
class ImageClassifier(object):
    
    def __init__(self, num_classes):
        self.model = models.resnet18(pretrained=True)
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, num_classes)
        
        self.model = self.model.to(device)
        
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.SGD(self.model.parameters(), lr=0.001, momentum=0.9)
        
        # Decay LR by a factor of 0.1 every 7 epochs
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=7, gamma=0.1)
    
    def save(self, path):
        torch.save(self.model.state_dict(), path)
    
    def load(self, path):
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        
    def train(self, dataloader, num_epochs=25):
        since = time.time()

        self.model.train()
        for epoch in range(num_epochs):
            print('Epoch {}/{}'.format(epoch, num_epochs - 1))
            print('-' * 10)
            
            running_loss = 0.0
            running_corrects = 0    
            # Iterate over data.
            for inputs, labels in dataloader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                self.optimizer.zero_grad()
                outputs = self.model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                self.scheduler.step()

            epoch_loss = running_loss / len(dataloader.dataset)
            epoch_acc = running_corrects.double() / len(dataloader.dataset)

            print('Train Loss: {:.4f} Acc: {:.4f}'.format(epoch_loss, epoch_acc))

        print()
    
        time_elapsed = time.time() - since
        print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))

        return self.model

##### next class
from label_studio_ml.model import LabelStudioMLBase

class ImageClassifierAPI(LabelStudioMLBase):
    
    def __init__(self, **kwargs):
        self.model = ImageClassifier(resources['num_classes'])
        self.model.load(resources['model_path'])
        self.labels = resources['labels']
        
    def predict(self, tasks, **kwargs):
        pass

    def fit(self, completions, **kwargs):
        pass