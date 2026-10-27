"""Linux wait4 CPU accounting and sampled aggregate process-tree RSS (includes shared pages)."""
import os,sys,time,json,pathlib,statistics,platform,subprocess,math,shutil,hashlib
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];os.chdir(ROOT)
FILES=sorted(str(p) for p in pathlib.Path('data').glob('*.cif'))
def measure(cmd):
    assert os.environ.get("SF_WRITE", "0") != "1", "Disable SF_WRITE during benchmarking"
    expected_exe=os.path.realpath(shutil.which(cmd[0]))
    start=time.perf_counter()
    with open('results/last.stdout','w') as out, open('results/last.stderr','w') as err:
        pid=os.fork()
        if pid==0:
            os.dup2(out.fileno(),1);os.dup2(err.fileno(),2);os.execvp(cmd[0],cmd)
        peak=0
        while True:
            try:
                proc=psutil.Process(pid)
                family=([proc]+proc.children(recursive=True)) if proc.exe()==expected_exe else []
                rss=0
                for child in family:
                    try:rss+=child.memory_info().rss
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss)
            except psutil.NoSuchProcess:pass
            done,status,usage=os.wait4(pid,os.WNOHANG)
            if done:break
            time.sleep(.002)
    if status:raise RuntimeError(pathlib.Path('results/last.stderr').read_text())
    values={line.rsplit(' ',1)[0]:float(line.rsplit(' ',1)[1]) for line in pathlib.Path('results/last.stdout').read_text().splitlines()}
    assert set(values)==set(FILES)
    wall=time.perf_counter()-start;cpu=usage.ru_utime+usage.ru_stime
    return dict(wall_s=wall,cpu_s=cpu,cpu_percent=100*cpu/wall,peak_tree_rss_mib=peak/2**20),values

def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 8
    repeats=int(sys.argv[2]) if len(sys.argv)>2 else 3
    assert FILES
    results=[];reference=None
    for workers in (1,4):
        for name,base in [('goose',['src/sf']),('rust',['src/sf-rust']),('python',[sys.executable,'src/sf.py']),('numpy',[sys.executable,'src/sf_numpy.py'])]:
            cmd=base+[str(workers),str(n)]+FILES
            measure(cmd) # warm-up
            for rep in range(repeats):
                row,values=measure(cmd)
                if reference is None:reference=values
                assert all(math.isclose(values[p],reference[p],rel_tol=1e-9,abs_tol=1e-7) for p in FILES),name
                row.update(language=name,workers=workers,repeat=rep);results.append(row)
            print(name,workers,results[-1],flush=True)
    report=dict(platform=platform.platform(),cpu=platform.processor(),cpu_max=pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),hmax=n,files=len(FILES),inputs=[dict(path=f,sha256=hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest(),atoms=len(pathlib.Path(f).read_text().split('# atoms\n')[1].splitlines())) for f in FILES],results=results)
    pathlib.Path('results/benchmark.json').write_text(json.dumps(report,indent=2))
    lines=['| Language | Workers | Wall s | CPU s | CPU % | Tree RSS MiB |','|---|---:|---:|---:|---:|---:|']
    for w in (1,4):
        for lang in ('goose','rust','python','numpy'):
            rows=[r for r in results if r['language']==lang and r['workers']==w]
            vals=[statistics.median(r[k] for r in rows) for k in ('wall_s','cpu_s','cpu_percent','peak_tree_rss_mib')]
            lines.append(f'| {lang} | {w} | '+ ' | '.join(f'{v:.3f}' for v in vals)+' |')
    pathlib.Path('results/summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
if __name__=='__main__':main()
