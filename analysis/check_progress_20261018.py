"""Verify published aggregate arithmetic; never reads models or cell predictions."""
from pathlib import Path
import csv,hashlib,itertools,json,math
FAMILIES={'main':6,'latitude':3,'transfer':2}
MODELS={'coverage':('Mean','H','M','HM','HC','HMC'),'magnetic':('H','HM','HMQ','HML')}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def same(a,b):
    if isinstance(b,dict):
        assert isinstance(a,dict) and a.keys()==b.keys()
        for k in b:same(a[k],b[k])
    elif isinstance(b,list):
        assert isinstance(a,list) and len(a)==len(b)
        for x,y in zip(a,b):same(x,y)
    elif type(b) is float:assert type(a) in (int,float) and math.isfinite(a) and abs(a-b)<=1e-12,(a,b)
    else:assert type(a) is type(b) and a==b,(a,b)
def mean(values):
    values=list(values);assert values
    return sum(values)/len(values)
def table(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def calculate_cpu(folder):
    answer={}
    for stage,models in MODELS.items():
        rows=table(folder/(stage+'_metrics.csv'));fixed=table(folder/(stage+'_fixed.csv'))
        assert len(rows)==15*11*len(models) and len(fixed)==14*11*len(models)
        targets=sorted({r['target'] for r in rows});assert len(targets)==15 and 'label_nominal' in targets
        assert set(r['model'] for r in rows)==set(models)
        assert len({(r['fold_id'],r['target'],r['model']) for r in rows})==len(rows)
        assert len({(r['fold_id'],r['evaluation_target'],r['model']) for r in fixed})==len(fixed)
        macro={};fixed_macro={};deltas={};fixed_deltas={}
        for family,nfold in FAMILIES.items():
            macro[family]={};fixed_macro[family]={};deltas[family]={};fixed_deltas[family]={}
            folds={r['fold_id'] for r in rows if r['family']==family};assert len(folds)==nfold
            for target in targets:
                macro[family][target]={}
                for model in models:
                    chosen=[r for r in rows if (r['family'],r['target'],r['model'])==(family,target,model)]
                    assert len(chosen)==nfold and {r['fold_id'] for r in chosen}==folds
                    macro[family][target][model]=mean(float(r['mae_pp']) for r in chosen)
                values=macro[family][target]
                pairs=[('H','HM'),('HC','HMC')] if stage=='coverage' else [('H','HM'),('H','HMQ'),('H','HML'),('HM','HMQ'),('HM','HML')]
                deltas[family][target]={a+'_minus_'+b+'_pp':values[a]-values[b] for a,b in pairs}
                if target=='label_nominal':continue
                fixed_macro[family][target]={}
                for model in models:
                    chosen=[r for r in fixed if (r['family'],r['evaluation_target'],r['model'])==(family,target,model)]
                    assert len(chosen)==nfold and all(r['training_target']=='label_nominal' for r in chosen)
                    fixed_macro[family][target][model]=mean(float(r['mae_pp']) for r in chosen)
                values=fixed_macro[family][target]
                fixed_deltas[family][target]={a+'_minus_'+b+'_pp':values[a]-values[b] for a,b in pairs}
        if stage=='coverage':
            positives={f:sum(all(v>0 for v in d.values()) for t,d in deltas[f].items() if t!='label_nominal') for f in FAMILIES}
            signal=all(all(v>0 for v in deltas[f]['label_nominal'].values()) for f in FAMILIES) and positives['main']/14>=.8
            decisions={'conservative_continue_signal':signal,'alternative_versions_both_positive':positives}
        else:
            decisions={}
            for model in ['HMQ','HML']:
                key='H_minus_'+model+'_pp';fold_positive={}
                for f in FAMILIES:
                    lookup={(r['fold_id'],r['model']):float(r['mae_pp']) for r in rows if r['family']==f and r['target']=='label_nominal'}
                    folds={a for a,b in lookup};fold_positive[f]=sum(lookup[fold,'H']>lookup[fold,model] for fold in folds)
                pos={f:sum(d[key]>0 for t,d in deltas[f].items() if t!='label_nominal') for f in FAMILIES}
                gates={'nominal_all_three_families_positive':all(deltas[f]['label_nominal'][key]>0 for f in FAMILIES),'latitude_at_least_two_of_three_positive':fold_positive['latitude']>=2,'both_transfer_directions_positive':fold_positive['transfer']==2,'every_family_at_least_twelve_of_fourteen_alternates_positive':all(v>=12 for v in pos.values())}
                decisions[model]={'passed':all(gates.values()),'conditions':gates,'nominal_positive_fold_counts':fold_positive,'alternative_positive_version_counts':pos}
        answer[stage]={'macro_mae_pp':macro,'fixed_macro_mae_pp':fixed_macro,'improvements_pp':deltas,'fixed_improvements_pp':fixed_deltas,'decisions':decisions,'fold_evaluations':len(rows),'fixed_evaluations':len(fixed),'ridge_fits':sum(r['model']!='Mean' for r in rows),'prediction_rows_as_sum_of_test_support':sum(int(r['n_test']) for r in rows)}
    return answer
def calculate_tinto(complement,transitions,old_records):
    metrics={(r['seed'],r['model'],r['condition'],r['subset']):r for r in old_records if r['stage']=='v1'}
    assert len(complement)==63 and len(transitions)==252
    seeds=(17,29,43);subsets=('E0','E10','E20');conditions=('clean','missing_vnir','missing_swir','missing_lwir','noise_vnir','noise_swir','noise_lwir')
    assert {(r['seed'],r['condition'],r['subset']) for r in complement}==set(itertools.product(seeds,conditions,subsets))
    clean=[]
    for r in complement:
        assert set(r)=={'seed','condition','subset','points','pairs','joint'}
        n=r['points'];joint=r['joint'];counts=joint['counts'];k=len(joint['available_experts'])
        assert set(joint)=={'available_experts','counts_by_class','class_support','counts','coverage_fraction','all_experts_and_early_wrong_fraction','expert_available_early_wrong_fraction','early_only_correct_fraction'}
        expected_experts=['expert_'+g for g in ['vnir','swir','lwir'] if r['condition']!='missing_'+g]
        assert joint['available_experts']==expected_experts
        assert len(counts)==k+1 and all(len(x)==2 for x in counts) and sum(sum(x) for x in counts)==n
        assert all(type(x) is int and x>=0 for row in counts for x in row)
        assert [sum(sum(x) for x in cls) for cls in joint['counts_by_class']]==joint['class_support']
        assert [[sum(cls[i][j] for cls in joint['counts_by_class']) for j in range(2)] for i in range(k+1)]==counts
        for pair in r['pairs']:
            assert set(pair)=={'left','right','counts_by_class','class_support','proportions_by_class','counts','proportions','contains_absent_expert_bias'}
            assert [sum(x) for x in pair['counts_by_class']]==pair['class_support']
            assert [sum(cls[i] for cls in pair['counts_by_class']) for i in range(4)]==pair['counts']
            assert sum(pair['counts'])==n
            for v,x in zip(pair['proportions'],pair['counts']):same(v,x/n)
            for proportions,counts_by_class,support in zip(pair['proportions_by_class'],pair['counts_by_class'],pair['class_support']):
                for v,x in zip(proportions,counts_by_class):same(v,x/support)
            for model,indices in [(pair['left'],(2,3)),(pair['right'],(1,3))]:same(sum(pair['counts'][i] for i in indices)/n,metrics[r['seed'],model,r['condition'],r['subset']]['accuracy'])
        computed={'coverage_fraction':sum(sum(x) for x in counts[1:])/n,'all_experts_and_early_wrong_fraction':counts[0][0]/n,'expert_available_early_wrong_fraction':sum(x[0] for x in counts[1:])/n,'early_only_correct_fraction':counts[0][1]/n}
        for key,value in computed.items():same(joint[key],value)
        if r['condition']=='clean' and r['subset']=='E0':clean.append({'seed':r['seed'],**computed})
    for r in transitions:
        assert set(r)=={'seed','model','condition','subset','counts_by_class','counts','columns'}
        n=sum(r['counts']);assert all(type(v) is int and v>=0 for v in r['counts'])
        assert [sum(cls[i] for cls in r['counts_by_class']) for i in range(4)]==r['counts']
        same((r['counts'][2]+r['counts'][3])/n,metrics[r['seed'],r['model'],'clean',r['subset']]['accuracy'])
        same((r['counts'][1]+r['counts'][3])/n,metrics[r['seed'],r['model'],r['condition'],r['subset']]['accuracy'])
    return {'clean_E0_by_seed':clean,'clean_E0_seed_mean':{key:mean(r[key] for r in clean) for key in clean[0] if key!='seed'}}
def verify(root):
    folder=root/'results/progress-20261018';summary=read(folder/'summary.json')
    cpu=calculate_cpu(folder);same(cpu,summary['cpu'])
    tinto=calculate_tinto(read(folder/'tinto_complementarity.json')['records'],read(folder/'tinto_transitions.json')['records'],read(root/'results/group-fusion-20261015/aggregate_records.json'));same(tinto,summary['tinto'])
    assert not cpu['coverage']['decisions']['conservative_continue_signal'] and not any(x['passed'] for x in cpu['magnetic']['decisions'].values())
    assert [(cpu[s]['ridge_fits'],cpu[s]['fold_evaluations'],cpu[s]['fixed_evaluations'],cpu[s]['prediction_rows_as_sum_of_test_support']) for s in ['coverage','magnetic']]==[(825,990,924,21060),(660,660,616,14040)]
    for entry in summary['lithology']['registrations'].values():
        for group in ['control','reserved_check']:
            row=entry[group];same(math.sqrt(row['sum_squared_error_m2']/row['n']),row['rmse_m'])
            assert row['n']==(8 if group=='control' else 4)
        assert entry['reserved_check']['rmse_m']<=100 and entry['reserved_check']['max_m']<=200
    current=summary['lithology'];assert current['S_shape']==[78,8] and current['min_feature_area_fraction']==1.0 and current['supervised_fits']==current['supervised_evaluations']==0
    assert current['lithology_training_admitted'] is False and current['independent_lithology_faces'] is None and current['admitted_lithology_cells'] is None
    same(current['support_area_m2'],78*400.0**2)
    for rel,item in read(folder/'provenance.json')['public_assets'].items():
        payload=(root/rel).read_bytes();assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'],rel
    for stage,values in [('coverage',('22.934','20.679','27.595','32.249','24.461','25.963')),('magnetic',('23.251','38.860','32.027','30.135','26.266','33.894'))]:
        text=(root/'docs/cuprite-cpu-results.md').read_text(encoding='utf-8')
        for value in values:assert value in text
    return {'status':'passed','fold_metrics':1650,'fixed_prediction_aggregate_metrics':1540,'tinto_joint_records':63,'tinto_transition_records':252,'new_lithology_fits':0,'relative_registrations':2,'absolute_tolerance':1e-12,'scope':'Aggregate arithmetic, provenance and presentation; no cell predictions, model loading/training, image decoding or independent geological validation.'}
if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parents[1]),ensure_ascii=False,indent=2))
