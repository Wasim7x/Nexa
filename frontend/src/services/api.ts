const API_BASE = '/api';

export class ApiClient {
  private static merchantId: string = 'grocery-store';

  public static setMerchantId(id: string) {
    this.merchantId = id;
    localStorage.setItem('vera_active_merchant', id);
  }

  public static getMerchantId(): string {
    return localStorage.getItem('vera_active_merchant') || this.merchantId;
  }

  private static getHeaders(extra: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      'X-Merchant-ID': this.getMerchantId(),
      ...extra
    };
    return headers;
  }

  public static async getMerchants() {
    const res = await fetch(`${API_BASE}/merchants`);
    return res.json();
  }

  public static async getDashboardStats() {
    const res = await fetch(`${API_BASE}/dashboard/stats`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async getCatalogItems() {
    const res = await fetch(`${API_BASE}/catalog/items`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async createCatalogItem(data: any) {
    const res = await fetch(`${API_BASE}/catalog/items`, {
      method: 'POST',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data)
    });
    return res.json();
  }

  public static async updateStock(itemId: string, stockQuantity: number) {
    const res = await fetch(`${API_BASE}/catalog/items/${itemId}/stock`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ stock_quantity: stockQuantity })
    });
    return res.json();
  }

  public static async getCustomers(search?: string, optedIn?: boolean) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (optedIn !== undefined) params.append('opted_in', String(optedIn));

    const res = await fetch(`${API_BASE}/customers?${params.toString()}`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static getCustomerExportUrl(): string {
    return `${API_BASE}/customers/export/csv`;
  }

  public static async getOperations(statusFilter?: string) {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);

    const res = await fetch(`${API_BASE}/operations/records?${params.toString()}`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async updateOperationStatus(reference: string, newStatus: string, reason?: string) {
    const res = await fetch(`${API_BASE}/operations/records/${reference}/status`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ status: newStatus, reason })
    });
    return res.json();
  }

  public static async getKnowledgeDocs(docType?: string) {
    const params = new URLSearchParams();
    if (docType) params.append('doc_type', docType);

    const res = await fetch(`${API_BASE}/knowledge/documents?${params.toString()}`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async createFAQ(title: string, content: string, docType: string = 'faq') {
    const res = await fetch(`${API_BASE}/knowledge/faq`, {
      method: 'POST',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title, content, doc_type: docType })
    });
    return res.json();
  }

  public static async uploadDocument(file: File, title?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);

    const res = await fetch(`${API_BASE}/knowledge/upload`, {
      method: 'POST',
      headers: {
        'X-Merchant-ID': this.getMerchantId()
      },
      body: formData
    });
    return res.json();
  }

  public static async togglePublishDoc(docId: string, isPublished: boolean) {
    const res = await fetch(`${API_BASE}/knowledge/documents/${docId}/publish`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ is_published: isPublished })
    });
    return res.json();
  }

  public static async deleteDoc(docId: string) {
    const res = await fetch(`${API_BASE}/knowledge/documents/${docId}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async getEscalations(statusFilter?: string) {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);

    const res = await fetch(`${API_BASE}/escalations?${params.toString()}`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async resolveEscalation(escalationId: string, resolutionNotes: string) {
    const res = await fetch(`${API_BASE}/escalations/${escalationId}/resolve`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ resolution_notes: resolutionNotes })
    });
    return res.json();
  }

  public static async getOffers() {
    const res = await fetch(`${API_BASE}/offers`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async createOffer(title: string, details: string, scheduleBroadcast: boolean = false) {
    const res = await fetch(`${API_BASE}/offers`, {
      method: 'POST',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title, details, schedule_broadcast: scheduleBroadcast })
    });
    return res.json();
  }

  public static async previewOffer(title: string, details: string) {
    const res = await fetch(`${API_BASE}/offers/preview`, {
      method: 'POST',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title, details })
    });
    return res.json();
  }

  public static async getSettings() {
    const res = await fetch(`${API_BASE}/settings`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async updateGeneralSettings(data: any) {
    const res = await fetch(`${API_BASE}/settings/general`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data)
    });
    return res.json();
  }

  public static async updateAISettings(data: any) {
    const res = await fetch(`${API_BASE}/settings/ai`, {
      method: 'PUT',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data)
    });
    return res.json();
  }

  public static async testAIConnection(aiProvider: string, aiModel?: string, apiKey?: string) {
    const res = await fetch(`${API_BASE}/settings/ai/test-connection`, {
      method: 'POST',
      headers: this.getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        ai_provider: aiProvider,
        ai_model: aiModel,
        api_key: apiKey
      })
    });
    return res.json();
  }

  public static async getAuditLogs() {
    const res = await fetch(`${API_BASE}/settings/audit-logs`, {
      headers: this.getHeaders()
    });
    return res.json();
  }

  public static async simulateWhatsApp(senderPhone: string, messageText: string, referralSlug?: string) {
    const res = await fetch(`${API_BASE}/whatsapp/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender_phone: senderPhone,
        message_text: messageText,
        referral_merchant_slug: referralSlug
      })
    });
    return res.json();
  }
}
