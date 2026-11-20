import { Routes, Route } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import StaticErrorRedirect from '@/components/StaticErrorRedirect';
import ProtectedRoute from './ProtectedRoute';
import PortalProtectedRoute from './PortalProtectedRoute';

import Login from '@/pages/auth/Login';
import PasswordReset from '@/pages/auth/PasswordReset';
import Profile from '@/pages/auth/Profile';
import HomeRoute from '@/pages/HomeRoute';
import POS from '@/pages/shop/POS';
import POSCart from '@/pages/shop/POSCart';

// Field
import FieldHome from '@/pages/field/FieldHome';
import FieldStartRun from '@/pages/field/FieldStartRun';
import FieldSale from '@/pages/field/FieldSale';
import FieldCompleteRun from '@/pages/field/FieldCompleteRun';
import FieldSaleReceipt from '@/pages/field/FieldSaleReceipt';

// Sales
import SalesList from '@/pages/sales/SalesList';
import SaleDetail from '@/pages/sales/SaleDetail';
import ReturnsList from '@/pages/sales/ReturnsList';
import SpecialOrdersList from '@/pages/sales/SpecialOrdersList';

// Inventory
import InventoryHome from '@/pages/inventory/InventoryHome';
import ProductDetail from '@/pages/inventory/ProductDetail';
import ProductForm from '@/pages/inventory/ProductForm';
import ImportProducts from '@/pages/inventory/ImportProducts';
import TransfersList from '@/pages/inventory/TransfersList';
import InventoryLayout from '@/pages/inventory/InventoryLayout';
import { InventoryCategories, InventoryLocations } from '@/pages/inventory/InventorySettings';

// Customers
import CustomersList from '@/pages/customers/CustomersList';
import CustomerDetail from '@/pages/customers/CustomerDetail';
import CustomerForm from '@/pages/customers/CustomerForm';

// Suppliers
import SuppliersList from '@/pages/suppliers/SuppliersList';
import SupplierDetail from '@/pages/suppliers/SupplierDetail';
import SupplierForm from '@/pages/suppliers/SupplierForm';

// Purchasing
import PurchaseOrdersList from '@/pages/purchasing/PurchaseOrdersList';
import PODetail from '@/pages/purchasing/PODetail';
import NewPO from '@/pages/purchasing/NewPO';
import ReceiveGoods from '@/pages/purchasing/ReceiveGoods';

// Routes
import RoutesList from '@/pages/routes/RoutesList';
import RouteForm from '@/pages/routes/RouteForm';
import RouteDetail from '@/pages/routes/RouteDetail';
import RouteRunDetail from '@/pages/routes/RouteRunDetail';
import RouteOperations from '@/pages/routes/RouteOperations';

// Payments
import PaymentsList from '@/pages/payments/PaymentsList';
import MpesaReconcile from '@/pages/payments/MpesaReconcile';

// Expenses
import ExpensesList from '@/pages/expenses/ExpensesList';

// Preorders
import PreordersQueue from '@/pages/preorders/PreordersQueue';
import PreorderDetail from '@/pages/preorders/PreorderDetail';

// Reports
import ReportsHome from '@/pages/reports/ReportsHome';
import ProfitLossReport from '@/pages/reports/ProfitLossReport';
import SalesReport from '@/pages/reports/SalesReport';
import CashReport from '@/pages/reports/CashReport';
import VatReport from '@/pages/reports/VatReport';
import StockReport from '@/pages/reports/StockReport';
import CustomerReport from '@/pages/reports/CustomerReport';
import SupplierReport from '@/pages/reports/SupplierReport';
import EtimsReport from '@/pages/reports/EtimsReport';
import RoutePerformanceReport from '@/pages/reports/RoutePerformanceReport';
import ExpenseReport from '@/pages/reports/ExpenseReport';

// Admin
import AdminEtims from '@/pages/admin/AdminEtims';
import AdminPrinters from '@/pages/admin/AdminPrinters';
import AdminUsers from '@/pages/admin/AdminUsers';
import AdminLocations from '@/pages/admin/AdminLocations';
import AdminAuditLogs from '@/pages/admin/AdminAuditLogs';
import AdminBusiness from '@/pages/admin/AdminBusiness';
import PrintJobs from '@/pages/admin/PrintJobs';

