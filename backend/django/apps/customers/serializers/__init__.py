from .customer import (
    CustomerListSerializer,
    CustomerDetailSerializer,
    CustomerCreateSerializer,
    CustomerUpdateSerializer,
)
from .contact import CustomerContactSerializer
from .route_assignment import (
    CustomerRouteAssignmentSerializer,
    AssignRouteSerializer,
)

__all__ = [
    "CustomerListSerializer",
    "CustomerDetailSerializer",
    "CustomerCreateSerializer",
    "CustomerUpdateSerializer",
    "CustomerContactSerializer",
    "CustomerRouteAssignmentSerializer",
    "AssignRouteSerializer",
]