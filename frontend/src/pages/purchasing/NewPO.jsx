import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import DatePicker from '@/components/ui/DatePicker';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import TextareaField from '@/components/ui/TextareaField';

export default function NewPO() {
  const navigate = useNavigate();
  const { data: suppliers } = useList('suppliers', endpoints.suppliers.list, { page_size: 200 });
  const { data: products } = useList('products', endpoints.inventory.products, { page_size: 500 });
  const [supplier, setSupplier] = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [taxRate, setTaxRate] = useState('16');
  const [items, setItems] = useState([]);
  const [productToAdd, setProductToAdd] = useState('');

  const create = useAction('pos', () => endpoints.purchasing.pos, {
    onSuccess: (data) => navigate(`/purchasing/pos/${data.id}`),
  });

  const addProduct = (pid) => {
    const p = (products?.results || products || []).find((x) => x.id === Number(pid));
    if (!p || items.find((i) => i.product === p.id)) return;
    setItems([...items, {
      product: p.id, name: p.name, sku: p.sku,
      quantity_ordered: 1, unit_cost: p.cost_price || 0,
    }]);
  };

  const submit = async () => {
    if (!supplier) return alert('Select a supplier.');
    if (!items.length) return alert('Add at least one item.');
    await create.mutateAsync({
      id: null,
      supplier, expected_date: expectedDate || null,
      notes, tax_rate: taxRate, items,
    });
  };

  const subtotal = items.reduce((s, i) => s + Number(i.quantity_ordered) * Number(i.unit_cost), 0);
  const total = subtotal * (1 + Number(taxRate) / 100);

  return (
    <div className="page-form">
      <PageHeader title="New Purchase Order" description="Build an order and confirm delivery details." />

      <FormSection title="Order details" description="Choose a supplier and set delivery and tax details" columns={3}>
        <Select
          label="Supplier"
          value={supplier}
          onChange={setSupplier}
          options={[
            { value: '', label: 'Select supplier...' },
            ...(suppliers?.results || suppliers || []).map((item) => ({ value: item.id, label: item.name })),
          ]}
          searchable
          required
        />
        <DatePicker label="Expected Date" value={expectedDate} onChange={setExpectedDate} />
        <Input label="Tax Rate %" type="number" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} />
      </FormSection>

      <FormSection title="Items" description="Add products and confirm quantities and unit costs" columns={1}>
        <Select
          label="Add Product"
          value={productToAdd}
          onChange={(value) => { addProduct(value); setProductToAdd(''); }}
          options={[
            { value: '', label: 'Select product...' },
            ...(products?.results || products || []).map((product) => ({
              value: product.id,
              label: product.name,
              sublabel: product.sku,
            })),
          ]}
          searchable
        />

        <div className="mt-4 overflow-x-auto overscroll-x-contain">
        <table className="table min-w-[38rem]">
          <thead><tr><th>Product</th><th>Qty</th><th>Unit Cost</th><th className="text-right">Line</th><th></th></tr></thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={it.product}>
                <td>{it.name} <span className="text-xs text-slate-500">{it.sku}</span></td>
                <td>
                  <input type="number" min="1" className="input w-20" value={it.quantity_ordered}
                    onChange={(e) => {
                      const c = [...items]; c[idx].quantity_ordered = e.target.value; setItems(c);
                    }} />
                </td>
                <td>
                  <input type="number" step="0.01" className="input w-28" value={it.unit_cost}
                    onChange={(e) => {
                      const c = [...items]; c[idx].unit_cost = e.target.value; setItems(c);
                    }} />
                </td>
                <td className="text-right">{formatKes(Number(it.quantity_ordered) * Number(it.unit_cost))}</td>
                <td><button className="text-red-600" onClick={() => setItems(items.filter((_, i) => i !== idx))}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </FormSection>

      <FormSection title="Notes and total" columns={1}>
        <TextareaField label="Notes" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        <div className="flex justify-between items-center mt-4 text-lg font-semibold">
          <span>Total (incl. tax)</span>
          <span>{formatKes(total)}</span>
        </div>
      </FormSection>

      <FormActions>
        <Button variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
        <Button onClick={submit} loading={create.isPending}>Create PO</Button>
      </FormActions>
    </div>
  );
}