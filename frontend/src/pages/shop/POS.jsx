import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useCart } from '@/store/cart';
import { useList, useCreateSale, useSalePreview, useQueueReceipt, useProductLookup } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { api, extractError } from '@/api/client';
import { formatKes } from '@/utils/money';
import ProductGrid from '@/components/pos/ProductGrid';
import CartPanel from '@/components/pos/CartPanel';
import PaymentModal from '@/components/pos/PaymentModal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Filter from '@/components/ui/Filter';

export default function POS() {
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const cart = useCart();
  const createSale = useCreateSale();
  const queueReceipt = useQueueReceipt();
  const preview = useSalePreview();
  const lookup = useProductLookup();
  const [search, setSearch] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [showPayment, setShowPayment] = useState(false);
  const [error, setError] = useState('');

  // Load customers, categories, and locations on mount
  const { data: customersData } = useList('customers', endpoints.customers.list, { page_size: 200 });
  const { data: locationsData } = useList('locations', endpoints.inventory.locations);
  const { data: categoriesData } = useList('categories', endpoints.inventory.categories, { page_size: 200 });
  const { data: walkInCustomer } = useQuery({
    queryKey: ['walk-in-customer'],
    queryFn: async () => (await api.get(endpoints.customers.walkIn)).data,
  });

  const customerOptions = customersData?.results || customersData || [];
  const categoryOptions = categoriesData?.results || categoriesData || [];
  const locationOptions = locationsData?.results || locationsData || [];

  // Auto-select shop location after queries settle.
  useEffect(() => {
    if (!cart.locationId && locationOptions.length && cart.channel === 'SHOP') {
      const shop = locationOptions.find((location) => location.location_type === 'SHOP');
      if (shop) cart.setLocation(shop.id);
    }
  }, [cart.locationId, cart.channel, locationOptions.length]);

  const handleBarcodeScan = async (e) => {
    if (e.key !== 'Enter') return;
    const value = e.target.value.trim();
    if (!value) return;
    try {
      const product = await lookup.mutateAsync(
        value.length > 8
          ? { barcode: value }
          : { part_number: value }
      );
      cart.addItem(product, 1);
      e.target.value = '';
    } catch {
      setError(`No product found for "${value}"`);
    }
  };

  const handleCheckout = async () => {
    setError('');
    if (!cart.customerId) {
      setError('Select a customer first.');
      return;
    }
    if (!cart.locationId) {
      setError('Select a till/location first.');
      return;
    }
    setShowPayment(true);
  };

  const handlePaymentConfirm = async (payment) => {
    setError('');
    try {
      const payload = {
        channel: 'SHOP',
        sale_type: 'STANDARD',
        customer: cart.customerId,
        location: cart.locationId,
        items: cart.items.map((i) => ({
          product: i.product.id,
          quantity: i.quantity,
          unit_price: i.unitPrice,
        })),
        amount_paid: payment.amount,
        payment_method: payment.method,
        payment_reference: payment.reference,
        confirm: true,
      };
      const sale = await createSale.mutateAsync(payload);
      setShowPayment(false);

      // Queue the receipt
      try {
        const job = await queueReceipt.mutateAsync(sale.id);
        // Give the queue ~1s, then navigate
        setTimeout(() => navigate(`/sales/${sale.id}?receiptJob=${job.id}`), 500);
      } catch {
        navigate(`/sales/${sale.id}`);
      }
      cart.clear();
    } catch (err) {
      setError(extractError(err, 'Sale failed.'));
    }
  };

  useEffect(() => {
    if (routeLocation.state?.openPayment && cart.customerId && cart.locationId) {
      setShowPayment(true);
      navigate('/pos', { replace: true, state: null });
    }
  }, [routeLocation.state, cart.customerId, cart.locationId, navigate]);

  const cartTotal = cart.subtotal();
  const activeProductFilterCount = [search, categoryId].filter(Boolean).length;

  return (
    <div className="flex min-h-0 flex-col gap-3 pb-20 md:h-[calc(100dvh-7rem)] md:pb-0 lg:flex-row lg:gap-2">
      <div className="flex-1 flex flex-col min-h-0">
        <Filter
          title="Product filters"
          defaultExpanded
          className="mb-3 md:mb-4"
          activeCount={activeProductFilterCount}
          onClear={() => { setSearch(''); setCategoryId(''); }}
          showClear
        >
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1.1fr)_minmax(12rem,0.6fr)]">
              <Input
                label="Barcode / Part Lookup"
                placeholder="Scan barcode or enter SKU / part number"
                onKeyDown={handleBarcodeScan}
                autoFocus
              />
              <Input
                label="Search Product"
                placeholder="Name or part number"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <Select
                label="Category"
                value={categoryId}
                onChange={(value) => setCategoryId(value)}
                className="col-span-2 w-full lg:col-span-1"
                searchable
                options={[
                  { value: '', label: 'All categories' },
                  ...categoryOptions.map((category) => ({
                    value: category.id,
                    label: category.name,
                  })),
                ]}
              />
            </div>
            <div className="grid grid-cols-1 gap-2 md:gap-3 lg:grid-cols-2">
              <Select
                searchable
                label="Customer"
                value={cart.customerId || ''}
                onChange={(value) => cart.setCustomer(value ? Number(value) : null)}
                options={[
                  { value: '', label: 'Select customer...' },
                  ...(walkInCustomer ? [{
                    value: walkInCustomer.id,
                    label: walkInCustomer.name,
                    sublabel: walkInCustomer.code,
                  }] : []),
                  ...customerOptions
                    .filter((customer) => customer.customer_type !== 'WALK_IN' && customer.id !== walkInCustomer?.id)
                    .map((customer) => ({
                      value: customer.id,
                      label: customer.name,
                      sublabel: customer.code,
                    })),
                ]}
              />
              <Select
                label="Till / Location"
                value={cart.locationId || ''}
                onChange={(e) => cart.setLocation(Number(e.target.value))}
              >
                <option value="">Select location...</option>
                {locationOptions
                  .filter((l) => l.location_type === 'SHOP' || l.location_type === 'WAREHOUSE')
                  .map((l) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
              </Select>
            </div>
          </div>
        </Filter>

        {error && (
          <div className="mb-3 rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">
            {error}
          </div>
        )}

        <div className="md:flex-1 md:min-h-0 md:overflow-y-auto">
          <ProductGrid
            onAdd={(p) => cart.addItem(p, 1)}
            search={search}
            categoryId={categoryId}
          />
        </div>
      </div>

      <div className="hidden w-96 flex-shrink-0 md:h-auto lg:flex lg:h-full lg:flex-col">
        <CartPanel onCheckout={handleCheckout} disabled={createSale.isPending} />
      </div>

      <PaymentModal
        open={showPayment}
        onClose={() => setShowPayment(false)}
        total={cartTotal * 1.16} // approximate; server recomputes with real tax
        customerId={cart.customerId}
        onConfirm={handlePaymentConfirm}
      />
    </div>
  );
}
