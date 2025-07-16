COST_CATEGORIES = [
    {"id": "envelope", "name": "Enclosure (Envelope)", "base_percentage": 15.0, "color": "#2E86AB"},
    {"id": "superstructure", "name": "Superstructure", "base_percentage": 20.0, "color": "#A23B72"},
    {"id": "foundation", "name": "Foundation", "base_percentage": 10.0, "color": "#F18F01"},
    {"id": "plumbing", "name": "Plumbing", "base_percentage": 8.0, "color": "#C73E1D"},
    {"id": "mechanical", "name": "Mechanical", "base_percentage": 18.0, "color": "#6A994E"},
    {"id": "electrical", "name": "Electrical", "base_percentage": 12.0, "color": "#BC4B51"},
    {"id": "equipment", "name": "Equipment", "base_percentage": 7.0, "color": "#5B8C85"},
    {"id": "fees", "name": "Contractor & A/E Fees", "base_percentage": 10.0, "color": "#8B5A3C"}
]

TRADE_OFF_RULES = {
    "envelope": {
        "mechanical": -0.8,  # +10% envelope = -8% mechanical
        "electrical": -0.3   # +10% envelope = -3% electrical
    },
    "superstructure": {
        "foundation": -0.6   # +5% superstructure = -3% foundation
    },
    "plumbing": {
        "electrical": -0.6,  # +10% plumbing = -6% electrical
        "mechanical": -0.4   # +10% plumbing = -4% mechanical
    }
}

DEFAULT_PROJECT_COST = 50_000_000  # $50M default project