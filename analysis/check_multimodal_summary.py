"""Verify published aggregate arithmetic and hashes; no source data or models."""
from pathlib import Path
import csv
import hashlib
import json
import math


def verify(root):
    folder = root / 'results/mm-reduced-v1'
    summary = json.loads((folder / 'coverage_summary.json').read_text(encoding='utf-8'))
    rows = list(csv.DictReader((folder / 'R_role_missingness.csv').open(encoding='utf-8-sig', newline='')))
    roles = ['train', 'validation', 'nevada', 'arizona', 'colorado']
    assert len(rows) == 5 and [r['role'] for r in rows] == roles
    assert sum(summary['scope_tiles'].values()) == 27
    assert summary['R']['threshold'] == 0.8
    assert summary['R']['cell_qualification_threshold'] == 0.6
    assert summary['G']['threshold'] == 0.9
    failed = []
    for row, recorded in zip(rows, summary['R']['groups']):
        role = row['role']
        assert role == recorded['role']
        area = float(row['original_area_km2'])
        qualified = float(row['qualified_area_km2'])
        fraction = qualified / area
        assert math.isclose(fraction, float(row['coverage_fraction']), rel_tol=0, abs_tol=1e-12)
        assert math.isclose(fraction, recorded['fraction'], rel_tol=0, abs_tol=1e-12)
        assert math.isclose(area, recorded['original_area_km2'], rel_tol=0, abs_tol=1e-8)
        assert math.isclose(qualified, recorded['area_in_cells_with_qualified_fraction_ge_60pct_km2'], rel_tol=0, abs_tol=1e-8)
        assert math.isclose(area - qualified, float(row['unqualified_area_km2']), rel_tol=0, abs_tol=1e-8)
        assert math.isclose(max(0, area * 0.8 - qualified), float(row['shortfall_to_80pct_km2']), rel_tol=0, abs_tol=1e-8)
        assert int(row['valid_cells']) == recorded['valid_cells']
        assert 0 <= int(row['qualified_cells']) <= int(row['valid_cells'])
        passed = fraction >= 0.8
        assert recorded['passed'] == passed == (row['passed_80pct'] == 'True')
        if not passed:
            failed.append(role)
        geo = summary['G']['groups'][role]
        assert math.isclose(geo['covered_area_km2'] / geo['effective_area_km2'], geo['fraction'], rel_tol=0, abs_tol=1e-12)
        assert geo['passes_90_percent'] == (geo['fraction'] >= 0.9) == True
    assert failed == ['validation', 'colorado']
    assert summary['R']['status'] == 'failed'
    assert summary['joint_input_audit'] == 'not_run_after_R_failure'
    assert all(value == 0 for value in summary['model_counts'].values())
    provenance = json.loads((folder / 'provenance.json').read_text(encoding='utf-8'))
    for asset in provenance['assets']:
        data = (root / asset['file']).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        assert len(data) == asset['bytes']
        assert digest == asset['published_sha256']
        if asset['copy_policy'].startswith('byte-identical'):
            assert digest == asset['source_sha256']
    return {'status': 'passed', 'roles_checked': 5, 'failed_R_roles': failed,
            'assets_checked': len(provenance['assets']),
            'scope': 'Published aggregate arithmetic and file hashes only; no raw decoding or scientific rerun.'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), ensure_ascii=False))
