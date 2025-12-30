"""
Analytics business logic and calculations
"""
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from apps.procurement.models import Transaction, Supplier, Category


class AnalyticsService:
    """
    Service class for analytics calculations
    """
    
    def __init__(self, organization):
        self.organization = organization
        self.transactions = Transaction.objects.filter(organization=organization)
    
    def get_overview_stats(self):
        """
        Get overview statistics
        """
        stats = self.transactions.aggregate(
            total_spend=Sum('amount'),
            transaction_count=Count('id'),
            supplier_count=Count('supplier', distinct=True),
            category_count=Count('category', distinct=True),
            avg_transaction=Avg('amount')
        )
        
        return {
            'total_spend': float(stats['total_spend'] or 0),
            'transaction_count': stats['transaction_count'] or 0,
            'supplier_count': stats['supplier_count'] or 0,
            'category_count': stats['category_count'] or 0,
            'avg_transaction': float(stats['avg_transaction'] or 0)
        }
    
    def get_spend_by_category(self):
        """
        Get spend breakdown by category
        """
        data = self.transactions.values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return [
            {
                'category': item['category__name'],
                'amount': float(item['total']),
                'count': item['count']
            }
            for item in data
        ]
    
    def get_spend_by_supplier(self):
        """
        Get spend breakdown by supplier
        """
        data = self.transactions.values(
            'supplier__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return [
            {
                'supplier': item['supplier__name'],
                'amount': float(item['total']),
                'count': item['count']
            }
            for item in data
        ]
    
    def get_monthly_trend(self, months=12):
        """
        Get monthly spend trend
        """
        cutoff_date = datetime.now().date() - timedelta(days=months*30)
        
        data = self.transactions.filter(
            date__gte=cutoff_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'amount': float(item['total']),
                'count': item['count']
            }
            for item in data
        ]
    
    def get_pareto_analysis(self):
        """
        Get Pareto analysis (80/20 rule) for suppliers
        """
        suppliers = self.transactions.values(
            'supplier__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        total_spend = sum(s['total'] for s in suppliers)
        cumulative = 0
        result = []
        
        for supplier in suppliers:
            cumulative += supplier['total']
            percentage = (cumulative / total_spend * 100) if total_spend > 0 else 0
            
            result.append({
                'supplier': supplier['supplier__name'],
                'amount': float(supplier['total']),
                'cumulative_percentage': round(percentage, 2)
            })
        
        return result
    
    def get_tail_spend_analysis(self, threshold_percentage=20):
        """
        Analyze tail spend (bottom X% of suppliers)
        """
        suppliers = list(self.transactions.values(
            'supplier__name',
            'supplier_id'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total'))
        
        total_spend = sum(s['total'] for s in suppliers) or Decimal('0')
        threshold_amount = total_spend * Decimal(str(threshold_percentage)) / Decimal('100')
        
        cumulative = 0
        tail_suppliers = []
        
        # Find tail suppliers (from bottom)
        for supplier in reversed(suppliers):
            if cumulative >= threshold_amount:
                break
            cumulative += supplier['total']
            tail_suppliers.append({
                'supplier': supplier['supplier__name'],
                'supplier_id': supplier['supplier_id'],
                'amount': float(supplier['total']),
                'transaction_count': supplier['count']
            })
        
        return {
            'tail_suppliers': tail_suppliers,
            'tail_count': len(tail_suppliers),
            'tail_spend': float(cumulative),
            'tail_percentage': round((cumulative / total_spend * 100) if total_spend > 0 else 0, 2)
        }
    
    def get_spend_stratification(self):
        """
        Categorize spend into strategic, leverage, bottleneck, and tactical
        Based on spend value and supplier count
        """
        categories = self.transactions.values(
            'category__name',
            'category_id'
        ).annotate(
            total_spend=Sum('amount'),
            supplier_count=Count('supplier', distinct=True),
            transaction_count=Count('id')
        )
        
        # Calculate medians for classification
        spends = [c['total_spend'] for c in categories]
        supplier_counts = [c['supplier_count'] for c in categories]
        
        median_spend = sorted(spends)[len(spends)//2] if spends else 0
        median_suppliers = sorted(supplier_counts)[len(supplier_counts)//2] if supplier_counts else 0
        
        result = {
            'strategic': [],  # High spend, few suppliers
            'leverage': [],   # High spend, many suppliers
            'bottleneck': [], # Low spend, few suppliers
            'tactical': []    # Low spend, many suppliers
        }
        
        for cat in categories:
            item = {
                'category': cat['category__name'],
                'spend': float(cat['total_spend']),
                'supplier_count': cat['supplier_count'],
                'transaction_count': cat['transaction_count']
            }
            
            if cat['total_spend'] >= median_spend:
                if cat['supplier_count'] <= median_suppliers:
                    result['strategic'].append(item)
                else:
                    result['leverage'].append(item)
            else:
                if cat['supplier_count'] <= median_suppliers:
                    result['bottleneck'].append(item)
                else:
                    result['tactical'].append(item)
        
        return result
    
    def get_seasonality_analysis(self):
        """
        Analyze spending patterns by month across years
        """
        data = self.transactions.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # Group by month number
        monthly_avg = {}
        for item in data:
            month_num = item['month'].month
            if month_num not in monthly_avg:
                monthly_avg[month_num] = []
            monthly_avg[month_num].append(float(item['total']))
        
        # Calculate averages
        result = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month_num in range(1, 13):
            values = monthly_avg.get(month_num, [0])
            result.append({
                'month': month_names[month_num-1],
                'average_spend': round(sum(values) / len(values), 2),
                'occurrences': len(values)
            })
        
        return result
    
    def get_year_over_year_comparison(self):
        """
        Compare spending year over year
        """
        data = self.transactions.annotate(
            year=TruncYear('date')
        ).values('year').annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        ).order_by('year')
        
        result = []
        for i, item in enumerate(data):
            year_data = {
                'year': item['year'].year,
                'total_spend': float(item['total']),
                'transaction_count': item['count'],
                'avg_transaction': float(item['avg'])
            }
            
            # Calculate growth if previous year exists
            if i > 0:
                prev_total = float(data[i-1]['total'])
                growth = ((float(item['total']) - prev_total) / prev_total * 100) if prev_total > 0 else 0
                year_data['growth_percentage'] = round(growth, 2)
            
            result.append(year_data)
        
        return result
    
    def get_supplier_consolidation_opportunities(self):
        """
        Identify opportunities for supplier consolidation
        """
        # Find categories with multiple suppliers
        categories_with_multiple = self.transactions.values(
            'category__name',
            'category_id'
        ).annotate(
            supplier_count=Count('supplier', distinct=True),
            total_spend=Sum('amount')
        ).filter(supplier_count__gt=2).order_by('-supplier_count')
        
        opportunities = []
        for cat in categories_with_multiple:
            # Get suppliers in this category
            suppliers = self.transactions.filter(
                category_id=cat['category_id']
            ).values('supplier__name').annotate(
                spend=Sum('amount')
            ).order_by('-spend')
            
            opportunities.append({
                'category': cat['category__name'],
                'supplier_count': cat['supplier_count'],
                'total_spend': float(cat['total_spend']),
                'suppliers': [
                    {
                        'name': s['supplier__name'],
                        'spend': float(s['spend'])
                    }
                    for s in suppliers
                ],
                'potential_savings': float(cat['total_spend'] * Decimal('0.10'))  # Estimate 10% savings
            })
        
        return opportunities
