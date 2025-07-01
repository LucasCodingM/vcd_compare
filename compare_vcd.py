from vcdvcd import VCDVCD
import re
from collections import defaultdict
import argparse

def extract_all_signals_with_refs(vcd_file):
    vcd = VCDVCD(vcd_file, store_tvs=True)
    pattern = re.compile(r'(.+)\[(\d+)\]')
    
    groups = defaultdict(list)
    ref_map = {}
    
    for sig in vcd.signals:
        sig_lower = sig.lower()
        m = pattern.match(sig_lower)
        if m:
            prefix = m.group(1)
            idx = int(m.group(2))
            groups[prefix].append((idx, sig))
        else:
            ref_map[sig_lower] = sig
    
    # Group vector signals into ranges
    for prefix, idx_sig_list in groups.items():
        indices = [i for i, _ in idx_sig_list]
        max_idx = max(indices)
        min_idx = min(indices)
        range_sig = f'{prefix}[{max_idx}:{min_idx}]'
        for _, sig in idx_sig_list:
            ref_map[range_sig] = ref_map.get(range_sig, []) + [sig]
    
    return vcd, ref_map

def reconstruct_vector(vcd, bit_signals):
    """
    Given a list of bit signals (e.g. ['sig[0]', 'sig[1]', ...]) from a VCD,
    reconstruct the full vector as (timestamp, value) tuples.
    Returns a sorted list of (timestamp, vector_value_str).
    """
    # Extract bit index from signal name like 'sig[7]'
    bit_pattern = re.compile(r'.*\[(\d+)\]')
    bits = []
    for sig in bit_signals:
        m = bit_pattern.match(sig)
        if m:
            bits.append((int(m.group(1)), sig))
        else:
            raise ValueError(f"Signal {sig} does not match bit pattern")

    bits.sort(key=lambda x: x[0])  # Sort bits by index ascending (LSB -> MSB)

    # Get all timestamps where any bit changes
    all_timestamps = set()
    bit_tvs = {}
    for bit_idx, sig in bits:
        bit_tvs[bit_idx] = vcd.data[vcd.references_to_ids[sig]].__getattribute__('tv')
        for ts, _ in bit_tvs[bit_idx]:
            all_timestamps.add(ts)
    all_timestamps = sorted(all_timestamps)

    # For each timestamp, find latest value for each bit (<= timestamp)
    def get_latest_val(tvs, ts):
        val = 'x'
        for t, v in tvs:
            if t <= ts:
                val = v
            else:
                break
        return val

    vector_tvs = []
    for ts in all_timestamps:
        bits_val = []
        for bit_idx, _ in bits:
            bits_val.append(get_latest_val(bit_tvs[bit_idx], ts))
        # Combine bits into string: MSB leftmost, LSB rightmost
        vector_str = ''.join(bits_val[::-1])  # Reverse bits list for MSB first
        vector_tvs.append((ts, vector_str))

    return vector_tvs


def compare_tv_data(vcd1, ref_map1, vcd2, ref_map2):
    common_signals = set(ref_map1.keys()) & set(ref_map2.keys())
    print("\n=== Comparing TV data of common signals ===")

    for sig in common_signals:
        refs1 = ref_map1[sig]
        refs2 = ref_map2[sig]

        # refs can be list of bit signals (vector) or single signal string
        # If refs1 or refs2 is a list of strings (vector), reconstruct vector values
        if isinstance(refs1, list):
            tv1 = reconstruct_vector(vcd1, refs1)
        else:
            tv1= vcd1.data[vcd1.references_to_ids[refs1]].__getattribute__('tv')

        if isinstance(refs2, list):
            tv2 = reconstruct_vector(vcd2, refs2)
        else:
            tv2= vcd2.data[vcd2.references_to_ids[refs2]].__getattribute__('tv')

        # Create timestamp union for alignment
        ts_all = sorted(set(ts for ts, _ in tv1) | set(ts for ts, _ in tv2))

        # Helper to get value at timestamp from tv list
        def get_val_at(tv, ts):
            val = None
            for t, v in tv:
                if t <= ts:
                    val = v
                else:
                    break
            return val

        # Compare values at each timestamp
        # differences = []
        for ts in ts_all:
            val1 = get_val_at(tv1, ts)
            val2 = get_val_at(tv2, ts)
            # Normalize widths by zero-padding to the longer length
            if val1 is None: val1 = ''
            if val2 is None: val2 = ''
            max_len = max(len(val1), len(val2))
            val1_padded = val1.zfill(max_len)
            val2_padded = val2.zfill(max_len)

            if val1_padded != val2_padded:
                print(f"\nDifferences in signal {sig}")
                break
                #differences.append((ts, val1_padded, val2_padded))

        #if differences:
            # print(f"\nDifferences in signal {sig}:")
            #for ts, v1, v2 in differences:
           #     print(f"  At time {ts}: file1={v1}, file2={v2}")


def compare_all_signals(file1, file2):
    vcd1, ref_map1 = extract_all_signals_with_refs(file1)
    vcd2, ref_map2 = extract_all_signals_with_refs(file2)

    common_signals = set(ref_map1.keys()) & set(ref_map2.keys())
    only_in_file1 = set(ref_map1.keys()) - set(ref_map2.keys())
    only_in_file2 = set(ref_map2.keys()) - set(ref_map1.keys())

    print("=== Signaux communs ===")
    print(sorted(common_signals))

    print(f"\n=== Signaux uniquement dans le fichier {file1} ===")
    print(sorted(only_in_file1))

    print(f"\n=== Signaux uniquement dans le fichier {file2} ===")
    print(sorted(only_in_file2))

    # Now compare the signal values
    compare_tv_data(vcd1, ref_map1, vcd2, ref_map2)


def main():
    parser = argparse.ArgumentParser(description="Compare signals in two VCD files.")
    parser.add_argument("file1", help="Path to first VCD file")
    parser.add_argument("file2", help="Path to second VCD file")
    args = parser.parse_args()

    compare_all_signals(args.file1, args.file2)

if __name__ == "__main__":
    main()

