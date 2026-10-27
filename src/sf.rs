use std::{env,fs,thread,sync::{Arc,atomic::{AtomicUsize,Ordering}}};
fn calculate(path: &str,n:i32)->f64 {
 let text=fs::read_to_string(path).unwrap();
 let atoms:Vec<[f64;4]>=text.split_once("# atoms\n").unwrap().1.lines().filter(|l| !l.trim().is_empty()).map(|l| l.split_whitespace().map(|s|s.parse().unwrap()).collect::<Vec<f64>>().try_into().unwrap()).collect();
 assert!(!atoms.is_empty() && atoms.iter().all(|a|a.len()==4));
 let mut total=0.0;
 for h in -n..=n {for k in -n..=n {for l in -n..=n {
 let (mut re,mut im)=(0.0,0.0);
 for a in &atoms {let p=6.283185307179586*(h as f64*a[0]+k as f64*a[1]+l as f64*a[2]);re+=a[3]*p.cos();im+=a[3]*p.sin();}
 total+=re*re+im*im;
 }}} total
}
fn main(){
 let a:Vec<String>=env::args().collect();let workers:usize=a[1].parse().unwrap();let n:i32=a[2].parse().unwrap(); assert!(workers>0 && n>=0 && a.len()>3);
 let paths=Arc::new(a[3..].to_vec());let next=Arc::new(AtomicUsize::new(0));
 let ids:Vec<_>=(0..workers).map(|_| {let paths=paths.clone();let next=next.clone(); thread::spawn(move||loop{let i=next.fetch_add(1,Ordering::Relaxed);if i>=paths.len(){break;}println!("{} {:.12}",paths[i],calculate(&paths[i],n));})}).collect();
 for id in ids {id.join().unwrap();}
}
