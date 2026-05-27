from __future__ import annotations

from typing import Any


def generate_demo_insight(voc: Any, analysis: Any, lead_score: Any) -> dict[str, Any]:
    topic = analysis.topic
    title = _title_for_topic(topic, lead_score.priority)
    action = _action_for_topic(topic, voc.product_category)

    return {
        "title": title,
        "summary": f"{voc.source} VOC indicates {analysis.intent} purchase intent around {voc.product_category} with {analysis.sentiment} sentiment.",
        "recommended_action": action,
        "reasoning": (
            f"Topic '{topic}' was detected from VOC keywords, lead score is {lead_score.lead_score}, "
            f"and priority is {lead_score.priority} based on intent, urgency, competitor mentions, source weight, and engagement."
        ),
        "priority": lead_score.priority,
        "target_segment": voc.product_category,
        "confidence": min(0.96, round((analysis.confidence + (lead_score.lead_score / 100)) / 2, 2)),
    }


def _title_for_topic(topic: str, priority: str) -> str:
    if topic == "Subscription Pricing":
        return "Price-sensitive subscription customer detected"
    if topic == "Installation Issues":
        return "Installation friction requires follow-up"
    if topic == "ThinQ Connectivity":
        return "ThinQ app connectivity is affecting product experience"
    if topic == "Air Quality Demand":
        return "Air quality context creates air purifier demand"
    if topic == "Energy Efficiency":
        return "Energy-saving value proposition is resonating"
    if priority == "high":
        return "High-priority VOC requires sales action"
    return "VOC insight ready for sales review"


def _action_for_topic(topic: str, product_category: str) -> str:
    if topic == "Subscription Pricing":
        return "Offer subscription bundle discount and compare total cost of ownership."
    if topic == "Installation Issues":
        return "Trigger installation recovery call and provide expected schedule."
    if topic == "ThinQ Connectivity":
        return "Send ThinQ setup guide and route recurring app issues to CX follow-up."
    if topic == "Air Quality Demand":
        return "Recommend filter subscription and seasonal air quality campaign."
    if topic == "Energy Efficiency":
        return "Highlight energy saving features and summer bundle promotion."
    return f"Prepare a product-specific response for {product_category}."
