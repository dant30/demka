import { useCallback, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { downloadProductTemplate, useProductImport } from '@/api/queries';
import { extractError } from '@/api/client';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';

const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm', '.csv'];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function ImportProducts() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const importMutation = useProductImport();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [commit, setCommit] = useState(null);
  const [skipErrors, setSkipErrors] = useState(false);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setCommit(null);
    setSkipErrors(false);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const pickFile = useCallback((selectedFile) => {
    const extension = selectedFile.name.slice(selectedFile.name.lastIndexOf('.')).toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setFile(null);
      setPreview(null);
      setCommit(null);
      setError('Choose an .xlsx, .xlsm, or .csv file. Legacy .xls files are not supported.');
      return;
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setFile(null);
      setPreview(null);
      setCommit(null);
      setError('The selected file exceeds the 10 MB limit.');
      return;
    }
    setFile(selectedFile);
    setPreview(null);
    setCommit(null);
    setSkipErrors(false);
    setError('');
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();
    setDragging(false);
    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) pickFile(droppedFile);
  }, [pickFile]);

  const onPreview = async () => {
    if (!file) return;
    setError('');
    try {
      const result = await importMutation.mutateAsync({ file, mode: 'preview' });
      setPreview(result);
      setCommit(null);
    } catch (err) {
      setError(extractError(err, 'Preview failed.'));
    }
  };

  const onCommit = async () => {
    if (!file) return;
    setError('');
    try {
      const result = await importMutation.mutateAsync({ file, mode: 'commit', skipErrors });
      setCommit(result);
      if (result.created > 0) {
        queryClient.invalidateQueries({ queryKey: ['products'] });
        queryClient.invalidateQueries({ queryKey: ['categories'] });
        queryClient.invalidateQueries({ queryKey: ['reporting-dashboard'] });
      }
    } catch (err) {
      setError(extractError(err, 'Import failed.'));
    }
  };

  const onDownloadTemplate = async () => {
    setError('');
    try {
      await downloadProductTemplate();
    } catch (err) {
      setError(extractError(err, 'Could not download the template.'));
    }
  };

  if (commit && commit.created > 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="card border-green-200 bg-green-50 py-8 text-center">
          <div className="mb-3 text-4xl font-semibold text-green-700" aria-hidden="true">✓</div>
          <h1 className="text-2xl font-bold text-green-900">
            {commit.created} product{commit.created !== 1 ? 's' : ''} imported
          </h1>
          {commit.invalid > 0 && (
            <p className="mt-2 text-sm text-green-800">
              {commit.invalid} row{commit.invalid !== 1 ? 's were' : ' was'} skipped due to errors.
            </p>
          )}
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          <Button onClick={() => navigate('/inventory')}>View Products</Button>
          <Button variant="secondary" onClick={() => navigate('/inventory/products/new')}>
            Add a Product Manually
          </Button>
          <Button variant="ghost" onClick={reset}>Import Another File</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        title="Import Products"
        description="Upload a spreadsheet or CSV, review the rows, then import."
        backTo="/inventory"
      />

      <section className="card">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-semibold">Download the template</h2>
            <p className="mt-1 text-sm text-slate-500">
              Includes sample rows, dropdowns, and field instructions.
            </p>
          </div>
          <Button variant="secondary" onClick={onDownloadTemplate}>
            Download Template (.xlsx)
          </Button>
        </div>
      </section>

      <section className="card">
        <h2 className="mb-3 font-semibold">Choose a file</h2>
        <div
          role="button"
          tabIndex={0}
          aria-label="Choose a product file or drop it here"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
            dragging
              ? 'border-brand-500 bg-brand-50'
              : 'border-slate-300 hover:border-brand-400 hover:bg-slate-50'
          }`}
        >
          {file ? (
            <>
              <div className="font-medium text-slate-900">{file.name}</div>
              <div className="mt-1 text-xs text-slate-500">
                {(file.size / 1024).toFixed(1)} KB · select or drop another file to replace
              </div>
            </>
          ) : (
            <>
              <div className="font-medium text-slate-900">Drop a file here or browse</div>
              <div className="mt-1 text-sm text-slate-500">
                .xlsx, .xlsm, or .csv · maximum 10 MB
              </div>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS.join(',')}
            className="sr-only"
            tabIndex={-1}
            onChange={(event) => {
              const selectedFile = event.target.files?.[0];
              if (selectedFile) pickFile(selectedFile);
              event.target.value = '';
            }}
          />
        </div>

        {file && !preview && (
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="ghost" onClick={reset}>Clear</Button>
            <Button onClick={onPreview} loading={importMutation.isPending}>
              Preview Import
            </Button>
          </div>
        )}
        {error && (
          <div role="alert" className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
      </section>

      {preview && (
        <section className="space-y-4" aria-label="Import preview">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <SummaryCard label="Total rows" value={preview.total} />
            <SummaryCard label="Valid" value={preview.valid} tone="success" />
            <SummaryCard label="Errors" value={preview.invalid} tone={preview.invalid ? 'danger' : 'neutral'} />
            <SummaryCard label="Warnings" value={preview.warnings} tone={preview.warnings ? 'warning' : 'neutral'} />
          </div>

          {preview.invalid > 0 && (
            <div className="card border-red-200 bg-red-50">
              <h2 className="mb-2 font-semibold text-red-900">
                {preview.invalid} row{preview.invalid !== 1 ? 's' : ''} need attention
              </h2>
              <div className="max-h-72 divide-y divide-red-100 overflow-y-auto">
                {preview.errors.map((rowError) => (
                  <div key={rowError.row} className="py-2 text-sm">
                    <div className="font-medium text-red-900">
                      Row {rowError.row} — {rowError.sku}
                    </div>
                    <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs text-red-700">
                      {rowError.messages.map((message) => <li key={message}>{message}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
              <label className="mt-4 flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={skipErrors}
                  onChange={(event) => setSkipErrors(event.target.checked)}
                />
                Skip invalid rows and import the {preview.valid} valid row{preview.valid !== 1 ? 's' : ''} only
              </label>
            </div>
          )}

          {preview.preview?.length > 0 && (
            <div className="card-tight overflow-hidden">
              <div className="border-b bg-slate-50 px-4 py-3">
                <h2 className="text-sm font-semibold">
                  Preview
                  {preview.truncated_preview && (
                    <span className="font-normal text-slate-500"> (first 100 rows shown)</span>
                  )}
                </h2>
              </div>
              <div className="max-h-80 overflow-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th><th>SKU</th><th>Part No.</th><th>Name</th><th>Category</th>
                      <th>Type</th><th className="text-right">Retail</th>
                      <th className="text-right">Wholesale</th><th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview.map((row) => (
                      <tr key={row.row}>
                        <td className="text-xs text-slate-400">{row.row}</td>
                        <td className="font-mono text-xs">{row.sku}</td>
                        <td className="font-mono text-xs">{row.part_number || '—'}</td>
                        <td>{row.name}</td>
                        <td>{row.category}</td>
                        <td className="text-xs">{row.product_type}</td>
                        <td className="text-right">{row.retail_price}</td>
                        <td className="text-right">{row.wholesale_price}</td>
                        <td><span className={`badge-${row.status === 'error' ? 'danger' : row.status === 'warning' ? 'warning' : 'success'}`}>{row.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {(!preview.invalid || skipErrors) && preview.valid > 0 && (
            <div className="card border-brand-200 bg-brand-50">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="font-semibold text-brand-900">
                    Ready to import {preview.valid} product{preview.valid !== 1 ? 's' : ''}
                  </div>
                  <div className="mt-0.5 text-sm text-brand-800">
                    Existing SKUs will not be modified.
                  </div>
                </div>
                <Button onClick={onCommit} loading={importMutation.isPending}>
                  Import {preview.valid} Product{preview.valid !== 1 ? 's' : ''}
                </Button>
              </div>
            </div>
          )}

          {commit?.aborted && (
            <div role="alert" className="card border-red-200 bg-red-50 text-sm text-red-800">
              {commit.reason || 'Import was aborted. Nothing was created.'}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function SummaryCard({ label, value, tone = 'neutral' }) {
  const tones = {
    success: 'border-green-200 bg-green-50 text-green-900',
    danger: 'border-red-200 bg-red-50 text-red-900',
    warning: 'border-amber-200 bg-amber-50 text-amber-900',
    neutral: 'border-slate-200 bg-white text-slate-900',
  };
  return (
    <div className={`rounded-md border p-4 ${tones[tone]}`}>
      <div className="text-xs uppercase opacity-70">{label}</div>
      <div className="mt-1 text-2xl font-bold">{value ?? 0}</div>
    </div>
  );
}