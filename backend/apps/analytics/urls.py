"""
URL patterns for analytics
"""
from django.urls import path
from . import views

urlpatterns = [
    # Core Analytics
    path('overview/', views.overview_stats, name='overview-stats'),
    path('spend-by-category/', views.spend_by_category, name='spend-by-category'),
    path('spend-by-supplier/', views.spend_by_supplier, name='spend-by-supplier'),
    path('monthly-trend/', views.monthly_trend, name='monthly-trend'),
    path('pareto/', views.pareto_analysis, name='pareto-analysis'),
    path('tail-spend/', views.tail_spend_analysis, name='tail-spend'),
    path('stratification/', views.spend_stratification, name='stratification'),
    path('seasonality/', views.seasonality_analysis, name='seasonality'),
    path('year-over-year/', views.year_over_year, name='year-over-year'),
    path('consolidation/', views.consolidation_opportunities, name='consolidation'),

    # AI Insights
    path('ai-insights/', views.ai_insights, name='ai-insights'),
    path('ai-insights/cost/', views.ai_insights_cost, name='ai-insights-cost'),
    path('ai-insights/risk/', views.ai_insights_risk, name='ai-insights-risk'),
    path('ai-insights/anomalies/', views.ai_insights_anomalies, name='ai-insights-anomalies'),

    # Predictive Analytics
    path('predictions/spending/', views.spending_forecast, name='spending-forecast'),
    path('predictions/category/<int:category_id>/', views.category_forecast, name='category-forecast'),
    path('predictions/supplier/<int:supplier_id>/', views.supplier_forecast, name='supplier-forecast'),
    path('predictions/trends/', views.trend_analysis, name='trend-analysis'),
    path('predictions/budget/', views.budget_projection, name='budget-projection'),

    # Contract Analytics
    path('contracts/overview/', views.contract_overview, name='contract-overview'),
    path('contracts/', views.contracts_list, name='contracts-list'),
    path('contracts/<int:contract_id>/', views.contract_detail, name='contract-detail'),
    path('contracts/expiring/', views.expiring_contracts, name='expiring-contracts'),
    path('contracts/<int:contract_id>/performance/', views.contract_performance, name='contract-performance'),
    path('contracts/savings/', views.contract_savings_opportunities, name='contract-savings'),
    path('contracts/renewals/', views.contract_renewals, name='contract-renewals'),
    path('contracts/vs-actual/', views.contract_vs_actual, name='contract-vs-actual'),

    # Compliance & Maverick Spend
    path('compliance/overview/', views.compliance_overview, name='compliance-overview'),
    path('compliance/maverick-spend/', views.maverick_spend_analysis, name='maverick-spend'),
    path('compliance/violations/', views.policy_violations, name='policy-violations'),
    path('compliance/violations/<int:violation_id>/resolve/', views.resolve_violation, name='resolve-violation'),
    path('compliance/trends/', views.violation_trends, name='violation-trends'),
    path('compliance/supplier-scores/', views.supplier_compliance_scores, name='supplier-compliance-scores'),
    path('compliance/policies/', views.spending_policies, name='spending-policies'),
]
