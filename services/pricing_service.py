from datetime import datetime
from database.models import db, PricingRule
from config import Config

class PricingService:
    @staticmethod
    def get_pricing_rule(category: str) -> dict:
        """Fetch current pricing rule for a given category."""
        rule = PricingRule.query.filter_by(category=category).first()
        if not rule:
            default = Config.DEFAULT_PRICING.get(category, Config.DEFAULT_PRICING[Config.CATEGORY_NORMAL])
            return default
        return rule.to_dict()

    @staticmethod
    def get_all_pricing_rules() -> list:
        """Fetch all pricing rules for all categories."""
        rules = PricingRule.query.all()
        return [r.to_dict() for r in rules]

    @staticmethod
    def update_pricing_rule(category: str, free_minutes: int, grace_minutes: int,
                            charge_amount: float, billing_interval_minutes: int,
                            rounding_policy: str = "CEIL", updated_by: str = "Guard") -> dict:
        """Update a pricing rule for a specific category."""
        rule = PricingRule.query.filter_by(category=category).first()
        if not rule:
            rule = PricingRule(category=category)
            db.session.add(rule)

        rule.free_minutes = max(0, int(free_minutes))
        rule.grace_minutes = max(0, int(grace_minutes))
        rule.charge_amount = max(0.0, float(charge_amount))
        rule.billing_interval_minutes = max(1, int(billing_interval_minutes))
        rule.rounding_policy = rounding_policy
        rule.updated_by = updated_by
        rule.updated_at = datetime.utcnow()

        db.session.commit()
        return rule.to_dict()

