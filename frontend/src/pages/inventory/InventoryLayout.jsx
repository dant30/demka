import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import Tabs from '@/components/ui/Tabs';
import PageHeader from '@/components/ui/PageHeader';

const pageDetails = {
  products: {
    title: 'Inventory',
    description: 'Browse products, stock levels, and reorder needs.',
  },
  transfers: {
    title: 'Transfers',
    description: 'Move stock between locations and track transfer status.',
  },
  import: {
    title: 'Import Products',
    description: 'Import and update product inventory from a CSV file.',
  },
  categories: {
    title: 'Categories',
    description: 'Organize products into categories for easier browsing.',
  },
  locations: {
    title: 'Locations',
    description: 'Manage stock locations and their inventory settings.',
  },
};

export default function InventoryLayout() {
  const { isBoss } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [createRequest, setCreateRequest] = useState(0);
  const routeTab = location.pathname.split('/')[2] || 'products';
  const selectedTab = ['import', 'transfers', 'categories', 'locations'].includes(routeTab)
    ? routeTab
    : 'products';
  const tabs = [
    { value: 'products', label: 'Products' },
    { value: 'transfers', label: 'Transfers' },
    ...(isBoss ? [
      { value: 'import', label: 'Import' },
      { value: 'categories', label: 'Categories' },
      { value: 'locations', label: 'Locations' },
    ] : []),
  ];
  const page = pageDetails[selectedTab];

  const action = {
    products: <Link to="/inventory/products/new" className="btn-primary">+ Product</Link>,
    transfers: <button type="button" className="btn-primary" onClick={() => setCreateRequest((request) => request + 1)}>+ New Transfer</button>,
    categories: isBoss
      ? <button type="button" className="btn-primary" onClick={() => setCreateRequest((request) => request + 1)}>+ New Category</button>
      : undefined,
    locations: isBoss
      ? <button type="button" className="btn-primary" onClick={() => setCreateRequest((request) => request + 1)}>+ New Location</button>
      : undefined,
  }[selectedTab];

  return (
    <div className="space-y-4">
      <PageHeader
        title={page.title}
        description={page.description}
        actions={action}
      />
      <Tabs
        tabs={tabs}
        value={selectedTab}
        onChange={(value) => navigate(value === 'products' ? '/inventory' : `/inventory/${value}`)}
        tabListClassName="bg-white"
      >
        <Outlet context={{ createRequest }} />
      </Tabs>
    </div>
  );
}