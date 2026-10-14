"""Recompute public aggregate comparisons; no model or prediction-array execution."""
from pathlib import Path
import csv,hashlib,json,math,statistics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/cap3-formal-v1'
def equal(a,b):
    assert math.isfinite(float(a)) and math.isfinite(float(b))
    assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12),(a,b)
def verify():
    with (DATA/'main_metrics.csv').open(encoding='utf-8',newline='') as f:raw=list(csv.DictReader(f))
    assert len(raw)==2112
    rows=[]
    for r in raw:
        x=dict(r)
        for k in ['L_km','context_repeat','cells','positives']:x[k]=int(r[k])
        x['seed']=int(r['seed']) if r['seed'] else None
        for k in ['keep_fraction','ap','area_km2','coverage_1','coverage_5','coverage_10']:x[k]=float(r[k])
        assert x['cells']==7500 and x['area_km2']==30000
        assert all(0<=x[k]<=1 for k in ['ap','coverage_1','coverage_5','coverage_10'])
        assert x['L_km'] in [10,20] and x['region'] in ['nevada','arizona','colorado'] and x['target'] in ['Gold','Copper']
        expected_positive={('nevada','Gold'):601,('nevada','Copper'):248,('arizona','Gold'):457,('arizona','Copper'):448,('colorado','Gold'):468,('colorado','Copper'):265}
        assert x['positives']==expected_positive[x['region'],x['target']]
        if x['architecture']=='UNet':assert x['group'] in ['M','MG','MR','MGR','GR'] and x['seed'] in [17,29,43]
        elif x['architecture']=='RF':assert x['group'] in ['M','MG','MR','MGR','GR'] and x['seed']==731
        else:assert x['architecture'] in ['kde','nearest'] and x['group']=='M' and x['seed'] is None
        assert x['context_repeat'] in ([101,211,307] if x['keep_fraction'] in [0.5,0.25] else [0])
        assert x['keep_fraction'] in [1,0.5,0.25,0]
        rows.append(x)
    idx={(x['architecture'],x['group'],x['seed'],x['L_km'],x['keep_fraction'],x['context_repeat'],x['region'],x['target']):x for x in rows}
    assert len(idx)==2112
    def pick(arch,group,L,keep):return [r for r in rows if r['architecture']==arch and r['group']==group and r['L_km']==L and r['keep_fraction']==keep]
    def avg(arch,group,L,keep,key='ap'):return statistics.mean(x[key] for x in pick(arch,group,L,keep))
    with (DATA/'comparisons.csv').open(encoding='utf-8',newline='') as f:comparisons=list(csv.DictReader(f))
    assert len(comparisons)==96
    comparison_keys=set()
    for x in comparisons:
        key=(x['architecture'],x['group'],int(x['L_km']),float(x['keep_fraction']))
        assert key not in comparison_keys;comparison_keys.add(key)
        rr=pick(*key)
        expected=(54 if key[3] in [0.5,0.25] else 18) if key[0]=='UNet' else (18 if key[3] in [0.5,0.25] else 6)
        assert int(x['rows'])==len(rr)==expected
        equal(x['AP'],statistics.mean(r['ap'] for r in rr));equal(x['coverage5'],statistics.mean(r['coverage_5'] for r in rr))
    summary=json.loads((DATA/'scientific_summary.json').read_text(encoding='utf-8'))
    science=summary['scientific_summary']
    equal(science['MGR_AP'],avg('UNet','MGR',10,0.25));equal(science['M_AP'],avg('UNet','M',10,0.25))
    equal(science['AP_difference'],science['MGR_AP']-science['M_AP'])
    equal(science['relative_AP_difference'],science['AP_difference']/science['M_AP'])
    equal(science['coverage5_difference'],avg('UNet','MGR',10,0.25,'coverage_5')-avg('UNet','M',10,0.25,'coverage_5'))
    equal(science['full_context_AP_difference'],avg('UNet','MGR',10,1)-avg('UNet','M',10,1))
    primary=[]
    for high in pick('UNet','MGR',10,0.25):
        low=idx['UNet','M',high['seed'],10,0.25,high['context_repeat'],high['region'],high['target']]
        primary.append({'seed':high['seed'],'region':high['region'],'delta':high['ap']-low['ap']})
    assert len(primary)==science['primary_pairs']==54
    for k,v in science['region_marginals'].items():equal(v,statistics.mean(x['delta'] for x in primary if x['region']==k))
    for k,v in science['seed_marginals'].items():equal(v,statistics.mean(x['delta'] for x in primary if x['seed']==int(k)))
    gates={'relative_AP_ge_5pct':science['relative_AP_difference']>=0.05-1e-12,'positive_regions_ge_2':sum(v>1e-12 for v in science['region_marginals'].values())>=2,'positive_seeds_ge_2':sum(v>1e-12 for v in science['seed_marginals'].values())>=2,'coverage5_drop_le_2pp':science['coverage5_difference']>=-0.02-1e-12,'full_context_AP_difference_nonnegative':science['full_context_AP_difference']>=-1e-12}
    assert science['continuation_gates']==gates and science['meets_registered_investment_conditions']==all(gates.values())==False
    assert science['K_admitted']==science['independent_geological_confirmation']==science['calibrated_prospectivity_probability']==False
    counts=summary['execution_counts']
    assert counts['main_metric_rows']==2112 and counts['phase_metric_rows']==4224 and counts['stratified_metric_rows']==21120
    assert counts['independently_recomputed_metric_rows']==sum(counts[k] for k in ['main_metric_rows','phase_metric_rows','stratified_metric_rows'])==27456
    assert counts['logical_views']==704 and counts['physical_prediction_files']==526 and counts['reload_process_checks']==55 and counts['registered_numeric_checks']==58778
    assert counts['new_fits']==0 and counts['GPU_used']==False
    assert sum(x['cells'] for x in summary['support'])==22500 and sum(x['area_km2'] for x in summary['support'])==90000
    page=(ROOT/'docs/cap3-formal-evaluation.md').read_text(encoding='utf-8')
    for g in ['M','MG','MR','MGR','GR']:
        expected='| '+g+' | '+' | '.join(f'{avg(a,g,10,k):.6f}' for a,k in [('UNet',1),('UNet',0.25),('RF',1),('RF',0.25)])+' |'
        assert expected in page,(g,'display table')
    for value in ['0.081193','0.088541','−0.007348','−8.30%','−1.501','0.190499','0.162854','16.97%','0.361258','0.180034']:assert value in page,value
    provenance=json.loads((DATA/'provenance.json').read_text(encoding='utf-8'))
    assert len(provenance['sources'])==7 and len(provenance['public_assets'])==5
    for rel,item in provenance['public_assets'].items():
        p=(ROOT/rel).resolve();assert p.is_relative_to(ROOT.resolve())
        data=p.read_bytes();assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],rel
    for rel,item in provenance['figure_sources'].items():assert provenance['public_assets'][rel]['sha256']==item['source_sha256']
    return {'status':'passed','aggregate_rows':2112,'comparisons':96,'primary_pairs':54,'continued':False,'absolute_tolerance':1e-12,'scope':'Public aggregate arithmetic and attachment hashes only. No model execution, grid-level recomputation, CPU/CUDA comparison or independent geological validation.'}

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
