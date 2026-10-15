"""Check published aggregate confusion matrices and fixed paired comparisons only."""
from pathlib import Path
import csv,hashlib,itertools,json,math
SEEDS=(17,29,43)
GROUPS=('vnir','swir','lwir')
FAMILIES={'clean':('clean',),'noise':tuple('noise_'+g for g in GROUPS),'missing':tuple('missing_'+g for g in GROUPS)}
CONDITIONS=tuple(c for cs in FAMILIES.values() for c in cs)
SUBSETS=('E0','E10','E20')
MODELS={'v1':('expert_vnir','expert_swir','expert_lwir','early','equal','global','dynamic','quality'),'continue':('global_continue',),'features':('early','feature_concat','feature_weighted')}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def same(a,b):
    if isinstance(b,dict):
        assert isinstance(a,dict) and a.keys()==b.keys()
        for k in b:same(a[k],b[k])
    elif isinstance(b,list):
        assert isinstance(a,list) and len(a)==len(b)
        for x,y in zip(a,b):same(x,y)
    elif type(b) is float:
        assert type(a) in (int,float) and math.isfinite(a) and abs(a-b)<=1e-12,(a,b)
    else:assert type(a) is type(b) and a==b,(a,b)
def mean(values):
    values=list(values)
    return None if any(x is None for x in values) else sum(values)/len(values)
def calculate(records,supports):
    expected={(stage,seed,model,c,sub) for stage,models in MODELS.items() for seed,model,c,sub in itertools.product(SEEDS,models,CONDITIONS,SUBSETS)}
    lookup={(r['stage'],r['seed'],r['model'],r['condition'],r['subset']):r for r in records}
    assert len(records)==len(lookup)==756 and set(lookup)==expected
    for r in records:
        matrix=r['confusion'];assert len(matrix)==10 and all(len(row)==10 for row in matrix)
        assert all(type(v) is int and v>=0 for row in matrix for v in row)
        support=[sum(row) for row in matrix];same(r['support'],support);same(support,supports[r['subset']])
        f1=[];iou=[]
        for k in range(10):
            predicted=sum(row[k] for row in matrix);tp=matrix[k][k]
            f1.append(2*tp/(support[k]+predicted) if support[k]+predicted else None)
            iou.append(tp/(support[k]+predicted-tp) if support[k]+predicted-tp else None)
        same(r['class_f1'],f1)
        same(r['macro_f1'],mean(f1) if all(support) else None)
        same(r['mean_iou'],mean(iou) if all(support) else None)
        same(r['accuracy'],sum(matrix[k][k] for k in range(10))/sum(support))
    def score(stage,model,family,sub='E0',seed=None):
        return mean(lookup[stage,s,model,c,sub]['macro_f1'] for s in ((seed,) if seed else SEEDS) for c in FAMILIES[family])
    means={stage:{sub:{m:{f:score(stage,m,f,sub) for f in FAMILIES} for m in models} for sub in SUBSETS} for stage,models in MODELS.items()}
    pairs={'v1':(('v1','dynamic','v1','global'),('v1','dynamic','v1','quality'),('v1','dynamic','v1','early')),'continue':(('v1','dynamic','continue','global_continue'),('continue','global_continue','v1','global'),('continue','global_continue','v1','early')),'features':(('features','feature_weighted','features','feature_concat'),('features','feature_concat','features','early'),('features','feature_weighted','features','early'))}
    comparisons={}
    for stage,ps in pairs.items():
        comparisons[stage]={}
        for sub in SUBSETS:
            paired=[]
            for seed in SEEDS:
                row={'seed':seed}
                for a,m,b,n in ps:
                    for f in FAMILIES:
                        left,right=score(a,m,f,sub,seed),score(b,n,f,sub,seed)
                        row[f+'_'+m+'_minus_'+n]=None if left is None or right is None else left-right
                paired.append(row)
            comparisons[stage][sub]={'paired_seeds':paired,'mean':{k:mean(r[k] for r in paired) for k in paired[0] if k!='seed'}}
    primary={}
    for stage,key in [('v1','dynamic_minus_global'),('continue','dynamic_minus_global_continue'),('features','feature_weighted_minus_feature_concat')]:
        main=comparisons[stage]['E0'];positive=sum(r['noise_'+key]>0 for r in main['paired_seeds'])
        gates=None if stage=='continue' else {'noise_delta_ge_2pp':main['mean']['noise_'+key]>=.02,'positive_seeds_ge_2':positive>=2,'clean_delta_ge_minus_1pp':main['mean']['clean_'+key]>=-.01}
        if stage=='v1':gates['noise_D_minus_Q_nonnegative']=main['mean']['noise_dynamic_minus_quality']>=0
        if stage=='features':gates['noise_weighted_not_weaker_than_matching_early']=main['mean']['noise_feature_weighted_minus_early']>=0
        primary[stage]={'positive_seeds':positive,'gates':gates,'engineering_continue':None if gates is None else all(gates.values()),'diagnostic_only':stage=='continue','not_a_significance_test':True}
    return {'means':means,'comparisons_fraction':comparisons,'primary_decisions':primary}
