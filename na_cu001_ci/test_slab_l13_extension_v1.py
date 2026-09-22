#!/usr/bin/env python3
from slab_l13_extension_v1 import strict_layer_selection


def row(value):
    return {"bulk_referenced_surface_excess_ev_per_surface_atom": value}


def make(values):
    return {(layer, 12.0, 16): row(value) for layer, value in values.items()}


def test_selects_11_when_l13_is_close():
    result = strict_layer_selection(make({5: 0.620, 7: 0.615, 9: 0.6130, 11: 0.6120, 13: 0.6114}), 12.0, 16)
    assert result["selected_layers"] == 11
    assert result["eligible_layers"] == [11]


def test_selects_9_only_when_all_thicker_values_are_close():
    result = strict_layer_selection(make({5: 0.620, 7: 0.616, 9: 0.6130, 11: 0.6125, 13: 0.6124}), 12.0, 16)
    assert result["selected_layers"] == 9
    assert result["eligible_layers"] == [9, 11]


def test_holds_when_11_vs_13_exceeds_threshold():
    result = strict_layer_selection(make({5: 0.620, 7: 0.616, 9: 0.6130, 11: 0.6120, 13: 0.6108}), 12.0, 16)
    assert result["selected_layers"] is None
    assert result["eligible_layers"] == []


def main():
    test_selects_11_when_l13_is_close()
    test_selects_9_only_when_all_thicker_values_are_close()
    test_holds_when_11_vs_13_exceeds_threshold()
    print("slab_l13_extension_v1 tests: PASS")


if __name__ == "__main__":
    main()
