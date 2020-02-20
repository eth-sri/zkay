from enum import IntEnum
from typing import Optional, Any

from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.transaction.types import AddressValue


def __convert(val: Any, nbits: Optional[int], signed: bool) -> int:
    if isinstance(val, IntEnum):
        val = val.value
    elif isinstance(val, AddressValue):
        val = int.from_bytes(val.val, byteorder='big')

    if nbits is None:  # modulo field prime
        trunc_val = val % bn128_scalar_field
    else:
        trunc_val = val & ((1 << nbits) - 1)  # unsigned representation
        if signed and trunc_val & (1 << (nbits - 1)):
            trunc_val -= (1 << nbits)  # signed representation
    return trunc_val


for i in range(8, 257, 8):
    globals()[f'int{i}'] = lambda x, i=i: __convert(x, i, True)
    globals()[f'uint{i}'] = lambda x, i=i: __convert(x, i, False)
globals()[f'uint'] = lambda x: __convert(x, None, False)
