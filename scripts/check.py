"""Analytic checks: F000 and systematic cancellation, for all four implementations."""
import pathlib, subprocess, sys, tempfile, math
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from prepare import write
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    path=pathlib.Path(tmp)/'two.cif';write(path,[(0.,0.,0.,6.),(.5,0.,0.,6.)])
    for cmd in ([str(root/'src/sf')],[str(root/'src/sf-rust')],[sys.executable,str(root/'src/sf.py')],[sys.executable,str(root/'src/sf_numpy.py')]):
        for w in (1,4):
            for n,expected in ((0,144.),(1,1296.)):
                result=subprocess.check_output(cmd+[str(w),str(n),str(path)],text=True)
                assert math.isclose(float(result.rsplit(' ',1)[1]),expected,rel_tol=1e-12),result
print('All analytic checks passed (4 implementations, 1/4 workers, hmax 0/1).')
# Verify general CIF input normalization and special-position deduplication.
with tempfile.TemporaryDirectory() as tmp:
    src=pathlib.Path(tmp)/'inversion.cif'
    src.write_text('''data_test
_cell_length_a 5
_cell_length_b 5
_cell_length_c 5
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P -1'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
C1 C 0.1 0.2 0.3 1
C2 C 0 0 0 0.5
''')
    out=pathlib.Path(tmp)/'normalized'
    subprocess.check_call([sys.executable,str(root/'scripts/prepare.py'),str(src),'--out',str(out)])
    rows=(out/'0_inversion.cif').read_text().split('# atoms\n')[1].splitlines()
    assert len(rows)==3
    assert sum(float(r.split()[3]) for r in rows)==15
print('CIF symmetry expansion and occupancy checks passed.')
# Inspect actual Goose complex factors, not just their summed checksum.
import csv, os
with tempfile.TemporaryDirectory() as tmp:
    p=pathlib.Path(tmp)/'atoms.cif';write(p,[(0.,0.,0.,6.),(.5,0.,0.,6.)])
    subprocess.check_call([str(root/'src/sf'),'2','1',str(p)],env={**os.environ,'SF_WRITE':'1'},stdout=subprocess.DEVNULL)
    rows=list(csv.DictReader(pathlib.Path(str(p)+'.sf.csv').open()))
    assert len(rows)==27
    for row in rows:
        expected=12. if int(row['h'])==0 else 0.
        assert math.isclose(float(row['re']),expected,abs_tol=1e-12)
        assert abs(float(row['im']))<1e-12
        assert math.isclose(float(row['intensity']),expected**2,abs_tol=1e-12)
print('Per-reflection complex factor CSV checks passed.')
with tempfile.TemporaryDirectory() as tmp:
    subprocess.check_call([sys.executable,str(root/'scripts/prepare.py'),str(root/'fixtures/NaCl.cif'),'--out',tmp])
    p=str(pathlib.Path(tmp)/'0_NaCl.cif')
    # conventional NaCl cell: F000=4*(11+17)=112; hmax=1 sum intensities=17152.
    for n,expected in ((0,12544.),(1,17152.)):
        line=subprocess.check_output([str(root/'src/sf'),'2',str(n),p],text=True)
        assert math.isclose(float(line.rsplit(' ',1)[1]),expected,rel_tol=1e-12)
print('Known NaCl analytic checks passed.')
