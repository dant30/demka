import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useList, useCreate, useUpdate } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { api } from '@/api/client';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import TextareaField from '@/components/ui/TextareaField';
import PageHeader from '@/components/ui/PageHeader';

export default function ProductForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;

  const { data: categories } = useList('categories', endpoints.inventory.categories);
  const { data: existing } = useQuery({
    queryKey: ['product-edit', id],
    queryFn: async () => (await api.get(endpoints.inventory.productDetail(id))).data,
    enabled: isEdit,
  });

  const [form, setForm] = useState({
    sku: '', part_number: '', name: '', description: '', category: '', product_type: 'AUTO_PART',
    brand: '', unit: 'PIECE', cost_price: 0, retail_price: 0, wholesale_price: 0,
    is_stocked: true, reorder_level: 0, reorder_qty: 0, is_active: true,
    compatibility_notes: '', etims_item_cls_cd: '',
  });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  useEffect(() => {
    if (existing) setForm({ ...form, ...existing });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [existing]);

  useEffect(() => {
    if (!imageFile) {
      setImagePreview('');
      return undefined;
    }
    const previewUrl = URL.createObjectURL(imageFile);
    setImagePreview(previewUrl);
    return () => URL.revokeObjectURL(previewUrl);
  }, [imageFile]);

  const create = useCreate('products', endpoints.inventory.products, {
    onSuccess: (data) => navigate(`/inventory/products/${data.id}`),
  });
  const update = useUpdate('products', endpoints.inventory.productDetail, {
    onSuccess: () => navigate(`/inventory/products/${id}`),
  });

  const submit = async (e) => {
    e.preventDefault();
    const payload = { ...form };
    delete payload.image;
    let requestData = payload;
    if (imageFile) {
      requestData = new FormData();
      Object.entries(payload).forEach(([key, value]) => {
        requestData.append(key, value == null ? '' : String(value));
      });
      requestData.append('image', imageFile);
    }
    if (isEdit) await update.mutateAsync({ id, payload: requestData });
    else await create.mutateAsync(requestData);
  };

  const setField = (k, v) => setForm({ ...form, [k]: v });
  const cats = categories?.results || categories || [];

  return (
    <form onSubmit={submit} className="page-form">
      <PageHeader
        title={`${isEdit ? 'Edit' : 'New'} Product`}
        description="Manage product identity, pricing, and stock controls."
      />

      <FormSection title="Product identity" description="Catalog details and selling unit">
        <Input label="SKU" value={form.sku} onChange={(e) => setField('sku', e.target.value)} required />
        <Input label="Part Number" value={form.part_number || ''} onChange={(e) => setField('part_number', e.target.value)} hint="Manufacturer or supplier part number" />
        <Input label="Barcode" value={form.barcode || ''} onChange={(e) => setField('barcode', e.target.value)} />
        <Input label="Name" value={form.name} onChange={(e) => setField('name', e.target.value)} required className="md:col-span-2" />
        <Select
          label="Category"
          value={form.category}
          onChange={(value) => setField('category', value)}
          options={[
            { value: '', label: 'Select...' },
            ...cats.map((category) => ({ value: category.id, label: category.name })),
          ]}
          searchable
          required
        />
        <Select label="Type" value={form.product_type} onChange={(e) => setField('product_type', e.target.value)}>
          <option value="MOTORBIKE_PART">Motorbike Part</option>
          <option value="AUTO_PART">Auto Part</option>
          <option value="ACCESSORY">Accessory</option>
        </Select>
        <Input label="Brand" value={form.brand} onChange={(e) => setField('brand', e.target.value)} />
        <div className="md:col-span-2">
          <label className="label" htmlFor="product-image">Product Image</label>
          <div className="flex flex-wrap items-center gap-4">
            {(imagePreview || existing?.image) ? (
              <img
                src={imagePreview || existing.image}
                alt={`${form.name || 'Product'} preview`}
                className="h-24 w-24 rounded-md border border-slate-200 object-cover"
              />
            ) : (
              <div className="flex h-24 w-24 items-center justify-center rounded-md border border-dashed border-slate-300 text-xs text-slate-400">
                No image
              </div>
            )}
            <div>
              <input
                id="product-image"
                type="file"
                accept="image/*"
                className="input max-w-sm"
                onChange={(event) => setImageFile(event.target.files?.[0] || null)}
              />
              <p className="field-hint">Select an image to upload or replace the current one.</p>
            </div>
          </div>
        </div>
        <Select label="Unit" value={form.unit} onChange={(e) => setField('unit', e.target.value)}>
          <option value="PIECE">Piece</option>
          <option value="SET">Set</option>
          <option value="PAIR">Pair</option>
          <option value="LITRE">Litre</option>
        </Select>
      </FormSection>

      <FormSection title="Pricing" description="Set cost and customer-facing prices" columns={3}>
        <Input label="Cost Price" type="number" step="0.01" value={form.cost_price} onChange={(e) => setField('cost_price', e.target.value)} />
        <Input label="Retail Price" type="number" step="0.01" value={form.retail_price} onChange={(e) => setField('retail_price', e.target.value)} />
        <Input label="Wholesale Price" type="number" step="0.01" value={form.wholesale_price} onChange={(e) => setField('wholesale_price', e.target.value)} />
      </FormSection>

      <FormSection title="Stock controls" description="Reorder thresholds and tax classification">
        <Input label="Reorder Level" type="number" value={form.reorder_level} onChange={(e) => setField('reorder_level', e.target.value)} />
        <Input label="Reorder Qty" type="number" value={form.reorder_qty} onChange={(e) => setField('reorder_qty', e.target.value)} />
        <Input label="eTIMS Classification Code" value={form.etims_item_cls_cd} onChange={(e) => setField('etims_item_cls_cd', e.target.value)} className="md:col-span-2" hint="Required for KRA submission" />
      </FormSection>

      <FormSection title="Product notes" columns={2}>
        <TextareaField label="Description" rows={3} value={form.description} onChange={(e) => setField('description', e.target.value)} />
        <TextareaField label="Compatibility Notes" rows={3} value={form.compatibility_notes} onChange={(e) => setField('compatibility_notes', e.target.value)} />
      </FormSection>

      <FormActions>
        <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={create.isPending || update.isPending}>
          {isEdit ? 'Save Changes' : 'Create Product'}
        </Button>
      </FormActions>
    </form>
  );
}