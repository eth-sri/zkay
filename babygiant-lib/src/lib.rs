extern crate cpython;

use cpython::{PyResult, Python, py_module_initializer, py_fn};

py_module_initializer!(babygiant, |py, m| {
    m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "compute_dlog", py_fn!(py, compute_dlog(x: &str, y: &str)))?;
    Ok(())
});

use ark_ed_on_bn254::{EdwardsAffine as BabyJubJub, Fr, Fq, EdwardsParameters};
use ark_ff::{BigInteger256, field_new, PrimeField, BigInteger};
use ark_ec::{AffineCurve, ProjectiveCurve};
use ark_ec::twisted_edwards_extended::{GroupProjective, GroupAffine};
use hex;

use std::collections::HashMap;

fn baby_giant(max_bitwidth: u64, a: &GroupAffine<EdwardsParameters>, b: &GroupProjective<EdwardsParameters>) -> u64 {
    let m = 1u64 << (max_bitwidth / 2);

    let mut table = HashMap::new();
    for j in 0u64..m {
        // NOTE: equality and hashing (used for HashMap) does not perform as expected
        // for projective representation (because coordinates are ambiguous), so switching
        // to affine coordinates here
        let v = a.mul(Fr::new(BigInteger256::from(j))).into_affine();
        table.insert(v, j);
    }
    let am = a.mul(Fr::new(BigInteger256::from(m)));
    let mut gamma = b.clone();

    for i in 0u64..m {
        if let Some(j) = table.get(&gamma.into_affine()) {
            return i*m + j;
        }
        gamma = gamma - &am;
    }

    panic!("No discrete log found");
}

fn compute_dlog(_py: Python, x: &str, y: &str) -> PyResult<String> {
    let res = do_compute_dlog(x, y);
    Ok(res.to_string())
}

fn parse_le_bytes_str(s: &str) -> BigInteger256 {
    let mut buffer = [0u8; 32];     // 32 bytes for 265 bits

    let v = hex::decode(s).unwrap();
    assert_eq!(v.len(), 32);
    let v = v.as_slice();
    for i in 0..32 {
        buffer[i] = v[i];
    }

    let mut bi = BigInteger256::new([0; 4]);
    bi.read_le(&mut buffer.as_ref()).unwrap();
    return bi;
}

fn do_compute_dlog(x: &str, y: &str) -> u64 {
    // x and y are in little-endian hex string format

    let gx = field_new!(Fq, "11904062828411472290643689191857696496057424932476499415469791423656658550213");
    let gy = field_new!(Fq, "9356450144216313082194365820021861619676443907964402770398322487858544118183");
    let a = BabyJubJub::new(gx, gy);
    // assert!(BabyJubJub::is_on_curve(&a));
    // assert!(BabyJubJub::is_in_correct_subgroup_assuming_on_curve(&a));

    let bx = Fq::from_repr(parse_le_bytes_str(x)).unwrap();
    let by = Fq::from_repr(parse_le_bytes_str(y)).unwrap();

    let b = BabyJubJub::new(bx, by);
    assert!(BabyJubJub::is_on_curve(&b));
    assert!(BabyJubJub::is_in_correct_subgroup_assuming_on_curve(&b));
    let b = b.mul(Fr::new(BigInteger256::from(1)));

    baby_giant(32, &a, &b)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_dlog() {
        let dlog = do_compute_dlog("c53d8d24e6767618b495ed560a0cb4fa3d86c5b86e0d9555ab4ef69cf675511a",
                                   "a7099eb9f4b811bbd4ea1643e449bd1551d732d9ebc81833e5e33a3c2890af14");
        assert_eq!(1, dlog);
    }
}
