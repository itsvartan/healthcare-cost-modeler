import numpy as np
from typing import Dict, List
from app.config import COST_CATEGORIES, TRADE_OFF_RULES

class CostModel:
    def __init__(self, total_project_cost: float = 50_000_000):
        self.total_project_cost = total_project_cost
        self.base_allocations = {cat["id"]: cat["base_percentage"] for cat in COST_CATEGORIES}
        self.current_allocations = self.base_allocations.copy()
        self.adjustments = {cat_id: 0.0 for cat_id in self.base_allocations}
        
    def update_allocation(self, category_id: str, new_percentage: float) -> Dict[str, float]:
        """Update allocation for a category and apply trade-off rules"""
        old_percentage = self.current_allocations[category_id]
        delta = new_percentage - self.base_allocations[category_id]
        
        # Reset all allocations to base
        self.current_allocations = self.base_allocations.copy()
        self.adjustments = {cat_id: 0.0 for cat_id in self.base_allocations}
        
        # Apply the direct change
        self.current_allocations[category_id] = new_percentage
        self.adjustments[category_id] = delta
        
        # Apply trade-off rules
        if category_id in TRADE_OFF_RULES and delta != 0:
            for affected_category, multiplier in TRADE_OFF_RULES[category_id].items():
                adjustment = delta * multiplier / 10  # Normalize to percentage points
                self.current_allocations[affected_category] += adjustment
                self.adjustments[affected_category] += adjustment
        
        # Ensure allocations sum to 100%
        self._normalize_allocations()
        
        return self.current_allocations
    
    def _normalize_allocations(self):
        """Ensure allocations sum to 100%"""
        total = sum(self.current_allocations.values())
        if total != 100.0:
            factor = 100.0 / total
            for cat_id in self.current_allocations:
                self.current_allocations[cat_id] *= factor
    
    def get_dollar_amounts(self) -> Dict[str, float]:
        """Convert percentages to dollar amounts"""
        return {
            cat_id: self.total_project_cost * (pct / 100)
            for cat_id, pct in self.current_allocations.items()
        }
    
    def get_deltas(self) -> Dict[str, float]:
        """Get the difference from baseline in dollars"""
        baseline_dollars = {
            cat_id: self.total_project_cost * (pct / 100)
            for cat_id, pct in self.base_allocations.items()
        }
        current_dollars = self.get_dollar_amounts()
        
        return {
            cat_id: current_dollars[cat_id] - baseline_dollars[cat_id]
            for cat_id in baseline_dollars
        }
    
    def reset(self):
        """Reset to baseline allocations"""
        self.current_allocations = self.base_allocations.copy()
        self.adjustments = {cat_id: 0.0 for cat_id in self.base_allocations}