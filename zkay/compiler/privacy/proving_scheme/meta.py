"""
This module stores metadata about the different proving schemes, which is used by config.py
"""

provingschemeparams = {
    'groth16': {
        'proof_len': 8,
        'external_sol_libs': []
    },
    'gm17': {
        'proof_len': 8,
        'external_sol_libs': ['BN256G2']
    }
}
