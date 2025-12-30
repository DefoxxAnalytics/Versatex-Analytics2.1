"""
Views for procurement data management with security features:
- Rate limiting on sensitive operations (upload, export, bulk_delete)
- Organization-scoped data access
- Object-level permission checks
- Audit logging for all operations
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from apps.authentication.permissions import CanUploadData, CanDeleteData
from apps.authentication.utils import log_action
from .models import Supplier, Category, Transaction, DataUpload
from .serializers import (
    SupplierSerializer, CategorySerializer, TransactionSerializer,
    TransactionCreateSerializer, TransactionBulkDeleteSerializer,
    DataUploadSerializer, CSVUploadSerializer
)
from .services import CSVProcessor, bulk_delete_transactions, export_transactions_to_csv


class UploadThrottle(ScopedRateThrottle):
    """Rate limiting for file upload operations (10/hour per user)"""
    scope = 'uploads'


class ExportThrottle(ScopedRateThrottle):
    """Rate limiting for export operations (30/hour per user)"""
    scope = 'exports'


class BulkDeleteThrottle(ScopedRateThrottle):
    """Rate limiting for bulk delete operations (10/hour per user)"""
    scope = 'bulk_delete'


class ReadAPIThrottle(ScopedRateThrottle):
    """Rate limiting for read API operations (500/hour per user)"""
    scope = 'read_api'


def check_object_organization(obj, user):
    """
    Verify that an object belongs to the user's organization.
    Raises PermissionDenied if organization mismatch.
    """
    if not hasattr(user, 'profile'):
        raise PermissionDenied("User profile not found")
    if obj.organization != user.profile.organization:
        raise PermissionDenied("Cannot access data from another organization")


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Supplier CRUD
    """
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadAPIThrottle]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        # Only show suppliers from user's organization
        if not hasattr(self.request.user, 'profile'):
            return Supplier.objects.none()

        queryset = Supplier.objects.filter(
            organization=self.request.user.profile.organization
        )

        # Annotate with transaction count and total spend
        queryset = queryset.annotate(
            transaction_count=Count('transactions'),
            total_spend=Sum('transactions__amount')
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.profile.organization)
        log_action(
            user=self.request.user,
            action='create',
            resource='supplier',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_update(self, serializer):
        # Verify object belongs to user's organization
        check_object_organization(serializer.instance, self.request.user)
        serializer.save()
        log_action(
            user=self.request.user,
            action='update',
            resource='supplier',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_destroy(self, instance):
        # Verify object belongs to user's organization
        check_object_organization(instance, self.request.user)
        log_action(
            user=self.request.user,
            action='delete',
            resource='supplier',
            resource_id=str(instance.id),
            request=self.request
        )
        instance.delete()


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadAPIThrottle]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        # Only show categories from user's organization
        if not hasattr(self.request.user, 'profile'):
            return Category.objects.none()

        queryset = Category.objects.filter(
            organization=self.request.user.profile.organization
        )

        # Annotate with transaction count and total spend
        queryset = queryset.annotate(
            transaction_count=Count('transactions'),
            total_spend=Sum('transactions__amount')
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.profile.organization)
        log_action(
            user=self.request.user,
            action='create',
            resource='category',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_update(self, serializer):
        # Verify object belongs to user's organization
        check_object_organization(serializer.instance, self.request.user)
        serializer.save()
        log_action(
            user=self.request.user,
            action='update',
            resource='category',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_destroy(self, instance):
        # Verify object belongs to user's organization
        check_object_organization(instance, self.request.user)
        log_action(
            user=self.request.user,
            action='delete',
            resource='category',
            resource_id=str(instance.id),
            request=self.request
        )
        instance.delete()


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Transaction CRUD
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadAPIThrottle]
    filterset_fields = ['supplier', 'category', 'fiscal_year', 'date']
    search_fields = ['description', 'invoice_number']
    ordering_fields = ['date', 'amount', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer

    def get_queryset(self):
        # Only show transactions from user's organization
        if not hasattr(self.request.user, 'profile'):
            return Transaction.objects.none()

        queryset = Transaction.objects.filter(
            organization=self.request.user.profile.organization
        ).select_related('supplier', 'category', 'uploaded_by')

        return queryset

    def perform_create(self, serializer):
        serializer.save()
        log_action(
            user=self.request.user,
            action='create',
            resource='transaction',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_update(self, serializer):
        # Verify object belongs to user's organization
        check_object_organization(serializer.instance, self.request.user)
        serializer.save()
        log_action(
            user=self.request.user,
            action='update',
            resource='transaction',
            resource_id=str(serializer.instance.id),
            request=self.request
        )

    def perform_destroy(self, instance):
        # Verify object belongs to user's organization
        check_object_organization(instance, self.request.user)
        log_action(
            user=self.request.user,
            action='delete',
            resource='transaction',
            resource_id=str(instance.id),
            request=self.request
        )
        instance.delete()
    
    @action(detail=False, methods=['post'], permission_classes=[CanUploadData], throttle_classes=[UploadThrottle])
    def upload_csv(self, request):
        """
        Upload CSV file with procurement data.
        Rate limited to 10 uploads per hour per user.
        """
        serializer = CSVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            processor = CSVProcessor(
                organization=request.user.profile.organization,
                user=request.user,
                file=serializer.validated_data['file'],
                skip_duplicates=serializer.validated_data['skip_duplicates']
            )
            
            upload = processor.process()
            
            log_action(
                user=request.user,
                action='upload',
                resource='transactions',
                resource_id=upload.batch_id,
                details={
                    'file_name': upload.file_name,
                    'successful': upload.successful_rows,
                    'failed': upload.failed_rows
                },
                request=request
            )
            
            return Response(
                DataUploadSerializer(upload).data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[CanDeleteData], throttle_classes=[BulkDeleteThrottle])
    def bulk_delete(self, request):
        """
        Bulk delete transactions.
        Rate limited to 10 bulk deletes per hour per user.
        """
        serializer = TransactionBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        count, _ = bulk_delete_transactions(
            organization=request.user.profile.organization,
            transaction_ids=serializer.validated_data['ids']
        )
        
        log_action(
            user=request.user,
            action='delete',
            resource='transactions',
            details={'count': count},
            request=request
        )
        
        return Response({
            'message': f'{count} transactions deleted successfully',
            'count': count
        })
    
    @action(detail=False, methods=['get'], throttle_classes=[ExportThrottle])
    def export(self, request):
        """
        Export transactions to CSV.
        Rate limited to 30 exports per hour per user.
        """
        filters = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
            'supplier': request.query_params.get('supplier'),
            'category': request.query_params.get('category'),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        df = export_transactions_to_csv(
            organization=request.user.profile.organization,
            filters=filters
        )
        
        # Convert to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        df.to_csv(response, index=False)
        
        log_action(
            user=request.user,
            action='export',
            resource='transactions',
            details={'count': len(df)},
            request=request
        )
        
        return response


class DataUploadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing upload history
    """
    serializer_class = DataUploadSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadAPIThrottle]
    ordering_fields = ['created_at']

    def get_queryset(self):
        # Only show uploads from user's organization
        if not hasattr(self.request.user, 'profile'):
            return DataUpload.objects.none()

        return DataUpload.objects.filter(
            organization=self.request.user.profile.organization
        )