def verify(root):
    folder=root/'results/group-fusion-20261015'
    records=read(folder/'aggregate_records.json');summary=read(folder/'summary.json')
    computed=calculate(records,summary['class_support']);same(summary['calculated'],computed)
    assert [sum(summary['class_support'][sub]) for sub in SUBSETS]==[2569474,2221982,1765653]
    assert len(summary['class_names'])==10
    with (folder/'metrics.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==756
    for row,record in zip(rows,records):
        for col in ['stage','seed','model','condition','subset','macro_f1','mean_iou','accuracy']:
            assert row[col]==('' if record[col] is None else str(record[col]))
        assert int(row['support_points'])==sum(record['support'])
    diag=read(folder/'weight_diagnostics.json');assert diag['sample_count_per_seed_condition']==8192
    assert len(diag['per_seed_condition'])==21
    for c in CONDITIONS:
        rows=[r for r in diag['per_seed_condition'] if r['condition']==c]
        assert sorted(r['seed'] for r in rows)==list(SEEDS)
        for k in range(3):
            same(diag['three_seed_mean'][c]['mean'][k],mean(r['mean'][k] for r in rows))
            same(diag['three_seed_mean'][c]['mean_within_seed_std'][k],mean(r['std_population'][k] for r in rows))
        if c.startswith('missing_'):
            k=GROUPS.index(c.split('_')[1]);assert all(r['mean'][k]==0 and r['std_population'][k]==0 for r in rows)
        if c.startswith('noise_'):
            k=GROUPS.index(c.split('_')[1])
            for row in rows:
                clean=next(r for r in diag['per_seed_condition'] if r['seed']==row['seed'] and r['condition']=='clean')
                same(row['noisy_group_mean_delta_from_clean'],row['mean'][k]-clean['mean'][k])
            same(diag['three_seed_mean'][c]['noisy_group_mean_delta_from_clean'],mean(r['noisy_group_mean_delta_from_clean'] for r in rows))
    for rel,item in read(folder/'provenance.json')['public_assets'].items():
        payload=(root/rel).read_bytes();assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'],rel
    primary=computed['comparisons_fraction']
    for stage,key,shown in [('v1','noise_dynamic_minus_global','0.267'),('continue','noise_dynamic_minus_global_continue','0.024'),('features','noise_feature_weighted_minus_feature_concat','−0.940'),('features','noise_feature_concat_minus_early','−0.945')]:
        value=100*primary[stage]['E0']['mean'][key]
        assert f'{value:.3f}'.replace('-','−')==shown
        assert shown in (root/'docs/group-fusion-results.md').read_text(encoding='utf-8')
    for model in MODELS['features']:
        for value in computed['means']['features']['E0'][model].values():
            assert f'{100*value:.3f}' in (root/'docs/group-fusion-results.md').read_text(encoding='utf-8')
    return {'status':'passed','aggregate_confusion_matrices':756,'confusion_counts':75600,'published_metric_rows':756,'primary_decisions':computed['primary_decisions'],'weight_diagnostic_records':21,'absolute_tolerance':1e-12,'scope':'Aggregate arithmetic and attachment identities only; no model loading, point predictions or new scientific evaluation.'}
if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parents[1]),ensure_ascii=False,indent=2))
