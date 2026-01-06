"""
AI Insights Service - Intelligent recommendations for procurement analytics.

Provides:
- Cost optimization insights (price variance detection)
- Supplier risk analysis (concentration risk)
- Anomaly detection (statistical outliers)
- Consolidation recommendations

Supports hybrid mode: Built-in ML + Optional External AI (Claude/OpenAI)
"""
import uuid
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional
from django.db.models import Sum, Count, Avg, StdDev, F, Q
from django.db.models.functions import TruncMonth
from apps.procurement.models import Transaction, Supplier, Category
from .services import AnalyticsService

logger = logging.getLogger(__name__)


class AIInsightsService:
    """
    Service class for AI-powered procurement insights.
    Combines built-in ML algorithms with optional external AI enhancement.
    """

    # Thresholds for insight generation
    PRICE_VARIANCE_THRESHOLD = 0.15  # 15% price variance = insight
    SUPPLIER_CONCENTRATION_THRESHOLD = 0.30  # 30% spend with single supplier = risk
    ANOMALY_Z_SCORE_THRESHOLD = 2.0  # Standard deviations for anomaly
    CONSOLIDATION_MIN_SUPPLIERS = 3  # Minimum suppliers for consolidation insight

    def __init__(
        self,
        organization,
        use_external_ai: bool = False,
        ai_provider: str = 'anthropic',
        api_key: Optional[str] = None
    ):
        """
        Initialize AI Insights Service.

        Args:
            organization: Organization object for data scoping
            use_external_ai: Whether to enhance insights with external AI
            ai_provider: AI provider ('anthropic' or 'openai')
            api_key: API key for external AI service
        """
        self.organization = organization
        self.transactions = Transaction.objects.filter(organization=organization)
        self.analytics = AnalyticsService(organization)
        self.use_external_ai = use_external_ai
        self.ai_provider = ai_provider
        self.api_key = api_key

    def get_all_insights(self) -> dict:
        """
        Get all AI insights combined.

        Returns:
            Dictionary with insights list and summary statistics
        """
        insights = []

        # Gather all insight types
        cost_insights = self.get_cost_optimization_insights()
        risk_insights = self.get_supplier_risk_insights()
        anomaly_insights = self.get_anomaly_insights()
        consolidation_insights = self.get_consolidation_recommendations()

        insights.extend(cost_insights)
        insights.extend(risk_insights)
        insights.extend(anomaly_insights)
        insights.extend(consolidation_insights)

        # Sort by severity and potential savings
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        insights.sort(key=lambda x: (
            severity_order.get(x['severity'], 4),
            -(x.get('potential_savings', 0) or 0)
        ))

        # Enhance with external AI if enabled
        if self.use_external_ai and self.api_key:
            insights = self._enhance_with_external_ai(insights)

        # Calculate summary
        summary = {
            'total_insights': len(insights),
            'high_priority': len([i for i in insights if i['severity'] in ['critical', 'high']]),
            'total_potential_savings': sum(i.get('potential_savings', 0) or 0 for i in insights),
            'by_type': {
                'cost_optimization': len(cost_insights),
                'risk': len(risk_insights),
                'anomaly': len(anomaly_insights),
                'consolidation': len(consolidation_insights)
            }
        }

        return {
            'insights': insights,
            'summary': summary
        }

    def get_cost_optimization_insights(self) -> list:
        """
        Identify cost optimization opportunities based on price variance.

        Analyzes same items from different suppliers to find price discrepancies.
        """
        insights = []

        # Get spend by category and supplier to find variance
        category_supplier_spend = self.transactions.values(
            'category__name',
            'category__uuid',
            'supplier__name',
            'supplier__uuid'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id'),
            avg_transaction=Avg('amount')
        ).order_by('category__name', '-total_amount')

        # Group by category
        category_data = {}
        for item in category_supplier_spend:
            cat_name = item['category__name']
            if cat_name not in category_data:
                category_data[cat_name] = {
                    'uuid': str(item['category__uuid']),
                    'suppliers': []
                }
            category_data[cat_name]['suppliers'].append({
                'name': item['supplier__name'],
                'uuid': str(item['supplier__uuid']),
                'total': float(item['total_amount']),
                'avg_transaction': float(item['avg_transaction']),
                'count': item['transaction_count']
            })

        # Analyze each category for price variance
        for cat_name, data in category_data.items():
            if len(data['suppliers']) < 2:
                continue

            # Calculate variance in average transaction
            avg_prices = [s['avg_transaction'] for s in data['suppliers']]
            if not avg_prices or max(avg_prices) == 0:
                continue

            price_variance = (max(avg_prices) - min(avg_prices)) / max(avg_prices)

            if price_variance > self.PRICE_VARIANCE_THRESHOLD:
                total_category_spend = sum(s['total'] for s in data['suppliers'])
                # Potential savings = difference × transactions from expensive suppliers
                expensive_suppliers = [s for s in data['suppliers']
                                       if s['avg_transaction'] > min(avg_prices) * 1.1]
                potential_savings = sum(
                    (s['avg_transaction'] - min(avg_prices)) * s['count']
                    for s in expensive_suppliers
                )

                severity = 'high' if price_variance > 0.30 else 'medium'

                insights.append({
                    'id': str(uuid.uuid4()),
                    'type': 'cost_optimization',
                    'severity': severity,
                    'confidence': min(0.95, 0.70 + (price_variance * 0.5)),
                    'title': f'Price variance detected in {cat_name}',
                    'description': (
                        f'Found {len(data["suppliers"])} suppliers with '
                        f'{round(price_variance * 100, 1)}% price variance. '
                        f'Average prices range from ${min(avg_prices):,.2f} to '
                        f'${max(avg_prices):,.2f}.'
                    ),
                    'potential_savings': round(potential_savings, 2),
                    'affected_entities': [data['uuid']] + [s['uuid'] for s in expensive_suppliers],
                    'recommended_actions': [
                        f'Review pricing from {data["suppliers"][-1]["name"]} (lowest avg: ${min(avg_prices):,.2f})',
                        'Negotiate better rates with higher-priced suppliers',
                        'Consider consolidating purchases to preferred supplier'
                    ],
                    'created_at': datetime.now().isoformat()
                })

        return insights

    def get_supplier_risk_insights(self) -> list:
        """
        Identify supplier concentration risks.

        Flags suppliers representing too large a portion of total spend.
        """
        insights = []

        # Get total spend
        total_spend = self.transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if total_spend == 0:
            return insights

        # Get spend by supplier
        supplier_spend = self.transactions.values(
            'supplier__name',
            'supplier__uuid'
        ).annotate(
            total=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total')

        for supplier in supplier_spend:
            concentration = float(supplier['total']) / float(total_spend)

            if concentration >= self.SUPPLIER_CONCENTRATION_THRESHOLD:
                severity = 'critical' if concentration > 0.50 else 'high'

                insights.append({
                    'id': str(uuid.uuid4()),
                    'type': 'risk',
                    'severity': severity,
                    'confidence': 0.90,
                    'title': f'High supplier concentration: {supplier["supplier__name"]}',
                    'description': (
                        f'{supplier["supplier__name"]} represents '
                        f'{round(concentration * 100, 1)}% of total spend '
                        f'(${float(supplier["total"]):,.2f} of ${float(total_spend):,.2f}). '
                        f'This creates supply chain vulnerability.'
                    ),
                    'potential_savings': None,  # Risk insight, not cost saving
                    'affected_entities': [str(supplier['supplier__uuid'])],
                    'recommended_actions': [
                        'Identify alternative suppliers for key categories',
                        'Negotiate backup supply agreements',
                        'Develop supplier diversification strategy',
                        'Review contract terms for flexibility'
                    ],
                    'created_at': datetime.now().isoformat()
                })

        return insights

    def get_anomaly_insights(self, sensitivity: float = None) -> list:
        """
        Detect anomalous transactions using statistical analysis.

        Uses Z-score to identify transactions that deviate significantly from the mean.
        """
        insights = []
        sensitivity = sensitivity or self.ANOMALY_Z_SCORE_THRESHOLD

        # Get statistics by category
        category_stats = self.transactions.values(
            'category__name',
            'category__uuid'
        ).annotate(
            avg_amount=Avg('amount'),
            std_amount=StdDev('amount'),
            transaction_count=Count('id')
        ).filter(transaction_count__gt=5)  # Need enough data for meaningful stats

        for cat_stat in category_stats:
            if not cat_stat['std_amount'] or cat_stat['std_amount'] == 0:
                continue

            avg = float(cat_stat['avg_amount'])
            std = float(cat_stat['std_amount'])
            upper_threshold = avg + (sensitivity * std)
            lower_threshold = max(0, avg - (sensitivity * std))

            # Find anomalous transactions
            anomalies = self.transactions.filter(
                category__name=cat_stat['category__name']
            ).filter(
                Q(amount__gt=upper_threshold) | Q(amount__lt=lower_threshold)
            ).values(
                'uuid',
                'amount',
                'date',
                'supplier__name',
                'description'
            )[:10]  # Limit to top 10

            if anomalies:
                high_anomalies = [a for a in anomalies if float(a['amount']) > upper_threshold]
                low_anomalies = [a for a in anomalies if float(a['amount']) < lower_threshold]

                total_anomaly_spend = sum(float(a['amount']) for a in high_anomalies)

                severity = 'high' if len(high_anomalies) > 3 else 'medium'

                insights.append({
                    'id': str(uuid.uuid4()),
                    'type': 'anomaly',
                    'severity': severity,
                    'confidence': 0.75,
                    'title': f'Unusual transactions in {cat_stat["category__name"]}',
                    'description': (
                        f'Found {len(list(anomalies))} transactions outside normal range. '
                        f'Average for category: ${avg:,.2f}, Threshold: ±${sensitivity * std:,.2f}. '
                        f'{len(high_anomalies)} unusually high, {len(low_anomalies)} unusually low.'
                    ),
                    'potential_savings': round(total_anomaly_spend * 0.20, 2) if high_anomalies else None,
                    'affected_entities': [str(a['uuid']) for a in anomalies],
                    'recommended_actions': [
                        'Review flagged transactions for accuracy',
                        'Verify pricing and quantities',
                        'Check for duplicate or erroneous entries',
                        'Investigate supplier invoicing practices'
                    ],
                    'details': {
                        'category': cat_stat['category__name'],
                        'average': avg,
                        'std_deviation': std,
                        'threshold_upper': upper_threshold,
                        'threshold_lower': lower_threshold,
                        'anomaly_count': len(list(anomalies)),
                        'sample_anomalies': [
                            {
                                'uuid': str(a['uuid']),
                                'amount': float(a['amount']),
                                'date': str(a['date']),
                                'supplier': a['supplier__name']
                            }
                            for a in list(anomalies)[:5]
                        ]
                    },
                    'created_at': datetime.now().isoformat()
                })

        return insights

    def get_consolidation_recommendations(self) -> list:
        """
        Identify supplier consolidation opportunities.

        Finds categories with many suppliers that could benefit from consolidation.
        """
        insights = []

        # Get categories with multiple suppliers
        categories = self.transactions.values(
            'category__name',
            'category__uuid'
        ).annotate(
            supplier_count=Count('supplier', distinct=True),
            total_spend=Sum('amount'),
            transaction_count=Count('id')
        ).filter(supplier_count__gte=self.CONSOLIDATION_MIN_SUPPLIERS).order_by('-supplier_count')

        for cat in categories:
            # Get suppliers in this category
            suppliers = self.transactions.filter(
                category__name=cat['category__name']
            ).values(
                'supplier__name',
                'supplier__uuid'
            ).annotate(
                spend=Sum('amount'),
                count=Count('id')
            ).order_by('-spend')

            supplier_list = list(suppliers)
            top_supplier = supplier_list[0] if supplier_list else None
            top_supplier_share = (
                float(top_supplier['spend']) / float(cat['total_spend'])
                if top_supplier and cat['total_spend']
                else 0
            )

            # Potential savings: estimate 10-15% through consolidation
            potential_savings = float(cat['total_spend']) * 0.10

            severity = 'high' if cat['supplier_count'] >= 5 else 'medium'

            insights.append({
                'id': str(uuid.uuid4()),
                'type': 'consolidation',
                'severity': severity,
                'confidence': 0.80,
                'title': f'Consolidation opportunity: {cat["category__name"]}',
                'description': (
                    f'{cat["supplier_count"]} suppliers for {cat["category__name"]} '
                    f'(${float(cat["total_spend"]):,.2f} total). '
                    f'Top supplier ({top_supplier["supplier__name"] if top_supplier else "N/A"}) '
                    f'has {round(top_supplier_share * 100, 1)}% share. '
                    f'Consider consolidating to reduce costs and complexity.'
                ),
                'potential_savings': round(potential_savings, 2),
                'affected_entities': [str(cat['category__uuid'])] + [str(s['supplier__uuid']) for s in supplier_list],
                'recommended_actions': [
                    f'Evaluate {top_supplier["supplier__name"] if top_supplier else "primary supplier"} as preferred vendor',
                    'Request volume discount proposals',
                    'Review supplier performance metrics',
                    'Develop preferred supplier program'
                ],
                'details': {
                    'category': cat['category__name'],
                    'supplier_count': cat['supplier_count'],
                    'total_spend': float(cat['total_spend']),
                    'suppliers': [
                        {
                            'name': s['supplier__name'],
                            'spend': float(s['spend']),
                            'share': round(float(s['spend']) / float(cat['total_spend']) * 100, 1)
                        }
                        for s in supplier_list[:5]
                    ]
                },
                'created_at': datetime.now().isoformat()
            })

        return insights

    def _enhance_with_external_ai(self, insights: list) -> list:
        """
        Enhance insights with external AI analysis.

        Uses Claude or OpenAI to provide additional context and recommendations.
        """
        if not self.api_key:
            return insights

        try:
            if self.ai_provider == 'anthropic':
                return self._enhance_with_claude(insights)
            elif self.ai_provider == 'openai':
                return self._enhance_with_openai(insights)
            else:
                logger.warning(f"Unknown AI provider: {self.ai_provider}")
                return insights
        except Exception as e:
            logger.error(f"External AI enhancement failed: {e}")
            return insights

    def _enhance_with_claude(self, insights: list) -> list:
        """Enhance insights using Claude API."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Prepare context
            insights_summary = "\n".join([
                f"- {i['type']}: {i['title']} (${i.get('potential_savings', 0):,.2f} potential savings)"
                for i in insights[:10]  # Limit to top 10 for context
            ])

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"""As a procurement analytics expert, review these insights and provide
                        2-3 additional strategic recommendations:

                        Insights:
                        {insights_summary}

                        Provide brief, actionable recommendations focused on cost savings and risk mitigation.
                        Format as a simple list."""
                    }
                ]
            )

            # Add AI recommendations to first insight
            if insights and message.content:
                ai_text = message.content[0].text if message.content else ""
                insights[0]['ai_enhanced'] = True
                insights[0]['ai_recommendations'] = ai_text

        except ImportError:
            logger.warning("anthropic package not installed, skipping Claude enhancement")
        except Exception as e:
            logger.error(f"Claude API error: {e}")

        return insights

    def _enhance_with_openai(self, insights: list) -> list:
        """Enhance insights using OpenAI API."""
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            # Prepare context
            insights_summary = "\n".join([
                f"- {i['type']}: {i['title']} (${i.get('potential_savings', 0):,.2f} potential savings)"
                for i in insights[:10]
            ])

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a procurement analytics expert providing actionable recommendations."
                    },
                    {
                        "role": "user",
                        "content": f"""Review these procurement insights and provide 2-3 additional
                        strategic recommendations:

                        {insights_summary}

                        Focus on cost savings and risk mitigation. Be brief and actionable."""
                    }
                ],
                max_tokens=500
            )

            # Add AI recommendations
            if insights and response.choices:
                ai_text = response.choices[0].message.content
                insights[0]['ai_enhanced'] = True
                insights[0]['ai_recommendations'] = ai_text

        except ImportError:
            logger.warning("openai package not installed, skipping OpenAI enhancement")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")

        return insights

    def get_insights_by_type(self, insight_type: str) -> list:
        """
        Get insights filtered by type.

        Args:
            insight_type: One of 'cost_optimization', 'risk', 'anomaly', 'consolidation'
        """
        type_methods = {
            'cost': self.get_cost_optimization_insights,
            'cost_optimization': self.get_cost_optimization_insights,
            'risk': self.get_supplier_risk_insights,
            'anomaly': self.get_anomaly_insights,
            'anomalies': self.get_anomaly_insights,
            'consolidation': self.get_consolidation_recommendations,
        }

        method = type_methods.get(insight_type.lower())
        if method:
            return method()
        else:
            raise ValueError(f"Unknown insight type: {insight_type}")
