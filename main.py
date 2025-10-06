import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import numpy as np
import torch.optim.lr_scheduler  as lr_scheduler
import wandb

import json

with open('circle_thin.json', 'r') as file:
    boxes = torch.tensor(json.load(file), dtype=float)
    boxes = (boxes-torch.mean(boxes, dim=0)) / torch.std(boxes)
boxes[:, 1] = - boxes[:, 1]
radius = torch.sqrt(2*torch.mean((boxes)**2))
print(radius)
def circle_error(mlp):
    x_t = torch.randn(1000,2)
    ts = np.arange(1000)/1000

    for t in ts:
        a = torch.zeros(x_t.shape[0], 3)
        a[:, 0:2] = x_t
        a[:, 2]  = t

        with torch.no_grad():
            x_t += 0.001 * mlp(a)

    return torch.mean(torch.abs(radius**2-torch.sum(x_t**2, dim=1)))
epochs = 100
lr = 1e-3
run = wandb.init(
    project="smilusion",  # Specify your project
    config={                        # Track hyperparameters and metadata
        "learning_rate": lr,
        "epochs": epochs
    },
    tags= ['circle']
)


class MLP(nn.Module):

    def __init__(self):
        super().__init__()
        
        self.net = nn.Sequential( 
                nn.Linear(3,100),
                nn.ReLU(),
                nn.Linear(100,100),
                nn.ReLU(),
                nn.Linear(100,100),
                nn.ReLU(),
                nn.Linear(100,2)
            ) 
          
    def forward(self, x):
        return self.net(x)




n_samples = 10000
idx = torch.randint(high=len(boxes), size=(n_samples,)) 
samples=boxes[idx]

mlp = MLP()
plt.scatter(samples[:, 0], samples[:, 1])
plt.figure()
optimizer = torch.optim.Adam(mlp.parameters(), lr=lr)

scheduler = lr_scheduler.StepLR(optimizer, step_size=20, gamma = 0.5)
loss_history = []
for epoch in range(epochs):
    samples = samples[torch.randperm(samples.shape[0])]

    
    batch_size = 100
    for i in range(samples.shape[0] // batch_size):
        optimizer.zero_grad()
        t = torch.rand(batch_size)
        eps = torch.randn(batch_size, 2)

        x = t.unsqueeze(1)*samples[i*batch_size : (i+1)*batch_size] + (1-t.unsqueeze(1))*eps
        a = torch.zeros(x.shape[0], 3)
        
        a[:, 0:2] = x
        a[:, 2]  = t

        loss = torch.mean(torch.sum((mlp(a) - samples[i*batch_size : (i+1)*batch_size] + eps)**2, dim=1))

        loss.backward()
        loss_history.append( scheduler.get_last_lr()[0])

        run.log({"loss" : loss.item(), "lr" : scheduler.get_last_lr()[0]})
        optimizer.step()
    run.log({'circle_error' : circle_error(mlp)})
    scheduler.step()

wandb.finish()

x_t = torch.randn(500,2)
ts = np.arange(10000)/10000
# plt.scatter(x_t[:,0].detach().numpy(), x_t[:,1].detach().numpy(), color='red')
for t in ts:
    a = torch.zeros(x_t.shape[0], 3)
    a[:, 0:2] = x_t
    a[:, 2]  = t

    x_t += 0.0001 * mlp(a)
plt.scatter(x_t[:,0].detach().numpy(), x_t[:,1].detach().numpy())
plt.figure()

plt.plot(np.arange(len(loss_history)), loss_history)
plt.show()

