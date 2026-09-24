"""Source U-Net architecture, freshly initialized for each new fit."""
import torch
from torch import nn
from torch.nn import functional as F
def block(i,o):return nn.Sequential(nn.Conv2d(i,o,3,padding=1),nn.GroupNorm(8,o),nn.ReLU(),nn.Conv2d(o,o,3,padding=1),nn.GroupNorm(8,o),nn.ReLU())
class UNet(nn.Module):
    def __init__(self,inputs):
        super().__init__();self.down=nn.ModuleList([block(inputs,32),block(32,64),block(64,128),block(128,256)])
        self.up=nn.ModuleList([block(384,128),block(192,64),block(96,32)]);self.head=nn.Conv2d(32,2,1)
    def forward(self,x):
        skips=[]
        for i,layer in enumerate(self.down):
            x=layer(x);skips.append(x)
            if i<3:x=F.max_pool2d(x,2)
        for layer,skip in zip(self.up,reversed(skips[:-1])):x=layer(torch.cat([F.interpolate(x,size=skip.shape[-2:],mode='bilinear',align_corners=False),skip],1))
        return self.head(x)
