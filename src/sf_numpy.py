"""Batched NumPy baseline; cap BLAS threads before import to avoid nested parallelism."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import sys
import numpy as np
from concurrent.futures import ProcessPoolExecutor

def calculate(job):
    path,n=job
    with open(path) as f: text=f.read().split('# atoms\n',1)[1]
    a=np.array([list(map(float,l.split())) for l in text.splitlines() if l.strip()],dtype=np.float64)
    assert a.ndim==2 and a.shape[1]==4
    hkl=np.array([(h,k,l) for h in range(-n,n+1) for k in range(-n,n+1) for l in range(-n,n+1)],dtype=np.float64)
    total=0.0
    for start in range(0,len(hkl),128):
        phase=6.283185307179586*(hkl[start:start+128] @ a[:,:3].T)
        re=np.cos(phase) @ a[:,3];im=np.sin(phase) @ a[:,3]
        total+=float(np.sum(re*re+im*im))
    return path,total
if __name__=='__main__':
    workers,n=map(int,sys.argv[1:3]);assert workers>0 and n>=0
    with ProcessPoolExecutor(workers) as pool:
        for path,value in pool.map(calculate,[(p,n) for p in sys.argv[3:]]):print(path,format(value,'.12f'))
