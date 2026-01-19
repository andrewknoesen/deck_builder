import re
from typing import Dict, List, Any
from app.models.card import Card
from app.models.deck import Deck

class DeckStatsService:
    @staticmethod
    def calculate_stats(deck: Deck) -> Dict[str, Any]:
        """
        Calculate comprehensive stats for a deck including mana curve,
        color distribution, and land recommendations.
        """
        cards = deck.cards
        
        # 1. Prepare Data
        total_cards = sum(dc.quantity for dc in cards)
        non_lands = []
        lands = []
        ramp_count = 0
        cantrip_count = 0
        
        mana_curve = {str(i): 0 for i in range(7)}
        mana_curve["7+"] = 0
        
        total_cmc = 0.0
        
        for dc in cards:
            if not dc.card:
                continue
                
            qty = dc.quantity
            card = dc.card
            
            is_land = "Land" in (card.type_line or "")
            
            if is_land:
                lands.append(dc)
            else:
                non_lands.append(dc)
                cmc = DeckStatsService._calculate_cmc(card.mana_cost or "")
                
                # Mana Curve
                bucket = min(int(cmc), 7)
                key = "7+" if bucket >= 7 else str(bucket)
                mana_curve[key] += qty
                
                # Avg CMC stats
                total_cmc += (cmc * qty)
                
                # Heuristics for Ramp/Cantrip
                # Ramp: Artifact/Creature, CMC <= 2, produces mana (oracle text 'add {')
                if cmc <= 2 and ("Creature" in (card.type_line or "") or "Artifact" in (card.type_line or "")):
                    if "add {" in (card.oracle_text or "").lower():
                        ramp_count += qty
                        
                # Cantrip: CMC <= 2, draws card
                if cmc <= 2 and "draw a card" in (card.oracle_text or "").lower():
                    cantrip_count += qty

        avg_cmc = total_cmc / sum(dc.quantity for dc in non_lands) if non_lands else 0
        
        # 2. Recommendations
        is_commander = total_cards > 80 # Simple heuristic
        
        if is_commander:
            base_lands = 31.42 + (3.13 * avg_cmc)
            limit_min, limit_max = 30, 42
        else:
            base_lands = 16 + (3.14 * avg_cmc)
            limit_min, limit_max = 18, 30
            
        recommended = base_lands - (0.5 * ramp_count) - (0.25 * cantrip_count)
        recommended = max(limit_min, min(limit_max, round(recommended)))
        
        # 3. Color Stats
        color_stats = DeckStatsService._calculate_color_needs(non_lands, lands, is_commander)
        
        return {
            "total_cards": total_cards,
            "mana_curve": mana_curve,
            "average_cmc": round(avg_cmc, 2),
            "recommendations": {
                "land_count": recommended,
                "ramp_count": ramp_count,
                "cantrip_count": cantrip_count,
                "reasoning": f"Based on avg CMC {round(avg_cmc, 2)} and {ramp_count} ramp sources."
            },
            "color_stats": color_stats
        }

    @staticmethod
    def _calculate_cmc(mana_cost: str) -> float:
        if not mana_cost:
            return 0
        
        cmc = 0
        # Count generic numbers e.g. {2}
        numbers = re.findall(r'\{(\d+)\}', mana_cost)
        for num in numbers:
            cmc += int(num)
            
        # Count pips e.g. {W}, {U/B} counts as 1 usually for CMC
        # Simple count of {...} minus the generic numbers
        # Actually easier: Remove regex matches for {\d+} then count remaining {}
        
        remaining = re.sub(r'\{(\d+)\}', '', mana_cost)
        pips = len(re.findall(r'\{.*?\}', remaining))
        cmc += pips
        
        return float(cmc)
        
    @staticmethod
    def _calculate_color_needs(non_lands: List[Any], lands: List[Any], is_commander: bool) -> Dict[str, Any]:
        """
        Calculate pip counts, source counts, and recommended sources based on Karsten's heuristics.
        """
        colors = ["W", "U", "B", "R", "G", "C"]
        stats = {c: {"pips": 0, "sources": 0, "recommended_sources": 0} for c in colors}
        
        # Karsten Tables (Simplified)
        # Format: (CMC/Turn, Pips) -> Required Sources
        # Values for 60-card / Commander
        karsten_table = {
            (1, 1): (14, 23), # {C} Turn 1
            (2, 1): (13, 20), # {1}{C} Turn 2
            (2, 2): (20, 33), # {C}{C} Turn 2
            (3, 1): (12, 19), # {2}{C} Turn 3
            (3, 2): (18, 29), # {1}{C}{C} Turn 3
            (3, 3): (23, 38), # {C}{C}{C} Turn 3
            (4, 1): (11, 18), # {3}{C} Turn 4
            (4, 2): (16, 26), # {2}{C}{C} Turn 4
            (4, 3): (20, 32), # {1}{C}{C}{C} Turn 4 (Extrapolated)
        }
        
        # 1. Count Pips & Requirements
        for dc in non_lands:
            if not dc.card or not dc.card.mana_cost:
                continue
                
            qty = dc.quantity
            cost = dc.card.mana_cost
            
            # Simple CMC for turn estimation
            cmc = int(DeckStatsService._calculate_cmc(cost))
            
            for color in ["W", "U", "B", "R", "G"]:
                # Count pips
                pips = len(re.findall(f"{{{color}}}", cost))
                if pips > 0:
                    stats[color]["pips"] += (pips * qty)
                    
                    # Determine recommendation (Max of any card)
                    # Turn is roughly CMC (clamped to sensible range for table 1-4)
                    turn = max(1, min(4, cmc))
                    # Pips restricted to max 3 for table lookup
                    lookup_pips = min(3, pips)
                    
                    if (turn, lookup_pips) in karsten_table:
                        req_60, req_cmd = karsten_table[(turn, lookup_pips)]
                        req = req_cmd if is_commander else req_60
                        stats[color]["recommended_sources"] = max(stats[color]["recommended_sources"], req)

            # Colorless pips (C)
            c_pips = len(re.findall(r"\{C\}", cost))
            if c_pips > 0:
                stats["C"]["pips"] += (c_pips * qty)
                
        # 2. Count Sources
        for dc in lands:
            if not dc.card:
                continue
            
            qty = dc.quantity
            produced = dc.card.produced_mana or []
            
            for p in produced:
                if p in stats:
                    stats[p]["sources"] += qty
                    
            # Basic land / Colorless heuristic
            if not produced and "Land" in (dc.card.type_line or ""):
                # Assume produces colorless if logic fails, or generic utility land
                # But safer to rely on produced_mana being correct now
                pass

        return stats
