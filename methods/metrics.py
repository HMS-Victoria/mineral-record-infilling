"""Fixed, threshold-tie AP and area/group arithmetic; no model execution."""
import hashlib
import numpy as np
def ap(y,s):
    y=np.asarray(y);s=np.asarray(s);assert np.isfinite(s).all()
    if not len(y) or not y.sum():return None
    order=np.argsort(-s,kind='stable');yy=y[order];ss=s[order]
    ends=np.r_[np.flatnonzero(ss[1:]!=ss[:-1]),len(ss)-1];tp=np.cumsum(yy,dtype=np.float64)[ends]
    return float(np.sum(np.diff(np.r_[0.,tp])*tp/(ends+1))/yy.sum())
def tie_keys(tile,gx,gy):return np.array([hashlib.sha256(f'checker-area-v1:{t}:{int(x)}:{int(y)}'.encode()).hexdigest() for t,x,y in zip(tile,gx,gy)])
def summarize(y,s,area,ties,cell_groups,zero_block):
    y=np.asarray(y);area=np.asarray(area,np.float64);out=dict(ap=ap(y,s),cells=len(y),positives=int(y.sum()),area_km2=float(area.sum()))
    allgroups=set().union(*cell_groups) if cell_groups else set();order=np.lexsort((ties,-np.asarray(s)));cum=np.cumsum(area[order],dtype=np.float64)
    out['target_groups']=len(allgroups)
    for frac in [.01,.05,.10]:
        n=min(len(order),int(np.searchsorted(cum,frac*area.sum(),side='left'))+1) if len(order) else 0;chosen=order[:n];prefix=str(int(frac*100))
        hit=set().union(*(cell_groups[i] for i in chosen)) if n else set()
        out['coverage_'+prefix]=float(y[chosen].sum()/y.sum()) if y.sum() else None
        out['group_hit_'+prefix]=len(hit)/len(allgroups) if allgroups else None
        out['actual_area_'+prefix]=float(area[chosen].sum()/area.sum()) if area.sum() else None
        if frac==.05:out['zero_positive_block_selected_area_km2']=float(area[chosen][zero_block[chosen]].sum())
    return out
def selfcheck():
    from sklearn.metrics import average_precision_score
    for y,s in [([1,0,1],[.9,.8,.7]),([1,0],[1,1]),([0,1,1,0],[2,2,1,0])]:assert abs(ap(y,s)-average_precision_score(y,s))<1e-12
    assert ap([],[]) is None and ap([0,0],[1,2]) is None
    x=summarize(np.array([1,0,1]),np.array([3,2,1]),np.array([.04,.01,.95]),np.array(['a','b','c']),[{'A'},set(),{'A','B'}],np.array([False,True,False]))
    assert x['coverage_5']==.5 and x['actual_area_5']==.05 and x['group_hit_5']==.5 and x['zero_positive_block_selected_area_km2']==.01
    return dict(status='passed',tests=['threshold ties sklearn','AP empty and zero positive NA','whole last cell area','duplicate group deduplication','zero-positive block selected area'])
if __name__=='__main__':print(selfcheck())
