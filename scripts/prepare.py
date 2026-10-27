"""Normalize small-molecule fractional CIFs, expanding space group to P1."""
import argparse, pathlib, random, math
import gemmi
HEADER = '''data_p1
_cell_length_a 10
_cell_length_b 10
_cell_length_c 10
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P 1'
loop_
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_poc_effective_electrons
# atoms
'''
def write(path, atoms, cell=None):
    header=HEADER
    if cell is not None:
        for tag,value in zip(('length_a','length_b','length_c','angle_alpha','angle_beta','angle_gamma'),cell.parameters):
            import re
            header=re.sub(r'(_cell_'+tag+r') [^\n]+',rf'\g<1> {value:.17g}',header)
    path.write_text(header + ''.join(' '.join(format(v,'.17g') for v in a)+'\n' for a in atoms))

def main():
    p=argparse.ArgumentParser();p.add_argument('inputs',nargs='*');p.add_argument('--out',default='data');p.add_argument('--synthetic',action='store_true');p.add_argument('--atoms',type=int,default=1000);p.add_argument('--files',type=int,default=8);a=p.parse_args()
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if a.synthetic:
        rng=random.Random(42)
        for i in range(a.files):
            write(out/f'synthetic_{i}.cif',[(rng.random(),rng.random(),rng.random(),float(rng.choice([6,7,8,16]))) for _ in range(a.atoms)])
    for i, source in enumerate(a.inputs):
        doc=gemmi.cif.read_file(source)
        if len(doc)!=1: raise ValueError('one data block per file required')
        st=gemmi.make_small_structure_from_block(doc.sole_block())
        if not st.sites: raise ValueError('fractional small-molecule CIF required (mmCIF not supported)')
        sg=gemmi.find_spacegroup_by_name(st.spacegroup_hm)
        if sg is None: raise ValueError('explicit recognized space group required')
        atoms=[]
        for site in st.sites:
            z=site.element.atomic_number
            if not z: raise ValueError('unknown element')
            seen=[]
            for op in sg.operations():
                xyz=tuple(v%1 for v in op.apply_to_xyz([site.fract.x,site.fract.y,site.fract.z]))
                if any(sum(min(abs(x-y),1-abs(x-y))**2 for x,y in zip(xyz,old))<1e-12 for old in seen): continue
                seen.append(xyz)
                row=(*xyz,z*site.occ)
                if not all(math.isfinite(v) for v in row): raise ValueError('non-finite atom')
                atoms.append(row)
        write(out/f'{i}_{pathlib.Path(source).stem}.cif',atoms,st.cell)
if __name__=='__main__':main()
