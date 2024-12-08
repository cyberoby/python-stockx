from enum import Enum


class Currency(Enum):
    """Supported currency codes.

    `AUD`
    `CAD`
    `CHF`
    `EUR`
    `GBP`
    `HKD`
    `JPY`
    `KRW`
    `MXN`
    `NZD`
    `SGD`
    `USD`

    Parameters
    ----------
    value : `str`
        The three-letter currency code
    """
    AUD = 'AUD'
    CAD = 'CAD' 
    CHF = 'CHF'
    EUR = 'EUR'
    GBP = 'GBP'
    HKD = 'HKD'
    JPY = 'JPY'
    KRW = 'KRW'
    MXN = 'MXN'
    NZD = 'NZD'
    SGD = 'SGD'
    USD = 'USD'


