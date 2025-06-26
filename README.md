# LME Daily Report Generator

**Professional LME (London Metal Exchange) Daily Market Report Generation System**

## 🎯 Overview

This system generates comprehensive daily market reports for LME metals (Copper, Aluminium, Zinc, Lead, Nickel, Tin) targeting professional traders and institutional investors. It collects data from multiple sources including LME, Shanghai Futures Exchange (SHFE), CME, and generates detailed analysis reports optimized for Claude AI analysis.

## ⚡ Quick Start

### Simple Execution
```bash
# Linux/macOS (automatic environment setup)
./run_report.sh

# Windows (automatic environment setup)
run_report.bat

# Manual execution
python lme_daily_report.py
```

### Output
- **Report File**: `output/LME_Daily_Report_Input_YYYYMMDD.txt`
- **Log File**: `logs/lme_report_YYYYMMDD.log`

## 🔧 Core Features

### Market Data Coverage
- **6 LME Metals**: Price data, inventory, trading volume, forward curves
- **Fund Positions**: Long/short positions for institutional investors
- **Multi-Exchange Comparison**: LME vs Shanghai vs CME copper curves
- **Shanghai Premiums**: 3 key indicators (Yangshan Port, CIF, Bonded Warehouse)
- **Macro Environment**: USD index, yields, VIX, equity markets
- **News Integration**: 3-day comprehensive news collection with priority filtering

### Advanced Analytics
- **Dynamic RIC Generation**: Auto-updating LME contract RICs based on execution date
- **Warrant Analysis**: Detailed LME warrant breakdown (on-warrant, cancelled, ratios)
- **Cross-Exchange Arbitrage**: Automatic detection of price discrepancies
- **Trend Analysis**: 5-day, 20-day moving patterns with statistical significance

## 📊 System Architecture

```
LME Daily Report Generator
├── lme_daily_report.py          # Main system
├── config.json                  # Configuration (RICs, settings)
├── requirements.txt             # Dependencies
├── run_report.sh/bat           # Auto-execution scripts
├── output/                     # Generated reports
├── logs/                       # Execution logs
├── tests/                      # Test scripts
├── development_scripts/        # Development utilities
├── docs/                       # Documentation
├── CopperSpreadAnalyzer/       # Integrated spread analysis
├── CopperSpreadAnalyzer_Standalone/  # Standalone spread system
└── RefinitivDataExplorer/      # Data exploration tools
```

## 🛠 Installation

### Requirements
- Python 3.8+
- Refinitiv Eikon Desktop (running)
- Valid Eikon API Key

### Dependencies
```bash
pip install -r requirements.txt
```

**Core packages**: `eikon`, `pandas`, `numpy`  
**Optional**: `python-dotenv`, `openpyxl`, `colorlog`

## ⚙️ Configuration

### API Setup
1. Update `config.json` with your Eikon API key:
```json
{
  "eikon_api_key": "your_actual_api_key_here"
}
```

2. Ensure Eikon Desktop is running and connected

### Customization
- **News Settings**: Enable/disable news collection
- **Market Holidays**: Add custom holiday dates
- **RIC Alternatives**: Configure fallback RICs for reliability

## 📈 Report Structure

### For Claude Analysis (2000-3000 words)
1. **Copper Market Detailed Analysis** (Primary focus)
   - Multi-exchange price comparison and arbitrage opportunities
   - Term structure analysis (1-6 months)
   - Inventory dynamics and warrant analysis
   - Fund positioning and sentiment analysis

2. **Trading Strategy Sections**
   - Calendar spread strategies (1M-3M, 3M-6M)
   - Regional spread analysis (LME-Shanghai, LME-CME)
   - Outright trading recommendations
   - Risk management guidelines

3. **Market Context**
   - Other metals correlation analysis
   - Macro environment impact
   - News analysis with market implications
   - Forward-looking insights

## 🚀 Advanced Features

### Multi-Exchange Integration
- **LME**: Dynamic monthly contract generation (MCU+month+year)
- **SHFE**: SCFc1-c12 contracts with CNY→USD conversion
- **CME**: HGc1-c12 contracts with cents/lb→USD/MT conversion

### Data Quality Assurance
- Comprehensive error handling and retry logic
- Alternative RIC fallback mechanisms
- Business day calculations with weekend/holiday handling
- API rate limiting compliance

### Automation Ready
- Cross-platform execution scripts
- Task scheduler integration (Windows XML template provided)
- Virtual environment auto-setup
- Unattended operation capabilities

## 📊 Performance

- **Execution Time**: 4-5 minutes (full report)
- **Data Coverage**: 95%+ success rate
- **Output Size**: ~1,675 lines of structured analysis
- **API Optimization**: Intelligent caching and batching

## 🔍 Testing

```bash
# Run comprehensive tests
cd tests/
python test_fund_positions_complete.py     # Fund position verification
python test_three_exchanges_integration.py # Multi-exchange testing
python test_dynamic_ric.py                 # Dynamic RIC generation
```

## 📚 Documentation

- **System Guide**: `docs/CLAUDE.md`
- **API Reference**: `docs/README.md`
- **Task Scheduling**: `docs/task_scheduler_template.xml`

## 🤝 Support

- **Issues**: GitHub Issues
- **Development**: See `development_scripts/` for analysis tools
- **Testing**: See `tests/` for validation scripts

## 📄 License

This project is designed for professional trading and institutional use.

---

**Last Updated**: 2025-06-26  
**Version**: 2.0 (Major Features Complete)  
**Compatibility**: LME/SHFE/CME Multi-Exchange Integration