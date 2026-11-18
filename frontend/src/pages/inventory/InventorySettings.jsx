import { useState } from 'react';
import { endpoints } from '@/api/endpoints';
import { useCreate, useList, useUpdate } from '@/api/queries';
import Button from '@/components/ui/Button';
import DataTable from '@/components/ui/DataTable';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';

export function InventoryCategories() {
  const { data, isLoading } = useList('categories', endpoints.inventory.categories, { page_size: 200 });
  const [editing, setEditing] = useState(null);
  const categories = data?.results || data || [];
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'applies_to', label: 'Applies to' },
    { key: 'product_count', label: 'Products', align: 'right' },
    {
      key: 'actions',
      label: 'Actions',
      align: 'right',
      render: (category) => (
        <button type="button" className="text-brand-600 text-xs hover:underline" onClick={() => setEditing(category)}>
          Edit
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Product Categories"
        description="Organize products and control which product types each category applies to."
        actions={<Button onClick={() => setEditing(false)}>+ New Category</Button>}
      />
      <DataTable columns={columns} rows={categories} loading={isLoading} empty="No categories found." caption="Categories" />
      {editing !== null && (
        <CategoryEditor
          key={editing?.id ?? 'new'}
          category={editing || null}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}

function CategoryEditor({ category, onClose }) {
  const [name, setName] = useState(category?.name ?? '');
  const [appliesTo, setAppliesTo] = useState(category?.applies_to ?? 'BOTH');
  const create = useCreate('categories', endpoints.inventory.categories, {
    invalidate: ['categories'],
    onSuccess: onClose,
  });
  const update = useUpdate('categories', endpoints.inventory.categoryDetail, {
    invalidate: ['categories'],
    onSuccess: onClose,
  });
  const saving = create.isPending || update.isPending;

  const submit = async () => {
    const payload = { name: name.trim(), applies_to: appliesTo };
    try {
      if (category) await update.mutateAsync({ id: category.id, payload });
      else await create.mutateAsync(payload);
    } catch {
      // The shared mutation hooks report request errors through Toast.
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={`${category ? 'Edit' : 'New'} Category`}
      size="sm"
      footer={(
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} loading={saving} disabled={!name.trim()}>
            {category ? 'Save Changes' : 'Create Category'}
          </Button>
        </>
      )}
    >
      <div className="space-y-4">
        <Input label="Category Name" value={name} onChange={(event) => setName(event.target.value)} required />
        <Select
          label="Applies To"
          value={appliesTo}
          onChange={setAppliesTo}
          options={[
            { value: 'BOTH', label: 'Both' },
            { value: 'AUTO', label: 'Auto' },
            { value: 'MOTORBIKE', label: 'Motorbike' },
          ]}
        />
      </div>
    </Modal>
  );
}

export function InventoryLocations() {
  const { data, isLoading } = useList('locations', endpoints.inventory.locations, { page_size: 200 });
  const [editing, setEditing] = useState(null);
  const locations = data?.results || data || [];
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'location_type_display', label: 'Type' },
    { key: 'assigned_agent_display', label: 'Assigned agent' },
    {
      key: 'is_active',
      label: 'Status',
      render: (location) => location.is_active ? 'Active' : 'Inactive',
    },
    {
      key: 'actions',
      label: 'Actions',
      align: 'right',
      render: (location) => (
        <button type="button" className="text-brand-600 text-xs hover:underline" onClick={() => setEditing(location)}>
          Edit
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Stock Locations"
        description="Manage shops, warehouses, and field locations used for stock control."
        actions={<Button onClick={() => setEditing(false)}>+ New Location</Button>}
      />
      <DataTable columns={columns} rows={locations} loading={isLoading} empty="No locations found." caption="Locations" />
      {editing !== null && (
        <LocationEditor
          key={editing?.id ?? 'new'}
          location={editing || null}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}

function LocationEditor({ location, onClose }) {
  const [name, setName] = useState(location?.name ?? '');
  const [locationType, setLocationType] = useState(location?.location_type ?? 'SHOP');
  const [isActive, setIsActive] = useState(location?.is_active ?? true);
  const create = useCreate('locations', endpoints.inventory.locations, {
    invalidate: ['locations'],
    onSuccess: onClose,
  });
  const update = useUpdate('locations', endpoints.inventory.locationDetail, {
    invalidate: ['locations'],
    onSuccess: onClose,
  });
  const saving = create.isPending || update.isPending;

  const submit = async () => {
    const payload = { name: name.trim(), location_type: locationType, is_active: isActive };
    try {
      if (location) await update.mutateAsync({ id: location.id, payload });
      else await create.mutateAsync(payload);
    } catch {
      // The shared mutation hooks report request errors through Toast.
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={`${location ? 'Edit' : 'New'} Location`}
      size="sm"
      footer={(
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} loading={saving} disabled={!name.trim()}>
            {location ? 'Save Changes' : 'Create Location'}
          </Button>
        </>
      )}
    >
      <div className="space-y-4">
        <Input label="Location Name" value={name} onChange={(event) => setName(event.target.value)} required />
        <Select
          label="Location Type"
          value={locationType}
          onChange={setLocationType}
          options={[
            { value: 'SHOP', label: 'Shop' },
            { value: 'WAREHOUSE', label: 'Warehouse' },
            { value: 'FIELD', label: 'Field / Van' },
          ]}
        />
        <Switch label="Active" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
      </div>
    </Modal>
  );
}