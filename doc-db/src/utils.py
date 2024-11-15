from perfRes import MARCMUSPERF
import seaborn as sn


def make_palette_by_instrument_group():
    def build_label_hex_pairs(prefix: str, color: str) -> dict:
        labels = [v for k, v in MARCMUSPERF.items() if k.startswith(prefix)]
        hex_list = sn.color_palette(color, len(labels)).as_hex()
        return {k: v for k, v in zip(labels, hex_list)}

    # Select labels from Color Brewer library
    woodwinds_kw = build_label_hex_pairs(prefix="w", color="Greens")
    plucked_kw = build_label_hex_pairs(prefix="t", color="YlOrBr")
    bowed_kw = build_label_hex_pairs(prefix="s", color="Greys")
    percussion_kw = build_label_hex_pairs(prefix="p", color="Blues")
    keys_kw = build_label_hex_pairs(prefix="k", color="Purples")
    brass_kw = build_label_hex_pairs(prefix="b", color="Reds")

    # voices_kw = build_label_hex_pairs(prefix="v", color="YlOrBr")

    kw = brass_kw | keys_kw | percussion_kw | bowed_kw | plucked_kw | woodwinds_kw
    return kw
