"""
Technical Indicators Configuration
Define periods and parameters for various technical indicators
"""

# RSI (Relative Strength Index) Configuration
RSI_CONFIG = {
    'enabled': True,
    'default_period': 14,
    'periods': [14, 21, 50],  # Multiple RSI periods
    'overbought_threshold': 70,
    'oversold_threshold': 30
}

# EMA (Exponential Moving Average) Configuration
EMA_CONFIG = {
    'enabled': True,
    'periods': [11, 21, 50, 200]  # Custom EMA periods
}

# SMA (Simple Moving Average) Configuration
SMA_CONFIG = {
    'enabled': True,
    'periods': [11, 21, 50, 200]  # Common SMA periods
}

# ATR (Average True Range) Configuration
ATR_CONFIG = {
    'enabled': True,
    'default_period': 14,
    'periods': [14, 21]  # ATR periods
}

# MACD (Moving Average Convergence Divergence) Configuration
MACD_CONFIG = {
    'enabled': True,
    'fast_period': 12,
    'slow_period': 26,
    'signal_period': 9
}

# Bollinger Bands Configuration
BOLLINGER_BANDS_CONFIG = {
    'enabled': True,
    'period': 20,
    'std_dev': 2
}

# Stochastic Oscillator Configuration
STOCHASTIC_CONFIG = {
    'enabled': True,
    'k_period': 14,
    'd_period': 3,
    'smooth_k': 3
}

# Williams %R Configuration
WILLIAMS_R_CONFIG = {
    'enabled': True,
    'period': 14
}

# Commodity Channel Index (CCI) Configuration
CCI_CONFIG = {
    'enabled': True,
    'period': 20
}

# Money Flow Index (MFI) Configuration
MFI_CONFIG = {
    'enabled': True,
    'period': 14
}

# All indicator configurations
INDICATOR_CONFIGS = {
    'RSI': RSI_CONFIG,
    'EMA': EMA_CONFIG,
    'SMA': SMA_CONFIG,
    'ATR': ATR_CONFIG,
    'MACD': MACD_CONFIG,
    'BOLLINGER_BANDS': BOLLINGER_BANDS_CONFIG,
    'STOCHASTIC': STOCHASTIC_CONFIG,
    'WILLIAMS_R': WILLIAMS_R_CONFIG,
    'CCI': CCI_CONFIG,
    'MFI': MFI_CONFIG
}

def get_enabled_indicators():
    """Get list of enabled indicators"""
    return [name for name, config in INDICATOR_CONFIGS.items() if config.get('enabled', False)]

def get_indicator_periods(indicator_name):
    """Get periods for a specific indicator"""
    config = INDICATOR_CONFIGS.get(indicator_name, {})
    if 'periods' in config:
        return config['periods']
    elif 'default_period' in config:
        return [config['default_period']]
    else:
        return []

def get_indicator_config(indicator_name):
    """Get full configuration for a specific indicator"""
    return INDICATOR_CONFIGS.get(indicator_name, {})

def validate_config():
    """Validate all indicator configurations"""
    errors = []
    
    for name, config in INDICATOR_CONFIGS.items():
        if not isinstance(config, dict):
            errors.append(f"{name}: Configuration must be a dictionary")
            continue
            
        if config.get('enabled', False):
            # Validate periods
            if 'periods' in config:
                if not isinstance(config['periods'], list) or not all(isinstance(p, int) and p > 0 for p in config['periods']):
                    errors.append(f"{name}: 'periods' must be a list of positive integers")
            
            if 'default_period' in config:
                if not isinstance(config['default_period'], int) or config['default_period'] <= 0:
                    errors.append(f"{name}: 'default_period' must be a positive integer")
    
    return errors

# Example usage and testing
if __name__ == "__main__":
    print("Technical Indicators Configuration")
    print("=" * 40)
    
    enabled = get_enabled_indicators()
    print(f"Enabled indicators: {', '.join(enabled)}")
    
    print(f"\nRSI periods: {get_indicator_periods('RSI')}")
    print(f"EMA periods: {get_indicator_periods('EMA')}")
    print(f"ATR periods: {get_indicator_periods('ATR')}")
    
    errors = validate_config()
    if errors:
        print(f"\nConfiguration errors: {errors}")
    else:
        print("\n✅ All configurations are valid!")
