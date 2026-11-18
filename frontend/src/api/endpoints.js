// Centralized list of every API path. Keep in sync with backend urls.

export const endpoints = {
  // ---- auth ----
  auth: {
    login:            '/accounts/auth/login/',
    logout:           '/accounts/auth/logout/',
    me:               '/accounts/auth/me/',
    changePassword:   '/accounts/auth/change-password/',
  },

  // ---- accounts ----
  users: {
    list:  '/accounts/users/',
    detail: (id) => `/accounts/users/${id}/`,
  },

  // ---- customers ----
  customers: {
    list:      '/customers/',
    detail:    (id) => `/customers/${id}/`,
    walkIn:    '/customers/walk-in/',
    withDebt:  '/customers/with-debt/',
    assignRoute: (id) => `/customers/${id}/assign-route/`,
    contacts:  '/customers/contacts/',
    routeAssignments: '/customers/route-assignments/',
  },

  // ---- inventory ----
  inventory: {
    categories:     '/inventory/categories/',
    categoryDetail: (id) => `/inventory/categories/${id}/`,
    products:       '/inventory/products/',
    productDetail:  (id) => `/inventory/products/${id}/`,
    productImport:  '/inventory/products/import/',
    productImportTemplate: '/inventory/products/import/template/',
    productLookup:  '/inventory/products/lookup/',
    productSummary: (id) => `/inventory/products/${id}/summary/`,
    locations:      '/inventory/locations/',
    locationDetail: (id) => `/inventory/locations/${id}/`,
    stockLevels:    '/inventory/stock-levels/',
    stockAdjust:    '/inventory/stock/adjust/',
    movements:      '/inventory/movements/',
    transfers:      '/inventory/transfers/',
    transferDetail: (id) => `/inventory/transfers/${id}/`,
    transferDispatch: (id) => `/inventory/transfers/${id}/dispatch/`,
    transferReceive:  (id) => `/inventory/transfers/${id}/receive/`,
    transferCancel:   (id) => `/inventory/transfers/${id}/cancel/`,
  },

  // ---- suppliers ----
  suppliers: {
    list:      '/suppliers/',
    detail:    (id) => `/suppliers/${id}/`,
    products:  (id) => `/suppliers/${id}/products/`,
    stats:     (id) => `/suppliers/${id}/stats/`,
    deactivate: (id) => `/suppliers/${id}/deactivate/`,
    links:     '/suppliers/products/',
    linkDetail: (id) => `/suppliers/products/${id}/`,
    forProduct: (productId) => `/suppliers/products/for-product/${productId}/`,
    preferred:  (productId) => `/suppliers/products/preferred/${productId}/`,
  },

  // ---- sales ----
  sales: {
    list:        '/sales/',
    detail:      (id) => `/sales/${id}/`,
    preview:     '/sales/preview/',
    confirm:     (id) => `/sales/${id}/confirm/`,
    cancel:      (id) => `/sales/${id}/cancel/`,
    applyPayment:(id) => `/sales/${id}/apply-payment/`,
    receipt:     (id) => `/sales/${id}/receipt/`,
    returns:     (id) => `/sales/${id}/returns/`,
    returnsList: '/sales/returns/',
    returnDetail:(id) => `/sales/returns/${id}/`,
    returnApprove: (id) => `/sales/returns/${id}/approve/`,
    returnReject:  (id) => `/sales/returns/${id}/reject/`,
    returnComplete:(id) => `/sales/returns/${id}/complete/`,
    specialOrders: '/sales/special-orders/',
    specialOrderDetail: (id) => `/sales/special-orders/${id}/`,
    soMarkArrived:   (id) => `/sales/special-orders/${id}/mark-arrived/`,
    soMarkDelivered: (id) => `/sales/special-orders/${id}/mark-delivered/`,
  },

  // ---- payments ----
  payments: {
    methods:       '/payments/methods/',
    list:          '/payments/',
    detail:        (id) => `/payments/${id}/`,
    reverse:       (id) => `/payments/${id}/reverse/`,
    mpesaTransactions: '/payments/mpesa/transactions/',
    mpesaReconcile:    (id) => `/payments/mpesa/transactions/${id}/reconcile/`,
    stkPush:          '/payments/mpesa/stk-push/',
    ledger:           '/payments/ledger/',
  },

  // ---- expenses ----
  expenses: {
    categories:     '/expenses/categories/',
    categoryDetail: (id) => `/expenses/categories/${id}/`,
    list:      '/expenses/',
    detail:    (id) => `/expenses/${id}/`,
    summary:        '/expenses/summary/',
    byCategory:     '/expenses/by-category/',
    byLocation:     '/expenses/by-location/',
    monthlyTrend:   '/expenses/monthly-trend/',
    byRouteRun:     (id) => `/expenses/by-route-run/${id}/`,
  },

  // ---- routes ----
  routes: {
    list:         '/routes/',
    detail:       (id) => `/routes/${id}/`,
    changeAgent:  (id) => `/routes/${id}/change-agent/`,
    reassign:     (id) => `/routes/${id}/reassign-customers/`,
    deactivate:   (id) => `/routes/${id}/deactivate/`,
    profitability:(id) => `/routes/${id}/profitability/`,
    routeRuns:    (id) => `/routes/${id}/runs/`,
    schedules:    '/routes/schedules/',
    runs:         '/routes/runs/',
    runDetail:    (id) => `/routes/runs/${id}/`,
    runStart:     (id) => `/routes/runs/${id}/start/`,
    runComplete:  (id) => `/routes/runs/${id}/complete/`,
    runCancel:    (id) => `/routes/runs/${id}/cancel/`,
    runMaterialize:  '/routes/runs/materialize/',
    runReconciliation: (id) => `/routes/runs/${id}/reconciliation/`,
    runVarianceReport:'/routes/runs/variance-report/',
    changeLog:   '/routes/change-log/',
  },

  // ---- purchasing ----
  purchasing: {
    pos:        '/purchasing/purchase-orders/',
    poDetail:   (id) => `/purchasing/purchase-orders/${id}/`,
    poSend:     (id) => `/purchasing/purchase-orders/${id}/send/`,
    poCancel:   (id) => `/purchasing/purchase-orders/${id}/cancel/`,
    poReceive:  (id) => `/purchasing/purchase-orders/${id}/receive/`,
    poOutstanding: (id) => `/purchasing/purchase-orders/${id}/outstanding/`,
    grns:       '/purchasing/grns/',
    grnDetail:  (id) => `/purchasing/grns/${id}/`,
  },

  // ---- etims ----
  etims: {
    config:      '/etims/config/',
    invoices:    '/etims/invoices/',
    invoiceDetail: (id) => `/etims/invoices/${id}/`,
    resubmit:    (id) => `/etims/invoices/${id}/resubmit/`,
    items:       '/etims/items/',
    sequences:   '/etims/sequences/',
  },

  // ---- preorders (staff + portal) ----
  preorders: {
    staffList:   '/preorders/',
    staffDetail: (id) => `/preorders/${id}/`,
    confirm:     (id) => `/preorders/${id}/confirm/`,
    prepare:     (id) => `/preorders/${id}/prepare/`,
    ready:       (id) => `/preorders/${id}/ready/`,
    deliver:     (id) => `/preorders/${id}/deliver/`,
    cancel:      (id) => `/preorders/${id}/cancel/`,

    portal: {
      requestOtp: '/preorders/portal/auth/request-otp/',
      verifyOtp:  '/preorders/portal/auth/verify-otp/',
      logout:     '/preorders/portal/auth/logout/',
      catalog:    '/preorders/portal/catalog/',
      categories: '/preorders/portal/catalog/categories/',
      product:    (id) => `/preorders/portal/catalog/${id}/`,
      orders:     '/preorders/portal/orders/',
      orderDetail:(id) => `/preorders/portal/orders/${id}/`,
      orderCancel:(id) => `/preorders/portal/orders/${id}/cancel/`,
    },
  },

  // ---- printing ----
  printing: {
    printers:      '/printing/printers/',
    printerDetail: (id) => `/printing/printers/${id}/`,
    testPrint:     (id) => `/printing/printers/${id}/test-print/`,
    jobs:          '/printing/jobs/',
    jobDetail:     (id) => `/printing/jobs/${id}/`,
    queueReceipt:  '/printing/jobs/queue/receipt/',
    queueCreditNote: '/printing/jobs/queue/credit-note/',
    queuePreorderSlip: '/printing/jobs/queue/preorder-slip/',
    queueRouteSheet:  '/printing/jobs/queue/route-sheet/',
    jobDispatch:   (id) => `/printing/jobs/${id}/dispatch/`,
    jobRetry:      (id) => `/printing/jobs/${id}/retry/`,
    jobCancel:     (id) => `/printing/jobs/${id}/cancel/`,
    jobEscpos:     (id) => `/printing/jobs/${id}/escpos/`,
    jobReportResult: (id) => `/printing/jobs/${id}/report-result/`,
  },

  // ---- reporting ----
  reporting: {
    dashboard:           '/reporting/dashboard/',
    profitLoss:          '/reporting/profit-loss/',
    profitByChannel:     '/reporting/profit-by-channel/',
    profitByProductType: '/reporting/profit-by-product-type/',
    cashReconciliation:  '/reporting/cash/reconciliation/',
    cashVariance:        '/reporting/cash/variance/',
    paymentMethods:      '/reporting/payment-methods/',
    vat:                 '/reporting/vat/',
    etimsHealth:         '/reporting/etims/health/',
    etimsFailures:       '/reporting/etims/failures/',
    salesSummary:        '/reporting/sales/summary/',
    salesByDay:          '/reporting/sales/by-day/',
    salesByCustomerType: '/reporting/sales/by-customer-type/',
    topProducts:         '/reporting/sales/top-products/',
    worstProducts:       '/reporting/sales/worst-products/',
    marginAnalysis:      '/reporting/sales/margin-analysis/',
    stockValuation:      '/reporting/stock/valuation/',
    lowStock:            '/reporting/stock/low-stock/',
    stockMovements:      '/reporting/stock/movements/',
    deadStock:           '/reporting/stock/dead-stock/',
    purchasesBySupplier: '/reporting/suppliers/purchases/',
    supplierPriceTrend:  '/reporting/suppliers/price-trend/',
    agingSummary:        '/reporting/customers/aging/',
    agingDetail:         '/reporting/customers/aging-detail/',
    topCustomers:        '/reporting/customers/top/',
    creditUtilization:   '/reporting/customers/credit-utilization/',
  },
};