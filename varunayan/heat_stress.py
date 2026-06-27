"""Heat stress index calculations."""

import math
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd


def relative_humidity_from_dewpoint(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Calculate relative humidity from temperature and dewpoint using Magnus-Tetens formula.

    Args:
        temp_c: Air temperature in Celsius
        dewpoint_c: Dewpoint temperature in Celsius

    Returns:
        Relative humidity as percentage (0-100)
    """
    a = 17.625
    b = 243.04
    rh = (
        100
        * np.exp((a * dewpoint_c) / (b + dewpoint_c))
        / np.exp((a * temp_c) / (b + temp_c))
    )
    result = np.clip(rh, 0, 100)
    if isinstance(temp_c, pd.Series):
        return pd.Series(result)
    return result  # type: ignore[return-value]


def vapor_pressure_from_dewpoint(
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Calculate vapor pressure from dewpoint using Magnus formula.

    Args:
        dewpoint_c: Dewpoint temperature in Celsius

    Returns:
        Vapor pressure in hPa

    Reference: Bolton (1980), Mon. Wea. Rev. 108, 1046-1053.
    """
    # Shared by humidex and WBGT so both languages agree on e.
    return 6.112 * np.exp(17.67 * dewpoint_c / (dewpoint_c + 243.5))


def wet_bulb_temperature(
    temp_c: Union[float, np.ndarray, pd.Series],
    rh: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Calculate wet bulb temperature using Stull (2011) empirical formula.

    Reference: Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity
    and Air Temperature. J. Appl. Meteor. Climatol., 50, 2267-2269.

    Args:
        temp_c: Air temperature in Celsius
        rh: Relative humidity as percentage (0-100)

    Returns:
        Wet bulb temperature in Celsius
    """
    # Clamp to Stull's stated validity window (RH 5-99%) to avoid extrapolation.
    rh = np.clip(rh, 5, 99)
    tw = (
        temp_c * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
        + np.arctan(temp_c + rh)
        - np.arctan(rh - 1.676331)
        + 0.00391838 * (rh**1.5) * np.arctan(0.023101 * rh)
        - 4.686035
    )
    return tw


def wet_bulb_from_dewpoint(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """Calculate wet bulb temperature from temperature and dewpoint."""
    rh = relative_humidity_from_dewpoint(temp_c, dewpoint_c)
    return wet_bulb_temperature(temp_c, rh)


def heat_index(
    temp_c: Union[float, np.ndarray, pd.Series],
    rh: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """Calculate Heat Index using the Rothfusz NWS equation.

    Args:
        temp_c: Air temperature in Celsius
        rh: Relative humidity as percentage (0-100)

    Returns:
        Heat index in Celsius
    """
    temp_f = np.asarray(temp_c, dtype=float) * 9 / 5 + 32
    rh = np.clip(rh, 0, 100)

    # Full Rothfusz regression (used when temp_f >= 80).
    hi_full = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f**2
        - 0.05481717 * rh**2
        + 0.00122874 * temp_f**2 * rh
        + 0.00085282 * temp_f * rh**2
        - 0.00000199 * temp_f**2 * rh**2
    )

    # NWS adjustments for the low-RH and high-RH corners of the regression.
    # The sqrt argument can go negative outside the adjustment's temp band; clip
    # to 0 there (those rows are discarded by the np.where conditions below).
    sqrt_arg = np.clip((17 - np.abs(temp_f - 95)) / 17, 0.0, None)
    adj_low = -((13 - rh) / 4) * np.sqrt(sqrt_arg)
    adj_high = ((rh - 85) / 10) * ((87 - temp_f) / 5)
    adj = np.where(
        (rh < 13) & (temp_f >= 80) & (temp_f <= 112),
        adj_low,
        np.where((rh > 85) & (temp_f >= 80) & (temp_f <= 87), adj_high, 0.0),
    )
    hi_full = hi_full + adj

    # Steadman simple form for cooler conditions (temp_f < 80).
    hi_simple = 0.5 * (temp_f + 61.0 + (temp_f - 68.0) * 1.2 + rh * 0.094)

    hi_f = np.where(temp_f < 80, hi_simple, hi_full)
    hi_c = (hi_f - 32) * 5 / 9

    # Preserve scalar-in / scalar-out behaviour.
    if np.isscalar(temp_c) and np.ndim(hi_c) == 0:
        return float(hi_c)
    return hi_c


def heat_index_from_dewpoint(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """Calculate heat index from temperature and dewpoint."""
    rh = relative_humidity_from_dewpoint(temp_c, dewpoint_c)
    return heat_index(temp_c, rh)


def wbgt_simple(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Estimate Wet Bulb Globe Temperature using the Australian BoM approximation.

    Closed-form WBGT from air temperature and humidity alone.
    Standard estimator in climate-epidemiology when wind/radiation are unavailable.

    Reference: Australian Bureau of Meteorology approximation of WBGT
    (Steadman-based); see ACSM heat guidelines.

    Args:
        temp_c: Air temperature in Celsius
        dewpoint_c: Dewpoint temperature in Celsius

    Returns:
        WBGT in Celsius
    """
    e = vapor_pressure_from_dewpoint(dewpoint_c)  # hPa
    return 0.567 * temp_c + 0.393 * e + 3.94


def wbgt_shade(
    temp_c: Union[float, np.ndarray, pd.Series],
    wet_bulb_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Calculate shade/indoor Wet Bulb Globe Temperature (ISO 7243).

    Uses the indoor formula 0.7*Tw + 0.3*Ta. For a closed-form estimate from
    temperature and humidity alone, use wbgt_simple(); for outdoor WBGT with an
    explicit globe temperature, use wbgt_outdoor().

    Reference: ISO 7243 standard for occupational heat stress.

    Args:
        temp_c: Air temperature in Celsius
        wet_bulb_c: Wet bulb temperature in Celsius

    Returns:
        WBGT in Celsius
    """
    return 0.7 * wet_bulb_c + 0.3 * temp_c


def wbgt_outdoor(
    temp_c: Union[float, np.ndarray, pd.Series],
    wet_bulb_c: Union[float, np.ndarray, pd.Series],
    globe_temp_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """
    Calculate outdoor Wet Bulb Globe Temperature with solar load.

    Reference: ISO 7243 standard for occupational heat stress.

    Args:
        temp_c: Air temperature in Celsius
        wet_bulb_c: Wet bulb temperature in Celsius
        globe_temp_c: Black globe temperature in Celsius

    Returns:
        WBGT in Celsius
    """
    return 0.7 * wet_bulb_c + 0.2 * globe_temp_c + 0.1 * temp_c


def humidex(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """Calculate Humidex (Canadian heat discomfort index).

    Args:
        temp_c: Air temperature in Celsius
        dewpoint_c: Dewpoint temperature in Celsius

    Reference: Masterson & Richardson (1979), Environment Canada.

    Returns:
        Humidex value (unitless, but interpreted like temperature)
    """
    # Masterson & Richardson (1979) vapor pressure (hPa). Uses the published
    # 273.16/273.15 mix verbatim; kept separate from vapor_pressure_from_dewpoint
    # so humidex matches its original definition exactly.
    e = 6.11 * np.exp(5417.7530 * (1.0 / 273.16 - 1.0 / (273.15 + dewpoint_c)))
    h = temp_c + 0.5555 * (e - 10)
    return h


# Stefan-Boltzmann constant (W m^-2 K^-4, CODATA 2018) and standard-person
# radiation constants from Thorsson et al. (2007).
_SIGMA_SB = 5.670374419e-8
_EMISSIVITY_PERSON = 0.97  # longwave emissivity of a standard person
_ABSORPTIVITY_PERSON = 0.7  # shortwave absorption coefficient of a standard person
_PROJECTED_AREA_FACTOR = 0.25  # rotationally-averaged projected area factor


def mean_radiant_temperature(
    temp_c: Union[float, np.ndarray, pd.Series],
    solar_rad_wm2: Union[float, np.ndarray, pd.Series],
    wind_ms: Optional[Union[float, np.ndarray, pd.Series]] = None,
) -> Union[float, np.ndarray, pd.Series]:
    """
    Estimate mean radiant temperature from global horizontal solar radiation.

    Closed-form radiation-balance estimator for a standard person from
    Thorsson et al. (2007), absorbing global horizontal shortwave onto the
    longwave radiant balance.

    Reference: Thorsson, S., et al. (2007). Different methods for estimating the
    mean radiant temperature in an outdoor urban setting. Int. J. Climatol.,
    27(14), 1983-1993.

    Args:
        temp_c: Air temperature in Celsius
        solar_rad_wm2: Global horizontal solar radiation in W/m²
        wind_ms: Unused; kept for backward-compatible signature. Wind enters the
            convective terms of UTCI/WBGT, not this radiant estimate.

    Returns:
        Estimated mean radiant temperature in Celsius
    """
    ta_k = temp_c + 273.15
    extra = (_ABSORPTIVITY_PERSON * _PROJECTED_AREA_FACTOR * solar_rad_wm2) / (
        _EMISSIVITY_PERSON * _SIGMA_SB
    )
    mrt = (ta_k**4 + extra) ** 0.25 - 273.15
    return mrt


# Coefficients of the UTCI reference saturation-vapor-pressure routine es()
# (Bröde 2012 operational code). Returns saturation vapor pressure over water.
_UTCI_ES_G = (
    -2836.5744,
    -6028.076559,
    19.54263612,
    -0.02737830188,
    0.000016261698,
    7.0229056e-10,
    -1.8680009e-13,
)


def _utci_saturation_kpa(
    temp_c: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """Saturation vapor pressure in kPa using the UTCI reference es() routine."""
    tk = np.asarray(temp_c, dtype=float) + 273.15
    es = 2.7150305 * np.log(tk)
    for i, g in enumerate(_UTCI_ES_G):
        es = es + g * tk ** (i - 2)
    # exp(es) is in Pa; the UTCI polynomial expects vapor pressure in kPa.
    return np.exp(es) * 0.001


def utci(
    temp_c: Union[float, np.ndarray, pd.Series],
    rh: Union[float, np.ndarray, pd.Series],
    wind_ms: Union[float, np.ndarray, pd.Series],
    mrt_c: Optional[Union[float, np.ndarray, pd.Series]] = None,
) -> Union[float, np.ndarray, pd.Series]:
    """Calculate Universal Thermal Climate Index (UTCI) using polynomial approximation.

    Reference: Bröde et al. (2012). Deriving the operational procedure for the
    Universal Thermal Climate Index (UTCI).

    Args:
        temp_c: Air temperature in Celsius (-50 to 50°C)
        rh: Relative humidity as percentage (0-100)
        wind_ms: Wind speed at 10m height in m/s (0.5 to 17 m/s)
        mrt_c: Mean radiant temperature in Celsius. If None, assumes mrt = temp_c

    Returns:
        UTCI in Celsius
    """
    if mrt_c is None:
        mrt_c = temp_c

    wind_ms = np.clip(wind_ms, 0.5, 17.0)
    rh = np.clip(rh, 0, 100)

    # Water-vapor pressure in kPa from the UTCI reference saturation routine.
    e_kpa = (rh / 100.0) * _utci_saturation_kpa(temp_c)

    # Bröde (2012) is defined for delta-MRT in [-30, 70] K.
    d_mrt = np.clip(mrt_c - temp_c, -30.0, 70.0)
    ta = temp_c
    va = wind_ms
    pa = e_kpa

    utci_val = (
        ta
        + 0.607562052
        + (-0.0227712343) * ta
        + (8.06470249e-4) * ta * ta
        + (-1.54271372e-4) * ta * ta * ta
        + (-3.24651735e-6) * ta * ta * ta * ta
        + (7.32602852e-8) * ta * ta * ta * ta * ta
        + (1.35959073e-9) * ta * ta * ta * ta * ta * ta
        + (-2.25836520) * va
        + (0.0880326035) * ta * va
        + (0.00216844454) * ta * ta * va
        + (-1.53347087e-5) * ta * ta * ta * va
        + (-5.72983704e-7) * ta * ta * ta * ta * va
        + (-2.55090145e-9) * ta * ta * ta * ta * ta * va
        + (-0.751269505) * va * va
        + (-0.00408350271) * ta * va * va
        + (-5.21670675e-5) * ta * ta * va * va
        + (1.94544667e-6) * ta * ta * ta * va * va
        + (1.14099531e-8) * ta * ta * ta * ta * va * va
        + (0.158137256) * va * va * va
        + (-6.57263143e-5) * ta * va * va * va
        + (2.22697524e-7) * ta * ta * va * va * va
        + (-4.16117031e-8) * ta * ta * ta * va * va * va
        + (-0.0127762753) * va * va * va * va
        + (9.66891875e-6) * ta * va * va * va * va
        + (2.52785852e-9) * ta * ta * va * va * va * va
        + (4.56306672e-4) * va * va * va * va * va
        + (-1.74202546e-7) * ta * va * va * va * va * va
        + (-5.91491269e-6) * va * va * va * va * va * va
        + (0.398374029) * d_mrt
        + (1.83945314e-4) * ta * d_mrt
        + (-1.73754510e-4) * ta * ta * d_mrt
        + (-7.60781159e-7) * ta * ta * ta * d_mrt
        + (3.77830287e-8) * ta * ta * ta * ta * d_mrt
        + (5.43079673e-10) * ta * ta * ta * ta * ta * d_mrt
        + (-0.0200518269) * va * d_mrt
        + (8.92859837e-4) * ta * va * d_mrt
        + (3.45433048e-6) * ta * ta * va * d_mrt
        + (-3.77925774e-7) * ta * ta * ta * va * d_mrt
        + (-1.69699377e-9) * ta * ta * ta * ta * va * d_mrt
        + (1.69992415e-4) * va * va * d_mrt
        + (-4.99204314e-5) * ta * va * va * d_mrt
        + (2.47417178e-7) * ta * ta * va * va * d_mrt
        + (1.07596466e-8) * ta * ta * ta * va * va * d_mrt
        + (8.49242932e-5) * va * va * va * d_mrt
        + (1.35191328e-6) * ta * va * va * va * d_mrt
        + (-6.21531254e-9) * ta * ta * va * va * va * d_mrt
        + (-4.99410301e-6) * va * va * va * va * d_mrt
        + (-1.89489258e-8) * ta * va * va * va * va * d_mrt
        + (8.15300114e-8) * va * va * va * va * va * d_mrt
        + (7.55043090e-4) * d_mrt * d_mrt
        + (-5.65095215e-5) * ta * d_mrt * d_mrt
        + (-4.52166564e-7) * ta * ta * d_mrt * d_mrt
        + (2.46688878e-8) * ta * ta * ta * d_mrt * d_mrt
        + (2.42674348e-10) * ta * ta * ta * ta * d_mrt * d_mrt
        + (1.54547250e-4) * va * d_mrt * d_mrt
        + (5.24110970e-6) * ta * va * d_mrt * d_mrt
        + (-8.75874982e-8) * ta * ta * va * d_mrt * d_mrt
        + (-1.50743064e-9) * ta * ta * ta * va * d_mrt * d_mrt
        + (-1.56236307e-5) * va * va * d_mrt * d_mrt
        + (-1.33895614e-7) * ta * va * va * d_mrt * d_mrt
        + (2.49709824e-9) * ta * ta * va * va * d_mrt * d_mrt
        + (6.51711721e-7) * va * va * va * d_mrt * d_mrt
        + (1.94960053e-9) * ta * va * va * va * d_mrt * d_mrt
        + (-1.00361113e-8) * va * va * va * va * d_mrt * d_mrt
        + (-1.21206673e-5) * d_mrt * d_mrt * d_mrt
        + (-2.18203660e-7) * ta * d_mrt * d_mrt * d_mrt
        + (7.51269482e-9) * ta * ta * d_mrt * d_mrt * d_mrt
        + (9.79063848e-11) * ta * ta * ta * d_mrt * d_mrt * d_mrt
        + (1.25006734e-6) * va * d_mrt * d_mrt * d_mrt
        + (-1.81584736e-9) * ta * va * d_mrt * d_mrt * d_mrt
        + (-3.52197671e-10) * ta * ta * va * d_mrt * d_mrt * d_mrt
        + (-3.36514630e-8) * va * va * d_mrt * d_mrt * d_mrt
        + (1.35908359e-10) * ta * va * va * d_mrt * d_mrt * d_mrt
        + (4.17032620e-10) * va * va * va * d_mrt * d_mrt * d_mrt
        + (-1.30369025e-9) * d_mrt * d_mrt * d_mrt * d_mrt
        + (4.13908461e-10) * ta * d_mrt * d_mrt * d_mrt * d_mrt
        + (9.22652254e-12) * ta * ta * d_mrt * d_mrt * d_mrt * d_mrt
        + (-5.08220384e-9) * va * d_mrt * d_mrt * d_mrt * d_mrt
        + (-2.24730961e-11) * ta * va * d_mrt * d_mrt * d_mrt * d_mrt
        + (1.17139133e-10) * va * va * d_mrt * d_mrt * d_mrt * d_mrt
        + (6.62154879e-10) * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt
        + (4.03863260e-13) * ta * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt
        + (1.95087203e-12) * va * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt
        + (-4.73602469e-12) * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt
        + (5.12733497) * pa
        + (-0.312788561) * ta * pa
        + (-0.0196701861) * ta * ta * pa
        + (9.99690870e-4) * ta * ta * ta * pa
        + (9.51738512e-6) * ta * ta * ta * ta * pa
        + (-4.66426341e-7) * ta * ta * ta * ta * ta * pa
        + (0.548050612) * va * pa
        + (-0.00330552823) * ta * va * pa
        + (-0.00164119440) * ta * ta * va * pa
        + (-5.16670694e-6) * ta * ta * ta * va * pa
        + (9.52692432e-7) * ta * ta * ta * ta * va * pa
        + (-0.0429223622) * va * va * pa
        + (0.00500845667) * ta * va * va * pa
        + (1.00601257e-6) * ta * ta * va * va * pa
        + (-1.81748644e-6) * ta * ta * ta * va * va * pa
        + (-1.25813502e-3) * va * va * va * pa
        + (-1.79330391e-4) * ta * va * va * va * pa
        + (2.34994441e-6) * ta * ta * va * va * va * pa
        + (1.29735808e-4) * va * va * va * va * pa
        + (1.29064870e-6) * ta * va * va * va * va * pa
        + (-2.28558686e-6) * va * va * va * va * va * pa
        + (-0.0369476348) * d_mrt * pa
        + (0.00162325322) * ta * d_mrt * pa
        + (-3.14279680e-5) * ta * ta * d_mrt * pa
        + (2.59835559e-6) * ta * ta * ta * d_mrt * pa
        + (-4.77136523e-8) * ta * ta * ta * ta * d_mrt * pa
        + (8.64203390e-3) * va * d_mrt * pa
        + (-6.87405181e-4) * ta * va * d_mrt * pa
        + (-9.13863872e-6) * ta * ta * va * d_mrt * pa
        + (5.15916806e-7) * ta * ta * ta * va * d_mrt * pa
        + (-3.59217476e-5) * va * va * d_mrt * pa
        + (3.28696511e-5) * ta * va * va * d_mrt * pa
        + (-7.10542454e-7) * ta * ta * va * va * d_mrt * pa
        + (-1.24382300e-5) * va * va * va * d_mrt * pa
        + (-7.38584400e-9) * ta * va * va * va * d_mrt * pa
        + (2.20609296e-7) * va * va * va * va * d_mrt * pa
        + (-7.32469180e-4) * d_mrt * d_mrt * pa
        + (-1.87381964e-5) * ta * d_mrt * d_mrt * pa
        + (4.80925239e-6) * ta * ta * d_mrt * d_mrt * pa
        + (-8.75492040e-8) * ta * ta * ta * d_mrt * d_mrt * pa
        + (2.77862930e-5) * va * d_mrt * d_mrt * pa
        + (-5.06004592e-6) * ta * va * d_mrt * d_mrt * pa
        + (1.14325367e-7) * ta * ta * va * d_mrt * d_mrt * pa
        + (2.53016723e-6) * va * va * d_mrt * d_mrt * pa
        + (-1.72857035e-8) * ta * va * va * d_mrt * d_mrt * pa
        + (-3.95079398e-8) * va * va * va * d_mrt * d_mrt * pa
        + (-3.59413173e-7) * d_mrt * d_mrt * d_mrt * pa
        + (7.04388046e-7) * ta * d_mrt * d_mrt * d_mrt * pa
        + (-1.89309167e-8) * ta * ta * d_mrt * d_mrt * d_mrt * pa
        + (-4.79768731e-7) * va * d_mrt * d_mrt * d_mrt * pa
        + (7.96079978e-9) * ta * va * d_mrt * d_mrt * d_mrt * pa
        + (1.62897058e-9) * va * va * d_mrt * d_mrt * d_mrt * pa
        + (3.94367674e-8) * d_mrt * d_mrt * d_mrt * d_mrt * pa
        + (-1.18566247e-9) * ta * d_mrt * d_mrt * d_mrt * d_mrt * pa
        + (3.34678041e-10) * va * d_mrt * d_mrt * d_mrt * d_mrt * pa
        + (-1.15606447e-10) * d_mrt * d_mrt * d_mrt * d_mrt * d_mrt * pa
        + (-2.80626406) * pa * pa
        + (0.548712484) * ta * pa * pa
        + (-0.00399428410) * ta * ta * pa * pa
        + (-9.54009191e-4) * ta * ta * ta * pa * pa
        + (1.93090978e-5) * ta * ta * ta * ta * pa * pa
        + (-0.308806365) * va * pa * pa
        + (0.0116952364) * ta * va * pa * pa
        + (4.95271903e-4) * ta * ta * va * pa * pa
        + (-1.90710882e-5) * ta * ta * ta * va * pa * pa
        + (0.00210787756) * va * va * pa * pa
        + (-6.98445738e-4) * ta * va * va * pa * pa
        + (2.30109073e-5) * ta * ta * va * va * pa * pa
        + (4.17856590e-4) * va * va * va * pa * pa
        + (-1.27043871e-5) * ta * va * va * va * pa * pa
        + (-3.04620472e-6) * va * va * va * va * pa * pa
        + (0.0514507424) * d_mrt * pa * pa
        + (-0.00432510997) * ta * d_mrt * pa * pa
        + (8.99281156e-5) * ta * ta * d_mrt * pa * pa
        + (-7.14663943e-7) * ta * ta * ta * d_mrt * pa * pa
        + (-2.66016305e-4) * va * d_mrt * pa * pa
        + (2.63789586e-4) * ta * va * d_mrt * pa * pa
        + (-7.01199003e-6) * ta * ta * va * d_mrt * pa * pa
        + (-1.06823306e-4) * va * va * d_mrt * pa * pa
        + (3.61341136e-6) * ta * va * va * d_mrt * pa * pa
        + (2.29748967e-7) * va * va * va * d_mrt * pa * pa
        + (3.04788893e-4) * d_mrt * d_mrt * pa * pa
        + (-6.42070836e-5) * ta * d_mrt * d_mrt * pa * pa
        + (1.16257971e-6) * ta * ta * d_mrt * d_mrt * pa * pa
        + (7.68023384e-6) * va * d_mrt * d_mrt * pa * pa
        + (-5.47446896e-7) * ta * va * d_mrt * d_mrt * pa * pa
        + (-3.59937910e-8) * va * va * d_mrt * d_mrt * pa * pa
        + (-4.36497725e-6) * d_mrt * d_mrt * d_mrt * pa * pa
        + (1.68737969e-7) * ta * d_mrt * d_mrt * d_mrt * pa * pa
        + (2.67489271e-8) * va * d_mrt * d_mrt * d_mrt * pa * pa
        + (3.23926897e-9) * d_mrt * d_mrt * d_mrt * d_mrt * pa * pa
        + (-0.0353874123) * pa * pa * pa
        + (-0.221201190) * ta * pa * pa * pa
        + (0.0155126038) * ta * ta * pa * pa * pa
        + (-2.63917279e-4) * ta * ta * ta * pa * pa * pa
        + (0.0453433455) * va * pa * pa * pa
        + (-0.00432943862) * ta * va * pa * pa * pa
        + (1.45389826e-4) * ta * ta * va * pa * pa * pa
        + (2.17508610e-4) * va * va * pa * pa * pa
        + (-6.66724702e-5) * ta * va * va * pa * pa * pa
        + (3.33217140e-5) * va * va * va * pa * pa * pa
        + (-0.00226921615) * d_mrt * pa * pa * pa
        + (3.80261982e-4) * ta * d_mrt * pa * pa * pa
        + (-5.45314314e-9) * ta * ta * d_mrt * pa * pa * pa
        + (-7.96355448e-4) * va * d_mrt * pa * pa * pa
        + (2.53458034e-5) * ta * va * d_mrt * pa * pa * pa
        + (-6.31223658e-6) * va * va * d_mrt * pa * pa * pa
        + (3.02122035e-4) * d_mrt * d_mrt * pa * pa * pa
        + (-4.77403547e-6) * ta * d_mrt * d_mrt * pa * pa * pa
        + (1.73825715e-6) * va * d_mrt * d_mrt * pa * pa * pa
        + (-4.09087898e-7) * d_mrt * d_mrt * d_mrt * pa * pa * pa
        + (0.614155345) * pa * pa * pa * pa
        + (-0.0616755931) * ta * pa * pa * pa * pa
        + (0.00133374846) * ta * ta * pa * pa * pa * pa
        + (0.00355375387) * va * pa * pa * pa * pa
        + (-5.13027851e-4) * ta * va * pa * pa * pa * pa
        + (1.02449757e-4) * va * va * pa * pa * pa * pa
        + (-0.00148526421) * d_mrt * pa * pa * pa * pa
        + (-4.11469183e-5) * ta * d_mrt * pa * pa * pa * pa
        + (-6.80434415e-6) * va * d_mrt * pa * pa * pa * pa
        + (-9.77675906e-6) * d_mrt * d_mrt * pa * pa * pa * pa
        + (0.0882773108) * pa * pa * pa * pa * pa
        + (-0.00301859306) * ta * pa * pa * pa * pa * pa
        + (0.00104452989) * va * pa * pa * pa * pa * pa
        + (2.47090539e-4) * d_mrt * pa * pa * pa * pa * pa
        + (0.00148348065) * pa * pa * pa * pa * pa * pa
    )

    return utci_val


def utci_sparse(
    temp_c: Union[float, np.ndarray, pd.Series],
    tmrt: Union[float, np.ndarray, pd.Series],
    wind_speed: Union[float, np.ndarray, pd.Series],
    rh: Union[float, np.ndarray, pd.Series],
) -> Union[float, np.ndarray, pd.Series]:
    """UTCI via sparse Legendre polynomial (Roman et al. 2025, doi:10.5281/zenodo.17465548).

    Wider wind range than Bröde polynomial (0.5-30.3 m/s vs 0.5-17 m/s).
    """
    Ta = np.asarray(temp_c, dtype=float)
    Tr = np.asarray(tmrt, dtype=float)
    va = np.clip(np.asarray(wind_speed, dtype=float), 0.5, 30.3)
    rh = np.clip(np.asarray(rh, dtype=float), 5, 100)

    dTrTa = Tr - Ta

    nTa = Ta / 50.0
    ndTrTa = (dTrTa - 20.0) / 50.0
    nva = (va - 15.4) / 14.9
    nrH = (rh - 52.5) / 47.5

    from numpy.polynomial.legendre import legval

    def _lbasis(x, n):
        return [legval(x, [0] * i + [1]) for i in range(1, n + 1)]

    Ta1, Ta2, Ta3, Ta4, Ta5, Ta6, Ta7, Ta8, Ta9, Ta10 = _lbasis(nTa, 10)
    dTrTa1, dTrTa2, dTrTa3 = _lbasis(ndTrTa, 3)
    va1, va2, va3, va4, va5, va6, va7, va8, va9, va10 = _lbasis(nva, 10)
    rH1, rH2, rH3, rH4, rH5, rH6, rH7, rH8, rH9 = _lbasis(nrH, 9)

    offset = (
        -0.0137842169737312
        + 0.605451658287147 * Ta1
        + 0.228978616673604 * dTrTa1
        + -0.411887517706717 * va1
        + 0.0516822161148559 * rH1
        + 0.280580929387293 * Ta2
        + 0.0494441100625763 * Ta1 * dTrTa1
        + 0.407606222800615 * Ta1 * va1
        + 0.0989531628394581 * Ta1 * rH1
        + 0.0246471408147623 * dTrTa2
        + -0.0571289630222624 * dTrTa1 * va1
        + -0.00981948141197167 * dTrTa1 * rH1
        + 0.115659720373134 * va2
        + -0.00534228470468843 * va1 * rH1
        + 0.016606193686503 * rH2
        + -0.151030966047951 * Ta2 * dTrTa1
        + 0.188807982337807 * Ta2 * va1
        + 0.0881449234650015 * Ta2 * rH1
        + -0.00930063989106069 * Ta1 * dTrTa2
        + 0.0215873308746893 * Ta1 * dTrTa1 * va1
        + -0.0227872935667395 * Ta1 * dTrTa1 * rH1
        + -0.11306527433562 * Ta1 * va2
        + -0.0109236071122277 * Ta1 * va1 * rH1
        + 0.0255963885144559 * Ta1 * rH2
        + -0.000676664345791177 * dTrTa3
        + 0.0244340319236622 * dTrTa1 * va2
        + 0.0020488990800455 * dTrTa1 * va1 * rH1
        + -0.00198787369921777 * dTrTa1 * rH2
        + -0.0262531747919802 * va3
        + 0.00241202999394371 * va2 * rH1
        + -0.0899003481633464 * Ta4
        + -0.0518348124459142 * Ta3 * dTrTa1
        + -0.019305242850497 * Ta3 * va1
        + 0.0288567768313003 * Ta3 * rH1
        + -0.00532373584837672 * Ta2 * dTrTa2
        + 0.00865046786070809 * Ta2 * dTrTa1 * va1
        + -0.0200025901337491 * Ta2 * dTrTa1 * rH1
        + -0.0560921250768577 * Ta2 * va2
        + -0.0120111532564824 * Ta2 * va1 * rH1
        + 0.0193526595005879 * Ta2 * rH2
        + -0.00147617610703898 * Ta1 * dTrTa3
        + 0.0147709386142124 * Ta1 * dTrTa2 * va1
        + 0.000223025361668181 * Ta1 * dTrTa2 * rH1
        + -0.0267126314476705 * Ta1 * dTrTa1 * va2
        + 0.00293284619228001 * Ta1 * dTrTa1 * va1 * rH1
        + -0.00274343594032762 * Ta1 * dTrTa1 * rH2
        + 0.0255375758890182 * Ta1 * va3
        + 0.00617742875276631 * Ta1 * va2 * rH1
        + 0.00131758038812698 * dTrTa3 * va1
        + -1.19588186117375e-05 * dTrTa2 * va2
        + -0.0195473208292468 * dTrTa1 * va3
        + 0.0308499978887788 * va4
        + -0.00168292560551294 * va3 * rH1
        + -0.000721243580359172 * rH4
        + 0.0241135789170187 * Ta5
        + 0.0667693514821362 * Ta4 * dTrTa1
        + -0.105442958374474 * Ta4 * va1
        + 0.0169733342570069 * Ta3 * dTrTa2
        + -0.0588730143622148 * Ta3 * dTrTa1 * va1
        + -0.00478455509424903 * Ta3 * dTrTa1 * rH1
        + 0.0322224934071458 * Ta3 * va2
        + -0.0109309219781879 * Ta3 * va1 * rH1
        + 0.00298613871955914 * Ta2 * dTrTa3
        + -0.00970592755419437 * Ta2 * dTrTa2 * va1
        + 0.0143009046314569 * Ta2 * va3
        + 0.0073472142860989 * Ta2 * va2 * rH1
        + -0.0118859833533268 * Ta2 * rH3
        + -0.00811197236365886 * Ta1 * dTrTa2 * va2
        + 0.0202049930797466 * Ta1 * dTrTa1 * va3
        + -0.00948544475972315 * Ta1 * va4
        + -0.00407327808659386 * Ta1 * va3 * rH1
        + 0.0013485215681372 * dTrTa2 * va3
        + 0.00386595947690624 * dTrTa1 * va4
        + 2.17696778130301e-05 * dTrTa1 * va3 * rH1
        + -0.00261892113164038 * dTrTa1 * rH4
        + -0.00489648267639115 * va5
        + 0.000681848728845763 * va4 * rH1
        + 0.0082368236806339 * Ta6
        + 0.0421952883373002 * Ta5 * dTrTa1
        + -0.0188866947129327 * Ta5 * va1
        + -0.0230895202091769 * Ta5 * rH1
        + 0.00050946740381826 * Ta4 * dTrTa2
        + 0.0387368190996963 * Ta4 * va2
        + -0.00365652796668801 * Ta4 * va1 * rH1
        + -0.0165226812597451 * Ta4 * rH2
        + -0.02106808547032 * Ta3 * dTrTa2 * va1
        + 0.0455127356554093 * Ta3 * dTrTa1 * va2
        + -0.0327523492050705 * Ta3 * va3
        + 0.00411199080502651 * Ta3 * va2 * rH1
        + -0.00529398688982106 * Ta3 * rH3
        + -0.00299659797672848 * Ta2 * dTrTa3 * va1
        + 0.0127070225168592 * Ta2 * dTrTa2 * va2
        + -0.0039536575347961 * Ta2 * va3 * rH1
        + 0.00176928876312725 * Ta1 * dTrTa2 * va3
        + 0.0249223383434746 * Ta1 * va5
        + 0.0010279948173077 * Ta1 * va4 * rH1
        + -0.000456624197665442 * dTrTa2 * va4
        + 0.000227993624070799 * dTrTa2 * rH4
        + -0.000497222888028054 * dTrTa1 * va1 * rH4
        + 0.00189906855480326 * va2 * rH4
        + -0.00516323105647903 * rH6
        + -0.0388335821720079 * Ta7
        + -0.0142074242411286 * Ta6 * dTrTa1
        + 0.0488685513521004 * Ta6 * va1
        + -0.0269122930593438 * Ta6 * rH1
        + -0.00845228865914141 * Ta5 * dTrTa2
        + 0.0386364103297441 * Ta5 * dTrTa1 * va1
        + 0.00333840546426587 * Ta5 * dTrTa1 * rH1
        + -0.0274986339482448 * Ta5 * va2
        + -0.0233728308709061 * Ta5 * rH2
        + -0.0010233136301785 * Ta4 * dTrTa3
        + 0.0109665440679091 * Ta4 * dTrTa2 * va1
        + -0.0141154511737893 * Ta4 * dTrTa1 * va2
        + 0.00797571345288548 * Ta4 * dTrTa1 * rH2
        + -0.00626818826879268 * Ta4 * rH3
        + 0.000541492731933859 * Ta3 * dTrTa2 * va2
        + -0.0194848041587283 * Ta3 * dTrTa1 * va3
        + -0.00242146589114414 * Ta3 * dTrTa1 * va1 * rH2
        + 0.00862214501674155 * Ta3 * va4
        + -0.000813086246676268 * Ta3 * va3 * rH1
        + -0.0109313281200866 * Ta2 * dTrTa2 * va3
        + 0.0107908356351421 * Ta2 * dTrTa1 * va4
        + -0.00154886246960825 * Ta2 * dTrTa1 * rH4
        + 0.000285510363654986 * Ta2 * va3 * rH2
        + 0.00600871455392313 * Ta1 * dTrTa1 * va5
        + 0.0133563698637056 * Ta1 * va6
        + 0.00200056613397992 * dTrTa2 * va5
        + -0.000487892088628483 * dTrTa2 * va1 * rH4
        + 0.00239926457161527 * dTrTa1 * va2 * rH4
        + -0.00147299336560724 * va3 * rH4
        + -0.0034747543766636 * rH7
        + -0.042138668585659 * Ta7 * dTrTa1
        + 0.0226809825649836 * Ta7 * va1
        + -0.0317422118129167 * Ta7 * rH1
        + -0.0165868569214051 * Ta6 * dTrTa2
        + 0.00866283641928592 * Ta6 * dTrTa1 * va1
        + -0.0158286817515286 * Ta6 * va2
        + -0.0123918623262792 * Ta6 * rH2
        + 0.00865497207378352 * Ta5 * dTrTa2 * va1
        + -0.0313622056127219 * Ta5 * dTrTa1 * va2
        + 0.0059883355097739 * Ta5 * dTrTa1 * rH2
        + 0.0282517594922186 * Ta5 * va3
        + -0.00055801074931404 * Ta5 * rH3
        + 0.00216134547091048 * Ta4 * dTrTa3 * va1
        + -0.00390324341081546 * Ta4 * dTrTa2 * va2
        + 0.0163223310714439 * Ta4 * dTrTa1 * va3
        + -0.00150025871011703 * Ta4 * dTrTa1 * va1 * rH2
        + 0.00276956624980006 * Ta4 * dTrTa1 * rH3
        + -0.0229190983632922 * Ta4 * va4
        + 0.00314130091223181 * Ta3 * dTrTa1 * va2 * rH2
        + -0.0112810754291653 * Ta3 * va5
        + 0.00416439851600464 * Ta3 * rH5
        + -0.000700256201721478 * Ta2 * dTrTa3 * va3
        + -0.000514959299985243 * Ta2 * dTrTa1 * va3 * rH2
        + 0.00233921794871584 * Ta2 * dTrTa1 * va1 * rH4
        + 0.00619041956132346 * Ta2 * va6
        + -0.00342955079343321 * Ta1 * dTrTa1 * va2 * rH4
        + 0.000527414639632667 * dTrTa1 * va7
        + -0.000183752476546752 * dTrTa1 * va1 * rH6
        + -0.0118888391328967 * va8
        + 0.000238712903990469 * va4 * rH4
        + -0.00274527466548323 * rH8
        + -0.00346736606571359 * Ta9
        + -0.015821140907443 * Ta8 * dTrTa1
        + -0.0159703972679985 * Ta8 * va1
        + -0.00220146749570155 * Ta8 * rH1
        + -0.0196462686116071 * Ta7 * dTrTa1 * va1
        + 0.0160930622139814 * Ta7 * va2
        + 0.0271083926542394 * Ta6 * dTrTa1 * va2
        + -0.0169727859361079 * Ta6 * va3
        + -0.00262019654796821 * Ta5 * va2 * rH2
        + 0.0117666226277279 * Ta5 * rH4
        + 0.00865116634722382 * Ta4 * dTrTa2 * va3
        + -0.0318664489619453 * Ta4 * dTrTa1 * va4
        + 0.00136762123420908 * Ta4 * va3 * rH2
        + -0.00648813541319593 * Ta2 * dTrTa2 * va5
        + 0.00283418925119063 * Ta2 * dTrTa1 * va6
        + 0.000627683891249201 * dTrTa2 * rH7
        + 0.000464486061684286 * va7 * rH2
        + -0.012558774419946 * Ta10
        + 0.0142246701070405 * Ta9 * dTrTa1
        + -0.0219945853668843 * Ta9 * va1
        + 0.00147989498898127 * Ta9 * rH1
        + 0.020694589513114 * Ta8 * dTrTa2
        + -0.0159821465878725 * Ta8 * dTrTa1 * va1
        + 0.00122990587236154 * Ta8 * va2
        + 0.00774643224013198 * Ta8 * rH2
        + 0.00348972484418949 * Ta7 * dTrTa3
        + -0.00449889353160404 * Ta7 * dTrTa2 * va1
        + 0.00150065745949661 * Ta7 * dTrTa2 * rH1
        + -0.000617652342920564 * Ta7 * va3
        + 0.0150749840950315 * Ta7 * rH3
        + -0.00456928274166078 * Ta6 * dTrTa1 * va3
        + 0.0132771238868905 * Ta6 * va4
        + -0.00313385473186283 * Ta6 * va2 * rH2
        + 0.0187605036147175 * Ta5 * dTrTa1 * va4
        + 0.000600921760262751 * Ta5 * va3 * rH2
        + -0.00662490990387182 * Ta4 * va6
        + 0.00527904629696365 * Ta4 * va2 * rH4
        + -0.000464141239154267 * Ta3 * dTrTa1 * va6
        + -0.00506780416680173 * Ta3 * va3 * rH4
        + 0.0040868742073381 * Ta2 * va8
        + 0.000288339820559906 * Ta1 * dTrTa2 * rH7
        + -0.0158274027071249 * Ta1 * va9
        + 0.00170167068625823 * dTrTa2 * rH8
        + 0.00283124879915756 * dTrTa1 * va9
        + -0.000290365909059354 * dTrTa1 * va1 * rH8
        + -0.0131987351201934 * va10
        + 0.000543804208687463 * va1 * rH9
    )

    result = Ta + offset * 45.135 - 17.085

    if np.isscalar(temp_c) and np.ndim(result) == 0:
        return float(result)
    return result


# Ordered (upper_bound, label) thresholds for each risk scale. A value is
# assigned the label of the first band whose upper bound it falls below; the
# final band has an upper bound of None (open-ended, matches anything larger).
# NWS heat-index categories, converted from the canonical 80/90/103/124 °F
# cutoffs to °C (C = (F - 32) * 5/9).
_HEAT_INDEX_BANDS = [
    (26.6667, "Normal"),
    (32.2222, "Caution"),
    (39.4444, "Extreme Caution"),
    (51.1111, "Danger"),
    (None, "Extreme Danger"),
]
# NWS/OSHA WBGT flag-condition breaks, converted from 78/82/85/88 °F to °C.
_WBGT_BANDS = [
    (25.5556, "Low"),
    (27.7778, "Moderate"),
    (29.4444, "High"),
    (31.1111, "Very High"),
    (None, "Extreme"),
]
_UTCI_BANDS = [
    (-40, "Extreme Cold Stress"),
    (-27, "Very Strong Cold Stress"),
    (-13, "Strong Cold Stress"),
    (0, "Moderate Cold Stress"),
    (9, "Slight Cold Stress"),
    (26, "No Thermal Stress"),
    (32, "Moderate Heat Stress"),
    (38, "Strong Heat Stress"),
    (46, "Very Strong Heat Stress"),
    (None, "Extreme Heat Stress"),
]


def _categorize_by_bands(
    value: Union[float, np.ndarray, pd.Series],
    bands: List[tuple],
) -> Union[str, np.ndarray, pd.Series]:
    """Map a value (scalar or array) to its band label using ordered bands."""
    if isinstance(value, (pd.Series, np.ndarray)):
        conditions = [value < upper for upper, _ in bands[:-1]]
        conditions.append(np.ones_like(value, dtype=bool))
        choices = [label for _, label in bands]
        return np.select(conditions, choices, default="Unknown")

    for upper, label in bands:
        if upper is None or value < upper:
            return label
    return "Unknown"


def heat_index_risk_category(
    hi: Union[float, np.ndarray, pd.Series],
) -> Union[str, np.ndarray, pd.Series]:
    """
    Categorize heat index into NWS risk categories.

    Categories:
    - Normal: < 27°C
    - Caution: 27-32°C
    - Extreme Caution: 32-39°C
    - Danger: 39-51°C
    - Extreme Danger: >= 51°C

    Args:
        hi: Heat index in Celsius

    Returns:
        Risk category string(s)
    """
    return _categorize_by_bands(hi, _HEAT_INDEX_BANDS)


def wbgt_risk_category(
    wbgt: Union[float, np.ndarray, pd.Series],
) -> Union[str, np.ndarray, pd.Series]:
    """
    Categorize WBGT into ISO 7243 risk categories for occupational heat stress.

    Categories:
    - Low: < 25°C
    - Moderate: 25-28°C
    - High: 28-30°C
    - Very High: 30-32°C
    - Extreme: >= 32°C

    Args:
        wbgt: WBGT in Celsius

    Returns:
        Risk category string(s)
    """
    return _categorize_by_bands(wbgt, _WBGT_BANDS)


def utci_category(
    utci_val: Union[float, np.ndarray, pd.Series],
) -> Union[str, np.ndarray, pd.Series]:
    """
    Categorize UTCI into thermal stress categories.

    Categories (10-level scale):
    - Extreme Cold Stress: < -40°C
    - Very Strong Cold Stress: -40 to -27°C
    - Strong Cold Stress: -27 to -13°C
    - Moderate Cold Stress: -13 to 0°C
    - Slight Cold Stress: 0 to 9°C
    - No Thermal Stress: 9 to 26°C
    - Moderate Heat Stress: 26 to 32°C
    - Strong Heat Stress: 32 to 38°C
    - Very Strong Heat Stress: 38 to 46°C
    - Extreme Heat Stress: >= 46°C

    Args:
        utci_val: UTCI in Celsius

    Returns:
        Thermal stress category string(s)
    """
    return _categorize_by_bands(utci_val, _UTCI_BANDS)


def calc_heat_indices(
    temp_c: Union[float, np.ndarray, pd.Series],
    dewpoint_c: Union[float, np.ndarray, pd.Series],
    wind_ms: Optional[Union[float, np.ndarray, pd.Series]] = None,
    solar_rad_wm2: Optional[Union[float, np.ndarray, pd.Series]] = None,
) -> Dict[str, Union[float, np.ndarray, pd.Series]]:
    """
    Calculate all heat stress indices at once.

    Args:
        temp_c: Air temperature in Celsius
        dewpoint_c: Dewpoint temperature in Celsius
        wind_ms: Wind speed in m/s (optional, needed for UTCI)
        solar_rad_wm2: Solar radiation in W/m² (optional, for outdoor MRT)

    Returns:
        Dictionary with all calculated indices:
        - rh: Relative humidity (%)
        - wet_bulb: Wet bulb temperature (°C)
        - heat_index: Heat index (°C)
        - wbgt: Wet Bulb Globe Temperature (°C)
        - humidex: Humidex value
        - utci: Universal Thermal Climate Index (°C) - if wind provided
        - heat_index_risk: Risk category for heat index
        - wbgt_risk: Risk category for WBGT
        - utci_stress: Stress category for UTCI - if wind provided
    """
    rh = relative_humidity_from_dewpoint(temp_c, dewpoint_c)
    wet_bulb = wet_bulb_temperature(temp_c, rh)
    hi = heat_index(temp_c, rh)
    wbgt = wbgt_simple(temp_c, dewpoint_c)
    hx = humidex(temp_c, dewpoint_c)

    result: Dict[str, Union[float, np.ndarray, pd.Series]] = {
        "rh": rh,
        "wet_bulb": wet_bulb,
        "heat_index": hi,
        "wbgt": wbgt,
        "humidex": hx,
        "heat_index_risk": heat_index_risk_category(hi),
        "wbgt_risk": wbgt_risk_category(wbgt),
    }

    if wind_ms is not None:
        mrt = None
        if solar_rad_wm2 is not None:
            mrt = mean_radiant_temperature(temp_c, solar_rad_wm2, wind_ms)
        utci_val = utci(temp_c, rh, wind_ms, mrt)
        result["utci"] = utci_val
        result["utci_stress"] = utci_category(utci_val)

    return result
