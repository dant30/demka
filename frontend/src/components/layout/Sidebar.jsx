import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useSystemHealth } from "@/api/queries";
import StatusDot from "@/components/ui/StatusDot";
import { storage } from "@/storage/localStorage";

/**
 * Grouped navigation definition. Sections collapse to icons-only mode
 * when the sidebar is collapsed. Items are filtered by role at render time.
 */
const NAV_GROUPS = [
  {
    title: "Operations",
    items: [
      { to: "/",            label: "Dashboard",  icon: "📊", bossOnly: true,  end: true },
      { to: "/pos",         label: "Shop POS",   icon: "🛒" },
      { to: "/field",       label: "Field Sales", icon: "🚐", fieldOnly: true },
      { to: "/sales",       label: "Sales",      icon: "🧾" },
      { to: "/preorders",   label: "Preorders",  icon: "📝" },
    ],
  },
  {
    title: "Inventory",
    items: [
      { to: "/inventory",   label: "Products",   icon: "📦" },
      { to: "/purchasing",  label: "Purchasing", icon: "📥", bossOnly: true },
      { to: "/suppliers",   label: "Suppliers",  icon: "🚚", bossOnly: true },
    ],
  },
  {
    title: "Customers",
    items: [
      { to: "/customers",   label: "Customers",  icon: "👥" },
      { to: "/routes",      label: "Routes",     icon: "🗺️" },
    ],
  },
  {
    title: "Finance",
    items: [
      { to: "/payments",    label: "Payments",   icon: "💳" },
      { to: "/expenses",    label: "Expenses",   icon: "💸" },
      { to: "/reports",     label: "Reports",    icon: "📈", bossOnly: true },
    ],
  },
  {
    title: "Admin",
    items: [
      { to: "/admin/etims",    label: "eTIMS",    icon: "🏛️", bossOnly: true },
      { to: "/admin/printers", label: "Printers", icon: "🖨️", bossOnly: true },
      { to: "/admin/users",    label: "Users",    icon: "🔧", bossOnly: true },
    ],
  },
];

const STORAGE_KEY = "demka_sidebar_collapsed";

export default function Sidebar() {
  const { user } = useAuth();
  const role = user?.role;
  const isBoss = role === "BOSS" || role === "ADMIN";
  const isField = role === "FIELD_AGENT";
  const { isPending: healthPending, isError: healthError } = useSystemHealth({
    enabled: Boolean(user),
  });
  const healthStatus = healthPending ? "checking" : healthError ? "offline" : "healthy";
  const healthLabel = healthPending
    ? "Checking system health"
    : healthError
      ? "System health unavailable"
      : "System healthy";

  // Persist collapse state across sessions.
  const [collapsed, setCollapsed] = useState(() => {
    return storage.getItem(STORAGE_KEY) === "1";
  });

  useEffect(() => {
    storage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
  }, [collapsed]);

  const width = collapsed
    ? "w-[var(--sidebar-width-collapsed)]"
    : "w-[var(--sidebar-width)]";

  return (
    <aside
      className={`
        hidden md:flex flex-col flex-shrink-0
        ${width}
        bg-slate-900 text-slate-300
        border-r border-slate-800
        transition-[width] duration-200 ease-out
      `}
    >
      {/* Brand / expand-collapse toggle */}
      <div className="h-[var(--topbar-height)] flex items-center justify-between px-4 border-b border-slate-800 flex-shrink-0">
        {!collapsed && (
          <span className="text-xl font-bold text-white tracking-tight">DEMKA</span>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      {/* Grouped nav list */}
      <nav className="flex-1 overflow-y-auto sidebar-scroll py-3">
        {NAV_GROUPS.map((group) => {
          // Filter group items by role.
          const visible = group.items.filter((item) => {
            if (item.bossOnly && !isBoss) return false;
            if (item.fieldOnly && !isField && !isBoss) return false;
            return true;
          });
          if (visible.length === 0) return null;

          return (
            <div key={group.title} className="mb-1">
              {/* Section header (hidden when collapsed) */}
              {!collapsed && (
                <div className="px-4 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                  {group.title}
                </div>
              )}
              {/* Items */}
              {visible.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  title={collapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    [
                      "flex items-center gap-3 mx-2 rounded-lg text-sm font-medium transition-colors",
                      collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5",
                      isActive
                        ? "bg-brand-600 text-white"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white",
                    ].join(" ")
                  }
                >
                  <span className="text-base leading-none w-5 text-center flex-shrink-0">
                    {item.icon}
                  </span>
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>

      {/* Footer — user role */}
      <div className="flex-shrink-0 p-3 border-t border-slate-800 text-[11px] text-slate-500">
        {collapsed ? (
          <div className="flex items-center justify-center gap-2">
            <span>{role?.slice(0, 3)}</span>
            <StatusDot
              status={healthStatus}
              label={healthLabel}
              showLabel={false}
              pulse
              className="text-slate-400"
            />
          </div>
        ) : (
          <>
            <div className="flex min-w-0 items-center justify-between gap-2">
              <div className="truncate">{user?.full_name || user?.username}</div>
              <StatusDot
                status={healthStatus}
                label={healthLabel}
                showLabel={false}
                pulse
                className="text-slate-400"
              />
            </div>
            <div className="text-slate-600 uppercase tracking-wide">{role}</div>
          </>
        )}
      </div>
    </aside>
  );
}