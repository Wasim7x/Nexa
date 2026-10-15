import React, { useState, useEffect } from 'react';
import { ApiClient } from './services/api';
import { Merchant } from './types';
import { Navbar } from './components/Navbar';
import { Sidebar, PageId } from './components/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { ProductsPage } from './pages/ProductsPage';
import { CustomersPage } from './pages/CustomersPage';
import { OperationsPage } from './pages/OperationsPage';
import { EscalationsPage } from './pages/EscalationsPage';
import { OffersPage } from './pages/OffersPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SimulatorPage } from './pages/SimulatorPage';

export const App: React.FC = () => {
  const [activeMerchant, setActiveMerchant] = useState<Merchant | null>(null);
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [pendingEscalations, setPendingEscalations] = useState(0);

  useEffect(() => {
    ApiClient.getMerchants().then((merchants) => {
      if (Array.isArray(merchants) && merchants.length > 0) {
        const savedId = ApiClient.getMerchantId();
        const found = merchants.find((m: Merchant) => m.id === savedId) || merchants[0];
        setActiveMerchant(found);
        ApiClient.setMerchantId(found.id);
      }
    });
  }, []);

  useEffect(() => {
    if (activeMerchant) {
      ApiClient.getDashboardStats().then((data) => {
        if (data?.pending_escalations !== undefined) {
          setPendingEscalations(data.pending_escalations);
        }
      });
    }
  }, [activeMerchant]);

  const handleSelectMerchant = (merchant: Merchant) => {
    setActiveMerchant(merchant);
    ApiClient.setMerchantId(merchant.id);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <OverviewPage activeMerchant={activeMerchant} onNavigate={setCurrentPage} />;
      case 'knowledge':
        return <KnowledgePage activeMerchant={activeMerchant} />;
      case 'products':
        return <ProductsPage activeMerchant={activeMerchant} />;
      case 'customers':
        return <CustomersPage activeMerchant={activeMerchant} />;
      case 'operations':
        return <OperationsPage activeMerchant={activeMerchant} />;
      case 'escalations':
        return <EscalationsPage activeMerchant={activeMerchant} />;
      case 'offers':
        return <OffersPage activeMerchant={activeMerchant} />;
      case 'integrations':
        return <IntegrationsPage activeMerchant={activeMerchant} />;
      case 'settings':
        return <SettingsPage activeMerchant={activeMerchant} />;
      case 'simulator':
        return <SimulatorPage />;
      default:
        return <OverviewPage activeMerchant={activeMerchant} onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        activeMerchant={activeMerchant}
        onSelectMerchant={handleSelectMerchant}
        onOpenSimulator={() => setCurrentPage('simulator')}
      />

      <div className="flex flex-1">
        <Sidebar
          currentPage={currentPage}
          onSelectPage={setCurrentPage}
          pendingEscalationsCount={pendingEscalations}
        />

        <main className="flex-1 overflow-x-hidden min-h-[calc(100vh-4rem)]">
          {renderPage()}
        </main>
      </div>
    </div>
  );
};
