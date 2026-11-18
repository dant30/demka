import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import ProtectedRoute from './ProtectedRoute';
import PortalProtectedRoute from './PortalProtectedRoute';

import Login from '@/pages/auth/Login';
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

// Admin
import AdminEtims from '@/pages/admin/AdminEtims';
import AdminPrinters from '@/pages/admin/AdminPrinters';
import AdminUsers from '@/pages/admin/AdminUsers';

// Portal
import PortalLogin from '@/pages/portal/PortalLogin';
import PortalCatalog from '@/pages/portal/PortalCatalog';
import PortalOrders from '@/pages/portal/PortalOrders';
import PortalOrderDetail from '@/pages/portal/PortalOrderDetail';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Portal */}
      <Route path="/portal/login" element={<PortalLogin />} />
      <Route path="/portal" element={<PortalProtectedRoute><PortalCatalog /></PortalProtectedRoute>} />
      <Route path="/portal/orders" element={<PortalProtectedRoute><PortalOrders /></PortalProtectedRoute>} />
      <Route path="/portal/orders/:id" element={<PortalProtectedRoute><PortalOrderDetail /></PortalProtectedRoute>} />

      {/* App */}
      <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route path="/" element={<HomeRoute />} />
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
        <Route path="/inventory/transfers" element={<TransfersList />} />

        {/* Customers */}
        <Route path="/customers" element={<CustomersList />} />
        <Route path="/customers/new" element={<CustomerForm />} />
        <Route path="/customers/:id/edit" element={<CustomerForm />} />
        <Route path="/customers/:id" element={<CustomerDetail />} />

        {/* Suppliers */}
        <Route path="/suppliers" element={<SuppliersList />} />
        <Route path="/suppliers/new" element={<SupplierForm />} />
        <Route path="/suppliers/:id" element={<SupplierDetail />} />

        {/* Purchasing */}
        <Route path="/purchasing" element={<PurchaseOrdersList />} />
        <Route path="/purchasing/pos/new" element={<NewPO />} />
        <Route path="/purchasing/pos/:id" element={<PODetail />} />
        <Route path="/purchasing/receive/:id" element={<ReceiveGoods />} />

        {/* Routes */}
        <Route path="/routes" element={<RoutesList />} />
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
        <Route path="/reports" element={<ReportsHome />} />
        <Route path="/reports/profit-loss" element={<ProfitLossReport />} />
        <Route path="/reports/sales" element={<SalesReport />} />
        <Route path="/reports/cash" element={<CashReport />} />
        <Route path="/reports/vat" element={<VatReport />} />
        <Route path="/reports/stock" element={<StockReport />} />
        <Route path="/reports/customers" element={<CustomerReport />} />
        <Route path="/reports/suppliers" element={<SupplierReport />} />
        <Route path="/reports/etims" element={<EtimsReport />} />

        {/* Admin */}
        <Route path="/admin/etims" element={<AdminEtims />} />
        <Route path="/admin/printers" element={<AdminPrinters />} />
        <Route path="/admin/users" element={<AdminUsers />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}