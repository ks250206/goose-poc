"""Ideal conventional cells from textbook fractional coordinates; no external dataset."""
import pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from prepare import write
import gemmi
ROOT=pathlib.Path(__file__).resolve().parents[1]
fcc=[(0,0,0),(0,.5,.5),(.5,0,.5),(.5,.5,0)]
structures={
 'NaCl':(5.6402,[(p,'Na') for p in fcc]+[(tuple((v+.5)%1 for v in p),'Cl') for p in fcc]),
 'diamond':(3.567,[(p,'C') for p in fcc]+[(tuple((v+.25)%1 for v in p),'C') for p in fcc]),
 'CsCl':(4.123,[((0,0,0),'Cs'),((.5,.5,.5),'Cl')]),
 'SrTiO3':(3.905,[((0,0,0),'Sr'),((.5,.5,.5),'Ti'),((.5,.5,0),'O'),((.5,0,.5),'O'),((0,.5,.5),'O')])}
raw=ROOT/'fixtures';raw.mkdir(exist_ok=True)
(ROOT/'data').mkdir(exist_ok=True)
for name,(edge,sites) in structures.items():
    header=f'''data_{name}
_cell_length_a {edge}
_cell_length_b {edge}
_cell_length_c {edge}
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P 1'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
'''
    (raw/f'{name}.cif').write_text(header+''.join(f'{el}{i} {el} {p[0]} {p[1]} {p[2]} 1\n' for i,(p,el) in enumerate(sites)))
    st=gemmi.make_small_structure_from_block(gemmi.cif.read_file(str(raw/f'{name}.cif')).sole_block())
    for size in (5,6):
        atoms=[((s.fract.x+i)/size,(s.fract.y+j)/size,(s.fract.z+k)/size,float(s.element.atomic_number*s.occ)) for i in range(size) for j in range(size) for k in range(size) for s in st.sites]
        write(ROOT/'data'/f'{name}_{size}x{size}x{size}.cif',atoms,gemmi.UnitCell(edge*size,edge*size,edge*size,90,90,90))
        print(name,size,len(atoms))
