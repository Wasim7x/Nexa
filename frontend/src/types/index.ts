export interface Merchant {
  id: string;
  name: string;
  slug: string;
  business_type: 'grocery' | 'sweets' | 'salon' | 'dental';
  phone_number?: string;
  description?: string;
}

export interface DashboardStats {
  merchant: {
    id: string;
    name: string;
    business_type: string;
  };
  customers_count: number;
  conversations_count: number;
  orders_or_appointments_count: number;
  total_revenue: number;
  pending_escalations: number;
  knowledge_docs_count: number;
  notifications_count: number;
}

export interface CatalogItem {
  id: string;
  name: string;
  category: string;
  price: number;
  unit?: string;
  stock?: number;
  duration_minutes?: number;
  is_sugar_free?: boolean;
  is_active: boolean;
  description?: string;
  type: 'product' | 'sweet' | 'service';
}

export interface Customer {
  customer_id: string;
  whatsapp_phone: string;
  display_name: string;
  opt_in_promotions: boolean;
  interaction_count: number;
  last_interaction?: string;
  notes?: string;
}

export interface OperationRecord {
  id: string;
  reference: string;
  type: 'order' | 'appointment';
  status: string;
  total?: number;
  service_name?: string;
  staff_name?: string;
  dentist_name?: string;
  date?: string;
  time?: string;
  created_at: string;
  delivery_address?: string;
  gift_packaging?: boolean;
  chief_complaint?: string;
  items_count?: number;
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  doc_type: string;
  file_name?: string;
  content: string;
  extracted_text?: string;
  embedding_status: string;
  is_published: boolean;
  created_at: string;
}

export interface EscalationRecord {
  id: string;
  customer_id: string;
  reason: string;
  category: string;
  urgency: string;
  status: string;
  assigned_to?: string;
  resolution_notes?: string;
  created_at: string;
}

export interface Offer {
  id: string;
  title: string;
  details: string;
  is_published: boolean;
  created_at: string;
}

export interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  status: string;
  customer_phone?: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface MerchantSettingsData {
  merchant: Merchant;
  settings: {
    business_hours: string;
    timezone: string;
    notification_phone?: string;
    notification_channel: string;
    escalation_message: string;
    welcome_message: string;
    ai_provider: string;
    ai_model: string;
  };
  whatsapp_integration: {
    status: string;
    mode: string;
    phone_number_id: string;
    webhook_verified: boolean;
  };
}
