from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid
from backend.app.models.shared import (
    Merchant,
    MerchantUser,
    Customer,
    CustomerMerchantProfile,
    Conversation,
    Message,
    KnowledgeDocument,
    MerchantSettings,
    SupportEscalation,
    NotificationJob,
    NotificationEvent,
    AuditLog,
)
from backend.app.models.grocery import (
    GroceryProduct,
    GroceryInventory,
    GroceryOrder,
    GroceryOrderItem,
)
from backend.app.models.sweets import (
    SweetsProduct,
    SweetsInventory,
    SweetsOrder,
    SweetsOrderItem,
)
from backend.app.models.salon import (
    SalonService,
    SalonStaff,
    SalonAvailability,
    SalonAppointment,
)
from backend.app.models.dental import (
    DentalService,
    DentalStaff,
    DentalAvailability,
    DentalAppointment,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "generate_uuid",
    "Merchant",
    "MerchantUser",
    "Customer",
    "CustomerMerchantProfile",
    "Conversation",
    "Message",
    "KnowledgeDocument",
    "MerchantSettings",
    "SupportEscalation",
    "NotificationJob",
    "NotificationEvent",
    "AuditLog",
    "GroceryProduct",
    "GroceryInventory",
    "GroceryOrder",
    "GroceryOrderItem",
    "SweetsProduct",
    "SweetsInventory",
    "SweetsOrder",
    "SweetsOrderItem",
    "SalonService",
    "SalonStaff",
    "SalonAvailability",
    "SalonAppointment",
    "DentalService",
    "DentalStaff",
    "DentalAvailability",
    "DentalAppointment",
]
