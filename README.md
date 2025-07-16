# Healthcare Architecture Cost Modeling Tool

A robust, flexible, and visually engaging cost modeling tool designed for healthcare architecture projects. This tool helps communicate first-cost trade-offs across major building systems for both client-facing presentations and internal design decision-making.

## Features

### ✅ Category-Based Cost Modeling
- Break down total project costs into 8 key categories:
  - Enclosure (Envelope)
  - Superstructure
  - Foundation
  - Plumbing
  - Mechanical
  - Electrical
  - Equipment
  - Contractor & A/E Fees

### ✅ Rule-Based Trade-Off Logic
- Automatic cost adjustments based on investment changes:
  - +10% to Envelope → -8% Mechanical, -3% Electrical
  - +5% to Superstructure → -3% Foundation
  - +10% to Plumbing (with heat recovery) → -6% Electrical, -4% Mechanical

### ✅ Visual Outputs
- **Comparison View**: Side-by-side baseline vs. adjusted allocations
- **Breakdown View**: Interactive treemap showing dollar amounts
- **Trade-off Analysis**: Waterfall chart showing changes from baseline

### ✅ Export Capabilities
- **CSV Export**: Detailed cost breakdown data
- **PNG Export**: High-resolution chart images
- **PDF Report**: Comprehensive report with all visualizations

### ✅ Presentation Mode
- Clean interface for client meetings
- Slide-based navigation
- Auto-generated insights

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd healthcare-cost-modeler
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
cd app
python app.py
```

2. Open your browser to `http://localhost:8050`

3. Adjust cost allocations using the sliders to see real-time trade-offs

4. Switch between visualization tabs to explore different views

5. Export your analysis using the export buttons

## Project Structure

```
healthcare-cost-modeler/
├── app/
│   ├── app.py              # Main Dash application
│   ├── config.py           # Configuration and constants
│   ├── models.py           # Cost model logic
│   ├── export_utils.py     # Export functionality
│   └── presentation_mode.py # Presentation interface
├── static/
│   └── css/
│       └── styles.css      # Custom styling
├── exports/                # Export output directory
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Customization

### Modifying Trade-Off Rules

Edit `app/config.py` to adjust the trade-off multipliers:

```python
TRADE_OFF_RULES = {
    "envelope": {
        "mechanical": -0.8,  # Adjust multiplier
        "electrical": -0.3
    },
    # Add more rules...
}
```

### Adding New Categories

1. Add to `COST_CATEGORIES` in `app/config.py`
2. Update base percentages to ensure they sum to 100%
3. Add any relevant trade-off rules

### Styling

Custom styles can be added to `static/css/styles.css`. The app uses Bootstrap 5 components.

## Future Enhancements

- **BIM Integration**: Connect with Revit/Rhino/Grasshopper
- **Database Backend**: Store and retrieve project data
- **User Authentication**: Multi-user support with saved scenarios
- **Advanced Analytics**: ROI calculations, lifecycle cost analysis
- **Custom Rule Builder**: UI for creating trade-off rules

## Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 4GB RAM minimum
- 500MB disk space

## License

This project is proprietary software for healthcare architecture cost modeling.