from vcdvcd import VCDVCD
import re
from collections import defaultdict

def extract_all_signals(vcd_file):
    vcd = VCDVCD(vcd_file, store_tvs=True)
    pattern = re.compile(r'(.+)\[(\d+)\]')

    groups = defaultdict(list)
    result = []

    for sig in vcd.signals:
        m = pattern.match(sig)
        if m:
            prefix = m.group(1)
            idx = int(m.group(2))
            groups[prefix].append(idx)
        else:
            result.append(sig)

    for prefix, indices in groups.items():
        max_idx = max(indices)
        min_idx = min(indices)
        # On construit la plage de max à min (même s'il y a des trous)
        result.append(f'{prefix}[{max_idx}:{min_idx}]')

    return result

def compare_all_signals(file1, file2):
    sigs1 = extract_all_signals(file1)
    sigs2 = extract_all_signals(file2)

    common_signals = set(sigs1) & set(sigs2)
    only_in_file1 = set(sigs1) - set(sigs2)
    only_in_file2 = set(sigs2) - set(sigs1)

    print("=== Signaux communs ===")
    print(common_signals)

    print("\n=== Signaux uniquement dans le fichier 1 ===")
    print(only_in_file1)

    print("\n=== Signaux uniquement dans le fichier 2 ===")
    print(only_in_file2)


# Utilisation
file1 = "counter_tb.vcd"
file2 = "counter_tb_extended.vcd"

compare_all_signals(file1, file2)
