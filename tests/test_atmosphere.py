#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Aaron Dettmann

import pytest
from pytest import approx
import numpy as np

from ambiance import Atmosphere, Constant

from table_data import table_data


def test_invalid_inputs():
    """
    Do not allow strange input
    """

    with pytest.raises(TypeError):
        Atmosphere()

    # Wrong types
    for invalid_input in [None, dict, str]:
        with pytest.raises(TypeError):
            Atmosphere(invalid_input)

    # Empty arrarys
    for invalid_input in [[], (), [[]]]:
        with pytest.raises(ValueError):
            Atmosphere(invalid_input)


def test_out_of_bounds_error():
    """
    Assert that errors are raised when height is too low or too high
    """

    # Minimal and maximal heights
    min_height = Constant.h_min
    max_height = Constant.h_max

    # Make exact values of min and max heights don't raise errors
    for boundary_height in [min_height, max_height]:
        try:
            Atmosphere(boundary_height)
        except ValueError:
            pytest.fail(f"ValueError for height {boundary_height} m...")

    invalid_inputs = [
            min_height-1,
            max_height+1,
            [1, 2, 3, min_height-1],
            [1, 2, 3, min_height-1, 50],
            [1, 2, 3, max_height+1],
            [1, 2, 3, max_height+1, 50],
            ]

    for invalid_input in invalid_inputs:
        with pytest.raises(ValueError):
            Atmosphere(invalid_input)


def test_sealevel():
    """
    Test sealevel conditions
    """

    sealevel = Atmosphere(0)

    # Geopotential and geometric height are equal
    assert sealevel.H == sealevel.h == 0

    # Table 1
    assert sealevel.temperature == 288.15
    assert sealevel.temperature_in_celsius == 15
    assert sealevel.pressure == 1.01325e5
    assert sealevel.density == approx(1.225)
    assert sealevel.grav_accel == 9.80665

    # Table 2
    assert sealevel.speed_of_sound == approx(340.294)
    assert sealevel.dynamic_viscosity == approx(1.7894e-5, 1e-4)
    assert sealevel.kinematic_viscosity == approx(1.4607e-5, 1e-4)
    assert sealevel.thermal_conductivity == approx(2.5343e-2, 1e-4)

    # Table 3
    assert sealevel.pressure_scale_height == approx(8434.5, 1e-4)
    assert sealevel.specific_weight == approx(1.2013e1, 1e-4)
    assert sealevel.number_density == approx(2.5471e25, 1e-4)
    assert sealevel.mean_particle_speed == approx(458.94, 1e-4)
    assert sealevel.collision_frequency == approx(6.9193e9, 1e-4)
    assert sealevel.mean_free_path == approx(6.6328e-8, 1e-4)


def test_table_data_single_value_input():
    """
    Test that data corresponds to tabularised data from "Doc 7488/3"
    """

    for h, entry in table_data.property_dict.items():
        print("="*80)
        print(f"Testing {h} m ...")
        for prop_name, value in entry.items():
            computed = float(getattr(Atmosphere(h), prop_name))
            # print(f"--> ({prop_name}) computed: {computed:.5e}")
            # print(f"--> ({prop_name}) expected: {value:.5e}")
            assert computed == approx(value, 1e-3)


def test_table_data_vector_input():
    """
    Test that vector can be passed as input (instead of single values)
    """

    # "Sorted" vectors
    heights, properties = table_data.get_vectors()
    atmos = Atmosphere(heights)

    for prop_name, exp_values in properties.items():
        computed_values = getattr(atmos, prop_name)
        # print(computed_values)
        # print(exp_values)
        assert np.testing.assert_allclose(computed_values, exp_values, rtol=1e-3) == None

    # Random vectors
    heights, properties = table_data.get_vectors(return_random=True)
    atmos = Atmosphere(heights)
    print(heights)

    for prop_name, exp_values in properties.items():
        computed_values = getattr(atmos, prop_name)
        assert np.testing.assert_allclose(computed_values, exp_values, rtol=1e-3) == None


def test_kelvin_celsius_conversion():
    """
    Test conversion between temperature in degrees Celsius and Kelvin
    """

    # See: https://www.wolframalpha.com/input/?i=-30.00%C2%B0C+in+Kelvin
    # See: https://www.wolframalpha.com/input/?i=236.00%C2%B0C+in+Kelvin
    # See: https://www.wolframalpha.com/input/?i=555.24%C2%B0C+in+Kelvin
    celsius = [-30.00, 236.00, 555.24]
    kelvins = [243.15, 509.15, 828.39]

    # Test single inputs
    for degC, kel in zip(celsius, kelvins):
        assert Atmosphere.t2T(degC) == approx(kel)
        assert Atmosphere.T2t(kel) == approx(degC)

    # Test vector input
    assert Atmosphere.t2T(celsius) == approx(kelvins)
    assert Atmosphere.t2T(celsius[::-1]) == approx(kelvins[::-1])
    assert Atmosphere.T2t(kelvins) == approx(celsius)
    assert Atmosphere.T2t(kelvins[::-1]) == approx(celsius[::-1])

    # Make sure "back and forth" conversion works
    for t in np.arange(-200, 1000, 30):
        assert t == approx(Atmosphere.T2t(Atmosphere.t2T(t)))

    for T in np.arange(0, 1000, 30):
        assert T == approx(Atmosphere.t2T(Atmosphere.T2t(T)))