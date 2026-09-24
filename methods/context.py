"""Protocol 29: whole white blocks and role-wide proxy groups, before slicing."""
import hashlib
from functools import lru_cache
import numpy as np
from scipy.ndimage import distance_transform_edt
from checker import Data,black,grid
from common import digest_arrays
CONTEXTS=[(1.,0),(.5,101),(.5,211),(.5,307),(.25,101),(.25,211),(.25,307),(0.,0)]

@lru_cache(maxsize=None)
def retained_block(km,repeat,i,j):
    return int.from_bytes(hashlib.sha256(f'checker-context-v1:{repeat}:{km}:{i}:{j}'.encode()).digest(),'big')

def available(gx,gy,km,phase,keep,repeat):
    assert (keep,repeat) in CONTEXTS
    white=~black(gx,gy,km,phase)
    if keep==1:return white
    if keep==0:return np.zeros_like(white)
    ii,jj=np.floor_divide(gx,km//2),np.floor_divide(gy,km//2)
    pairs,inverse=np.unique(np.stack([ii.ravel(),jj.ravel()],axis=1),axis=0,return_inverse=True)
    threshold=1<<(255 if keep==.5 else 254)
    kept=np.array([retained_block(km,repeat,int(i),int(j))<threshold for i,j in pairs])
    return white&kept[inverse].reshape(white.shape)

class ContextData(Data):
    def __init__(self,role,pilot=False):
        super().__init__(role,pilot=pilot,encode_geo=False)
        self.role=role;self.scenarios={}
    def role_context(self,km,phase,keep,repeat):
        key=(km,phase,keep,repeat)
        if key not in self.scenarios:
            r=self.records;a=available(r.cell_x.to_numpy(),r.cell_y.to_numpy(),km,phase,keep,repeat)
            hidden=set(r.loc[~a,'group_id']);surviving=a&~r.group_id.isin(hidden).to_numpy()
            self.scenarios[key]=(hidden,surviving,a)
        return self.scenarios[key]
    def ctx(self,i,km,phase,keep=1.,repeat=0):
        hidden,_,_=self.role_context(km,phase,keep,repeat)
        t=self.tiles[i];tid=self.ids[i];gx,gy=grid(tid);valid=t['valid'].astype(bool)
        av=available(gx,gy,km,phase,keep,repeat)&valid;b=black(gx,gy,km,phase)
        rr,cc=t['record_row'],t['record_col'];kept=av[rr,cc]&np.array([g not in hidden for g in t['record_group']],dtype=bool)
        vis=np.zeros((10,50,50),np.float32)
        for k in range(10):
            use=kept&t['record_minerals'][:,k].astype(bool);vis[k,rr[use],cc[use]]=1
        masks=[vis.any(axis=0),vis[0].astype(bool),vis[4].astype(bool)]
        exists=np.array([m.any() for m in masks],bool)
        dist=np.stack([distance_transform_edt(~m,sampling=2) if m.any() else np.full((50,50),np.inf) for m in masks])
        av=av.astype(np.float32)
        return dict(visible=vis,availability=av,score_mask=b&valid,kept=kept,distance_km=dist,exists=exists,context_sha256=digest_arrays(visible=vis,availability=av,kept=kept))

def arrays(data,ids,km,phase,keep,repeat):
    out=np.zeros((len(ids),143,50,50),np.float32)
    for n,i in enumerate(ids):
        c=data.ctx(i,km,phase,keep,repeat);out[n,131]=data.tiles[i]['valid'];out[n,132:142]=c['visible'];out[n,142]=c['availability']
    return out
