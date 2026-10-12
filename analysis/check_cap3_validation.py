"""Check published aggregates only; never train, infer, or reconstruct grid AP."""
from pathlib import Path
import csv,hashlib,json,math,statistics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/cap3-validation-v1'
GROUPS=['M','MG','MR','MGR','GR']
ROLES=['train','validation','nevada','arizona','colorado']
def equal(a,b):
    assert math.isfinite(float(a)) and math.isfinite(float(b))
    assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12),(a,b)
def verify():
    summary=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
    assert summary['evaluation_status']=='not_executed'
    assert summary['validation_use']=='checkpoint_selection'
    assert summary['validation_tiles']==6 and summary['validation_valid_cells']==13943
    assert summary['L_km']==10 and summary['keep_fraction']==1
    assert summary['formal_NN_fits_complete']==15 and summary['formal_RF_target_fits_complete']==10
    assert summary['seeds']==[17,29,43]
    equal(summary['R_role_threshold'],0.8)
    equal(summary['R_cell_qualification_threshold'],0.6)
    with (DATA/'NN_validation.csv').open(encoding='utf-8',newline='') as f:nn=list(csv.DictReader(f))
    assert len(nn)==15
    indexed={}
    for r in nn:
        key=(r['group'],int(r['seed']))
        assert key not in indexed and key[0] in GROUPS and key[1] in [17,29,43]
        equal(r['AP'],(float(r['Gold_AP'])+float(r['Copper_AP']))/2)
        assert all(0<=float(r[k])<=1 for k in ['AP','Gold_AP','Copper_AP'])
        assert 0<int(r['best_step'])<=int(r['updates'])<=10000
        indexed[key]=r
    table=(ROOT/'docs/cap3-training-stage.md').read_text(encoding='utf-8')
    for g in GROUPS:
        rows=[indexed[g,s] for s in [17,29,43]]
        result={'AP_mean':statistics.mean(float(r['AP']) for r in rows),'AP_sample_sd':statistics.stdev(float(r['AP']) for r in rows),'Gold_AP_mean':statistics.mean(float(r['Gold_AP']) for r in rows),'Copper_AP_mean':statistics.mean(float(r['Copper_AP']) for r in rows)}
        for k,v in result.items():equal(v,summary['NN_validation_summary'][g][k])
        displayed='| '+g+' | '+' | '.join(f'{result[k]:.6f}' for k in ['AP_mean','AP_sample_sd','Gold_AP_mean','Copper_AP_mean'])+' |'
        assert displayed in table,(g,'document validation table')
    for g in ['MG','MR','MGR']:
        for seed in [17,29,43]:assert float(indexed[g,seed]['AP'])<float(indexed['M',seed]['AP'])
    with (DATA/'R_role_coverage.csv').open(encoding='utf-8',newline='') as f:coverage=list(csv.DictReader(f))
    assert [r['role'] for r in coverage]==ROLES
    for r in coverage:
        denominator=float(r['original_area_km2'])
        assert denominator>0 and int(r['valid_cells'])==({'train':18555,'validation':13943}.get(r['role'],7500))
        for v in ['cap2','cap3']:
            numerator=float(r['qualified_area_'+v+'_km2'])
            assert 0<=numerator<=denominator
            equal(numerator/denominator,r['fraction_'+v])
        assert float(r['fraction_cap3'])>=0.8
        label={'train':'训练','validation':'验证'}.get(r['role'],r['role'].capitalize())
        displayed=f"| {label} | {100*float(r['fraction_cap2']):.2f}% | {100*float(r['fraction_cap3']):.2f}% | 通过 |"
        assert displayed in table,(r['role'],'document coverage table')
    assert [r['role'] for r in coverage if float(r['fraction_cap2'])<0.8]==['validation','colorado']
    provenance=json.loads((DATA/'provenance.json').read_text(encoding='utf-8'))
    assert len(provenance['sources'])==6
    for source in provenance['sources']:
        assert len(source['sha256'])==64 and all(c in '0123456789abcdef' for c in source['sha256'])
    assert set(provenance['public_assets'])=={'NN_validation.csv','R_role_coverage.csv','summary.json'}
    for name,item in provenance['public_assets'].items():
        payload=(DATA/name).read_bytes()
        assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'],name
    return {'status':'passed','validation_rows':15,'paired_negative_comparisons':9,'coverage_roles':5,'tolerance':1e-12,'scope':'Published aggregate arithmetic, provenance and displayed tables only; not new training, grid AP, raw decoding or independent geological validation.'}

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
