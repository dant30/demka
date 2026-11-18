import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import Tabs from '@/components/ui/Tabs';

export default function InventoryLayout() {
  const { isBoss } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
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

  return (
    <Tabs
      tabs={tabs}
      value={selectedTab}
      onChange={(value) => navigate(value === 'products' ? '/inventory' : `/inventory/${value}`)}
      className="space-y-4"
      tabListClassName="bg-white"
    >
      <Outlet />
    </Tabs>
  );
}