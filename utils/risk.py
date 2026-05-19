from typing import Any, Dict

import pandas as pd

RiskSummary = Dict[str, Any]


EMPTY_RISK_DISTRIBUTION = pd.DataFrame(
    {"Risk Level": ["Low Risk", "Medium Risk", "High Risk"], "Count": [0, 0, 0]}
)
EMPTY_CONTRIBUTORS = pd.DataFrame({"Factor": [], "Count": []})


def build_user_risk_profile(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    profile = (
        df.groupby(["user_id", "full_name", "department"])
        .agg(
            total_events=("user_id", "size"),
            anomaly_events=("unusual_query_flag", "sum"),
            sensitive_events=("sensitive_data_access", "sum"),
            after_hours_events=("after_hours_access", "sum"),
            failed_login_events=("failed_login_attempt", "sum"),
            exfiltration_events=("data_exfiltration_pattern", "sum"),
        )
        .reset_index()
    )

    for rate_col, source_col in {
        "anomaly_rate": "anomaly_events",
        "sensitive_rate": "sensitive_events",
        "after_hours_rate": "after_hours_events",
        "failed_login_rate": "failed_login_events",
        "exfiltration_rate": "exfiltration_events",
    }.items():
        profile[rate_col] = profile[source_col] / profile["total_events"]

    profile["risk_score"] = (
        (profile["anomaly_rate"] * 55)
        + (profile["exfiltration_rate"] * 20)
        + (profile["sensitive_rate"] * 15)
        + (profile["after_hours_rate"] * 5)
        + (profile["failed_login_rate"] * 5)
    ).round(1)

    rank = profile["risk_score"].rank(pct=True, method="first")
    profile["risk_level"] = "Low Risk"
    profile.loc[rank >= 0.4, "risk_level"] = "Medium Risk"
    profile.loc[rank >= 0.75, "risk_level"] = "High Risk"
    return profile.sort_values("risk_score", ascending=False)


def summarize_risk(df: pd.DataFrame) -> RiskSummary:
    if df.empty:
        return {
            "total_users": 0,
            "high_risk_users": 0,
            "medium_risk_users": 0,
            "low_risk_users": 0,
            "risk_distribution": EMPTY_RISK_DISTRIBUTION.copy(),
            "risk_contributors": EMPTY_CONTRIBUTORS.copy(),
            "user_risk_profile": pd.DataFrame(),
        }

    profile = build_user_risk_profile(df)
    counts_dict = profile["risk_level"].value_counts().to_dict()
    distribution = pd.DataFrame(
        {
            "Risk Level": ["Low Risk", "Medium Risk", "High Risk"],
            "Count": [
                counts_dict.get("Low Risk", 0),
                counts_dict.get("Medium Risk", 0),
                counts_dict.get("High Risk", 0),
            ],
        }
    )
    contributors = pd.DataFrame(
        {
            "Factor": [
                "Sensitive Data Access",
                "After-Hours Access",
                "ML Anomaly Flag",
                "Failed Login Attempt",
                "Exfiltration Pattern",
            ],
            "Count": [
                int(df["sensitive_data_access"].sum()),
                int(df["after_hours_access"].sum()),
                int(df["unusual_query_flag"].sum()),
                int(df["failed_login_attempt"].sum()),
                int(df["data_exfiltration_pattern"].sum()),
            ],
        }
    ).sort_values("Count", ascending=True)

    return {
        "total_users": len(profile),
        "high_risk_users": counts_dict.get("High Risk", 0),
        "medium_risk_users": counts_dict.get("Medium Risk", 0),
        "low_risk_users": counts_dict.get("Low Risk", 0),
        "risk_distribution": distribution,
        "risk_contributors": contributors,
        "user_risk_profile": profile,
    }