// Portal
import PortalLogin from '@/pages/portal/PortalLogin';
import PortalCatalog from '@/pages/portal/PortalCatalog';
import PortalOrders from '@/pages/portal/PortalOrders';
import PortalOrderDetail from '@/pages/portal/PortalOrderDetail';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/password-reset" element={<PasswordReset />} />

      {/* Portal */}
      <Route path="/portal/login" element={<PortalLogin />} />
      <Route path="/portal" element={<PortalProtectedRoute><PortalCatalog /></PortalProtectedRoute>} />
      <Route path="/portal/orders" element={<PortalProtectedRoute><PortalOrders /></PortalProtectedRoute>} />
      <Route path="/portal/orders/:id" element={<PortalProtectedRoute><PortalOrderDetail /></PortalProtectedRoute>} />

      {/* App */}
      <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route path="/" element={<HomeRoute />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/pos" element={<ProtectedRoute shopOnly><POS /></ProtectedRoute>} />
        <Route path="/pos/cart" element={<ProtectedRoute shopOnly><POSCart /></ProtectedRoute>} />

        {/* Field */}
        <Route path="/field" element={<FieldHome />} />
        <Route path="/field/start/:runId" element={<FieldStartRun />} />
        <Route path="/field/sale/:runId" element={<FieldSale />} />
        <Route path="/field/sale-receipt/:saleId" element={<FieldSaleReceipt />} />
        <Route path="/field/complete/:runId" element={<FieldCompleteRun />} />

        {/* Sales */}
        <Route path="/sales" element={<SalesList />} />
        <Route path="/sales/special-orders" element={<SpecialOrdersList />} />
        <Route path="/sales/:id" element={<SaleDetail />} />
        <Route path="/sales/returns" element={<ReturnsList />} />

        {/* Inventory */}
        <Route path="/inventory" element={<InventoryLayout />}>
          <Route index element={<InventoryHome />} />
          <Route path="import" element={<ProtectedRoute bossOnly><ImportProducts /></ProtectedRoute>} />
          <Route path="transfers" element={<TransfersList />} />
          <Route path="categories" element={<ProtectedRoute bossOnly><InventoryCategories /></ProtectedRoute>} />
          <Route path="locations" element={<ProtectedRoute bossOnly><InventoryLocations /></ProtectedRoute>} />
        </Route>
        <Route path="/inventory/products/new" element={<ProductForm />} />
        <Route path="/inventory/products/:id" element={<ProductDetail />} />
        <Route path="/inventory/products/:id/edit" element={<ProductForm />} />

        {/* Customers */}
        <Route path="/customers" element={<CustomersList />} />
        <Route path="/customers/new" element={<CustomerForm />} />
        <Route path="/customers/:id/edit" element={<CustomerForm />} />
        <Route path="/customers/:id" element={<CustomerDetail />} />

        {/* Suppliers */}
        <Route path="/suppliers" element={<SuppliersList />} />
        <Route path="/suppliers/new" element={<SupplierForm />} />
        <Route path="/suppliers/:id/edit" element={<SupplierForm />} />
        <Route path="/suppliers/:id" element={<SupplierDetail />} />

        {/* Purchasing */}
        <Route path="/purchasing" element={<PurchaseOrdersList />} />
        <Route path="/purchasing/pos/new" element={<NewPO />} />
        <Route path="/purchasing/pos/:id" element={<PODetail />} />
        <Route path="/purchasing/receive/:id" element={<ReceiveGoods />} />

        {/* Routes */}
        <Route path="/routes" element={<RoutesList />} />
        <Route path="/routes/operations" element={<ProtectedRoute bossOnly><RouteOperations /></ProtectedRoute>} />
        <Route path="/routes/new" element={<ProtectedRoute bossOnly><RouteForm /></ProtectedRoute>} />
        <Route path="/routes/:id/edit" element={<ProtectedRoute bossOnly><RouteForm /></ProtectedRoute>} />
        <Route path="/routes/:id" element={<RouteDetail />} />
        <Route path="/routes/runs/:id" element={<RouteRunDetail />} />

        {/* Payments */}
        <Route path="/payments" element={<PaymentsList />} />
        <Route path="/payments/mpesa" element={<MpesaReconcile />} />

        {/* Expenses */}
        <Route path="/expenses" element={<ExpensesList />} />

        {/* Preorders */}
        <Route path="/preorders" element={<PreordersQueue />} />
        <Route path="/preorders/:id" element={<PreorderDetail />} />

        {/* Reports */}
        <Route path="/reports" element={<ProtectedRoute bossOnly><ReportsHome /></ProtectedRoute>} />
        <Route path="/reports/profit-loss" element={<ProtectedRoute bossOnly><ProfitLossReport /></ProtectedRoute>} />
        <Route path="/reports/sales" element={<ProtectedRoute bossOnly><SalesReport /></ProtectedRoute>} />
        <Route path="/reports/cash" element={<ProtectedRoute bossOnly><CashReport /></ProtectedRoute>} />
        <Route path="/reports/vat" element={<ProtectedRoute bossOnly><VatReport /></ProtectedRoute>} />
        <Route path="/reports/stock" element={<ProtectedRoute bossOnly><StockReport /></ProtectedRoute>} />
        <Route path="/reports/customers" element={<ProtectedRoute bossOnly><CustomerReport /></ProtectedRoute>} />
        <Route path="/reports/suppliers" element={<ProtectedRoute bossOnly><SupplierReport /></ProtectedRoute>} />
        <Route path="/reports/etims" element={<ProtectedRoute bossOnly><EtimsReport /></ProtectedRoute>} />
        <Route path="/reports/route-performance" element={<ProtectedRoute bossOnly><RoutePerformanceReport /></ProtectedRoute>} />
        <Route path="/reports/expenses" element={<ProtectedRoute bossOnly><ExpenseReport /></ProtectedRoute>} />

        {/* Admin */}
        <Route path="/admin/etims" element={<ProtectedRoute bossOnly><AdminEtims /></ProtectedRoute>} />
        <Route path="/admin/printers" element={<ProtectedRoute bossOnly><AdminPrinters /></ProtectedRoute>} />
        <Route path="/admin/print-jobs" element={<ProtectedRoute bossOnly><PrintJobs /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute bossOnly><AdminUsers /></ProtectedRoute>} />
        <Route path="/admin/locations" element={<ProtectedRoute bossOnly><AdminLocations /></ProtectedRoute>} />
        <Route path="/admin/audit" element={<ProtectedRoute bossOnly><AdminAuditLogs /></ProtectedRoute>} />
        <Route path="/admin/business" element={<ProtectedRoute bossOnly><AdminBusiness /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<StaticErrorRedirect path="/not_found.html" />} />
    </Routes>
  );
}