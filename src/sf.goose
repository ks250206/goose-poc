import std;
import os;
import math;
import json;
struct Atom { x: f64, y: f64, z: f64, w: f64 }
struct Job { path: u8[], n: i64 }
struct Result { path: u8[], value: f64 }
fn number(s: u8[:]) -> f64 { let v, ok = parse_flt(s); assert(ok); return v; }
fn calculate(path: u8[:], n: i64) -> f64 {
    var text: u8[>..] = [];
    assert(read_file(path, text));
    var atoms: Atom[>..] = [];
    var active = false;
    for line in split(text, '\n') {
        if line == "# atoms" { active = true; continue; }
        if !active { continue; }
        let w = words(line);
        if w.len == 0 { continue; }
        assert(w.len == 4);
        atoms.push(Atom { number(w[0]), number(w[1]), number(w[2]), number(w[3]) });
    }
    assert(atoms.len > 0);
    var flag: u8[>..] = [];
    let save = env("SF_WRITE", flag) && flag == "1";
    var csv: u8[>..] = [];
    if save { csv.append("h,k,l,re,im,intensity\n"); }
    var total = 0.0;
    for h in -n..n+1 { for k in -n..n+1 { for l in -n..n+1 {
        var re = 0.0; var im = 0.0;
        for a in atoms {
            let p = 6.283185307179586 * (h * a.x + k * a.y + l * a.z);
            re += a.w * cos(p); im += a.w * sin(p);
        }
        let intensity = re * re + im * im;
        total += intensity;
        if save {
            format(csv, h, ",", k, ",", l, ",");
            json::format_number(csv, re); csv.push(',');
            json::format_number(csv, im); csv.push(',');
            json::format_number(csv, intensity); csv.push('\n');
        }
    } } }
    if save {
        var output: u8[>..] = []; format(output, path, ".sf.csv");
        assert(write_file(output, csv));
    }
    return total;
}
thread_fn worker() {
    loop {
        let j = qget<Job>();
        if j.n < 0 { break; }
        qput(Result { path: copy(j.path), value: calculate(j.path, j.n) });
    }
}
fn main() {
    let a = args();
    assert(a.len >= 4);
    let workers, ok = parse_int(a[1]); assert(ok && workers > 0);
    let n, good = parse_int(a[2]); assert(good && n >= 0);
    for i in 3..a.len { qput(Job { path: a[i], n: n }); }
    for i in workers { qput(Job { path: "", n: -1 }); }
    var ids: i64[>..] = [];
    for i in workers { ids.push(thread_spawn(worker)); }
    for i in 3..a.len {
        let r = qget<Result>();
        var out: u8[>..] = [];
        format(out, r.path, " "); json::format_number(out, r.value); print(out);
    }
    for id in ids { thread_wait(id); }
}
