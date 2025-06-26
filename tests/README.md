# Test Scripts

This directory contains all test scripts for validating LME Daily Report functionality.

## 🔍 Key Test Categories

### Integration Tests
- `test_three_exchanges_integration.py` - LME/SHFE/CME integration verification
- `test_fund_positions_complete.py` - All 6 metals fund position testing
- `test_integrated_shanghai_premiums.py` - Shanghai premium data integration

### Core Function Tests
- `test_dynamic_ric.py` - Dynamic LME RIC generation testing
- `test_mcu_pattern.py` - MCU+month+year pattern validation
- `test_exchange_curves_integration.py` - Multi-exchange curve comparison

### Data Validation Tests
- `test_shanghai_copper_futures.py` - SHFE SCFc series validation
- `test_cme_copper_futures.py` - CME HGc series validation
- `test_warrant_integration.py` - LME warrant data verification

### Alternative RIC Tests
- `test_alternative_fund_rics.py` - Backup RIC pattern testing
- `test_lme_monthly_rics_correct.py` - Monthly contract RIC validation

## 🚀 Running Tests

```bash
# Individual test execution
python test_fund_positions_complete.py

# Integration testing
python test_three_exchanges_integration.py

# Dynamic functionality
python test_dynamic_ric.py
```

## 📊 Test Coverage

- **Fund Positions**: 6 metals × 2 positions = 12 data points
- **Exchange Integration**: 3 exchanges × 6-12 contracts each
- **RIC Validation**: 100+ RIC patterns tested
- **Error Handling**: Comprehensive fallback scenarios

All tests include comprehensive logging and error reporting for debugging purposes.