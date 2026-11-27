import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/auth/AuthContext';
import { PermissionGate, RequireAuth } from '@/auth/guards';
import { AppShell } from '@/components/shell/AppShell';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ProductsPage } from '@/pages/ProductsPage';
import { ProductDetailPage } from '@/pages/ProductDetailPage';
import { CostsPage } from '@/pages/CostsPage';
import { SuppliersPage } from '@/pages/SuppliersPage';
import { InventoryPage } from '@/pages/InventoryPage';
import { ChannelsPage } from '@/pages/ChannelsPage';
import { CompetitorsPage } from '@/pages/CompetitorsPage';
import { CompetitorPricesPage } from '@/pages/CompetitorPricesPage';
import { CompetitorCollectedPage } from '@/pages/CompetitorCollectedPage';
import { PricingRunPage } from '@/pages/PricingRunPage';
import { PricingJobsPage } from '@/pages/PricingJobsPage';
import { RecommendationsPage } from '@/pages/RecommendationsPage';
import { RecommendationDetailPage } from '@/pages/RecommendationDetailPage';
import { PricingRulesPage } from '@/pages/PricingRulesPage';
import { AutomationRunsPage } from '@/pages/AutomationRunsPage';
import { BiProfitabilityPage } from '@/pages/BiProfitabilityPage';
import { BiCompetitorsPage } from '@/pages/BiCompetitorsPage';
import { BiAutomationPage } from '@/pages/BiAutomationPage';
import { UsersPage } from '@/pages/UsersPage';
import { AuditLogsPage } from '@/pages/AuditLogsPage';
import { ChannelFeesPage } from '@/pages/ChannelFeesPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

export function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<RequireAuth />}>
            <Route element={<AppShell />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route
                path="/dashboard"
                element={
                  <PermissionGate permission="bi.read">
                    <DashboardPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/products"
                element={
                  <PermissionGate permission="product.read">
                    <ProductsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/products/:id"
                element={
                  <PermissionGate permission="product.read">
                    <ProductDetailPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/suppliers"
                element={
                  <PermissionGate permission="product.read">
                    <SuppliersPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/costs"
                element={
                  <PermissionGate permission="product.read">
                    <CostsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/inventory"
                element={
                  <PermissionGate permission="inventory.read">
                    <InventoryPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/channels"
                element={
                  <PermissionGate permission="channel.read">
                    <ChannelsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/competitors"
                element={
                  <PermissionGate permission="competitor.read">
                    <CompetitorsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/competitor-prices"
                element={
                  <PermissionGate permission="competitor.read">
                    <CompetitorPricesPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/competitor-prices/collected"
                element={
                  <PermissionGate permission="competitor.read">
                    <CompetitorCollectedPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/pricing/run"
                element={
                  <PermissionGate permission="pricing.run">
                    <PricingRunPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/pricing/runs"
                element={
                  <PermissionGate permission="pricing.read">
                    <PricingJobsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/pricing/recommendations"
                element={
                  <PermissionGate permission="pricing.read">
                    <RecommendationsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/pricing/recommendations/:id"
                element={
                  <PermissionGate permission="pricing.read">
                    <RecommendationDetailPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/pricing-rules"
                element={
                  <PermissionGate permission="rule.read">
                    <PricingRulesPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/automation/runs"
                element={
                  <PermissionGate permission="execution.read">
                    <AutomationRunsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/bi/profitability"
                element={
                  <PermissionGate permission="bi.read">
                    <BiProfitabilityPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/bi/competitors"
                element={
                  <PermissionGate permission="bi.read">
                    <BiCompetitorsPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/bi/automation"
                element={
                  <PermissionGate permission="bi.read">
                    <BiAutomationPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/settings/users"
                element={
                  <PermissionGate permission="settings.read">
                    <UsersPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/settings/channel-fees"
                element={
                  <PermissionGate permission="settings.read">
                    <ChannelFeesPage />
                  </PermissionGate>
                }
              />
              <Route
                path="/settings/audit-logs"
                element={
                  <PermissionGate permission="audit.read">
                    <AuditLogsPage />
                  </PermissionGate>
                }
              />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}