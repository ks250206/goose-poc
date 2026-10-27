"""Scalar float64 baseline; processes avoid the CPython GIL."""
import sys
import math
from concurrent.futures import ProcessPoolExecutor

def calculate(job):
    path, n = job
    text = open(path).read().split('# atoms\n', 1)[1]
    atoms = [tuple(map(float, line.split())) for line in text.splitlines() if line.strip()]
    assert atoms and all(len(a) == 4 for a in atoms)
    total = 0.0
    for h in range(-n, n+1):
        for k in range(-n, n+1):
            for l in range(-n, n+1):
                re = im = 0.0
                for x,y,z,w in atoms:
                    p = 6.283185307179586 * (h*x+k*y+l*z)
                    re += w*math.cos(p)
                    im += w*math.sin(p)
                total += re*re+im*im
    return path, total

if __name__ == '__main__':
    workers, n = map(int, sys.argv[1:3])
    assert workers > 0 and n >= 0 and len(sys.argv) > 3
    with ProcessPoolExecutor(workers) as pool:
        for path, value in pool.map(calculate, [(p,n) for p in sys.argv[3:]]):
            print(path, format(value, '.12f'))
