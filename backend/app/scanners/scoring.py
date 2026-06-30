from typing import Tuple

class ScoringEngine:
    @staticmethod
    def calculate_pillar(pillar_name: str, checks: dict, weights: dict) -> Tuple[float, float, str]:
        total_possible = sum(weights.values())
        achieved = 0.0
        explanations = []
        
        for key, w in weights.items():
            if checks.get(key, {}).get("found"):
                achieved += w
                explanations.append(f"{key.replace('_', ' ').title()}: +{w}")
            else:
                explanations.append(f"{key.replace('_', ' ').title()}: 0/{w}")
                
        if total_possible > 0:
            weighted = (achieved / total_possible) * 20.0
        else:
            weighted = 0.0
            
        weighted = min(20.0, max(0.0, weighted))
        explanation_str = " | ".join(explanations)
        return achieved, weighted, explanation_str

    @staticmethod
    def get_grade(score: int) -> str:
        if score >= 90: return "Excellent"
        if score >= 70: return "Good"
        if score >= 50: return "Average"
        return "Needs Improvement"
