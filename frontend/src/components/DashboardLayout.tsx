import { useState, ReactNode } from 'react';
import { Link, useLocation } from 'wouter';
import {
  BarChart3,
  Package,
  Upload,
  FolderTree,
  Users,
  TrendingUp,
  Layers,
  CalendarDays,
  TrendingDown,
  Sparkles,
  LineChart,
  FileText,
  AlertTriangle,
  Settings,
  Menu,
  X,
  SlidersHorizontal,
  LogOut,
  LayoutDashboard,
  Calendar,
  Target,
  Shield,
  User as UserIcon,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useProcurementData } from '@/hooks/useProcurementData';
import type { ColorScheme } from '@/hooks/useSettings';
import { cn } from '@/lib/utils';
import { Breadcrumb } from './Breadcrumb';
import { FilterPane } from './FilterPane';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

/**
 * Style helpers for color scheme-aware components
 * Provides consistent styling between Navy and Classic themes
 */
const getHeaderStyles = (scheme: ColorScheme) => ({
  header: scheme === 'navy'
    ? 'bg-[#1e3a8a] border-blue-900 shadow-lg'
    : 'bg-white border-gray-200 shadow-sm',
  text: scheme === 'navy' ? 'text-white' : 'text-gray-900',
  logo: scheme === 'navy' ? 'brightness-0 invert' : '',
  button: scheme === 'navy'
    ? 'text-white hover:bg-blue-700'
    : 'text-gray-700 hover:bg-gray-100',
  userBox: scheme === 'navy'
    ? 'bg-blue-900/50 border-blue-700'
    : 'bg-gray-50 border-gray-200',
  avatar: scheme === 'navy'
    ? 'bg-white text-[#1e3a8a]'
    : 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white',
});

const getSidebarStyles = (scheme: ColorScheme) => ({
  bg: scheme === 'navy'
    ? 'bg-[#1e3a8a] border-blue-900'
    : 'bg-white border-gray-200',
  active: scheme === 'navy'
    ? 'bg-white/20 text-white font-medium'
    : 'bg-blue-50 text-blue-700 font-medium',
  inactive: scheme === 'navy'
    ? 'text-white/80 hover:text-white'
    : 'text-gray-700 hover:text-gray-900',
  hover: scheme === 'navy'
    ? 'hover:bg-white/10'
    : 'hover:bg-gray-100',
  focus: scheme === 'navy'
    ? 'focus:ring-white/50'
    : 'focus:ring-blue-500',
  icon: scheme === 'navy' ? 'text-white/70' : 'text-gray-500',
  iconActive: scheme === 'navy' ? 'text-white' : 'text-blue-600',
  divider: scheme === 'navy' ? 'bg-white/20' : 'bg-gray-200',
  dividerText: scheme === 'navy' ? 'text-white/60' : 'text-gray-500',
});

/**
 * Check if the current user has admin role
 */
function isAdmin(): boolean {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return false;

    const user = JSON.parse(userStr);
    return user?.profile?.role === 'admin';
  } catch {
    return false;
  }
}

/**
 * User information interface
 */
interface UserInfo {
  username: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  role: 'admin' | 'manager' | 'viewer';
  initials: string;
  displayName: string;
}

/**
 * Get current user information from localStorage
 */
function getUserInfo(): UserInfo | null {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;

    const user = JSON.parse(userStr);
    const firstName = user?.first_name || '';
    const lastName = user?.last_name || '';
    const username = user?.username || 'User';
    const role = user?.profile?.role || 'viewer';

    // Generate initials
    let initials = '';
    if (firstName && lastName) {
      initials = `${firstName[0]}${lastName[0]}`.toUpperCase();
    } else if (firstName) {
      initials = firstName.substring(0, 2).toUpperCase();
    } else if (username) {
      initials = username.substring(0, 2).toUpperCase();
    } else {
      initials = 'U';
    }

    // Generate display name
    let displayName = '';
    if (firstName && lastName) {
      displayName = `${firstName} ${lastName}`;
    } else if (firstName) {
      displayName = firstName;
    } else {
      displayName = username;
    }

    return {
      username,
      firstName,
      lastName,
      email: user?.email,
      role,
      initials,
      displayName,
    };
  } catch {
    return null;
  }
}

/**
 * Navigation item configuration
 * Each item represents a tab in the dashboard
 */
interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

/**
 * Complete navigation configuration for all 13 tabs
 * Organized logically by analysis type
 */
const NAV_ITEMS: NavItem[] = [
  {
    path: '/upload',
    label: 'Upload Data',
    icon: Upload,
    description: 'Upload procurement data files',
  },
  {
    path: '/',
    label: 'Overview',
    icon: LayoutDashboard,
    description: 'Dashboard overview',
  },
  {
    path: '/categories',
    label: 'Categories',
    icon: FolderTree,
    description: 'Spend analysis by category',
  },
  {
    path: '/suppliers',
    label: 'Suppliers',
    icon: Users,
    description: 'Supplier performance and insights',
  },
  {
    path: '/pareto',
    label: 'Pareto Analysis',
    icon: TrendingUp,
    description: '80/20 rule insights',
  },
  {
    path: '/stratification',
    label: 'Spend Stratification',
    icon: Layers,
    description: 'Spend tier analysis',
  },
  {
    path: '/seasonality',
    label: 'Seasonality',
    icon: Calendar,
    description: 'Time-based spending patterns',
  },
  {
    path: '/yoy',
    label: 'Year-over-Year',
    icon: BarChart3,
    description: 'Trend comparison',
  },
  {
    path: '/tail-spend',
    label: 'Tail Spend',
    icon: Target,
    description: 'Long-tail spending analysis',
  },
  {
    path: '/ai-insights',
    label: 'AI Insights',
    icon: Sparkles,
    description: 'Smart recommendations',
  },
  {
    path: '/predictive',
    label: 'Predictive Analytics',
    icon: LineChart,
    description: 'Forecasting and predictions',
  },
  {
    path: '/contracts',
    label: 'Contract Optimization',
    icon: FileText,
    description: 'Contract analysis',
  },
  {
    path: '/maverick',
    label: 'Maverick Spend',
    icon: AlertTriangle,
    description: 'Policy compliance tracking',
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: Settings,
    description: 'Configuration and preferences',
  },
];

/**
 * User display component showing avatar, name, and role
 */
function UserDisplay({ colorScheme }: { colorScheme: ColorScheme }) {
  const userInfo = getUserInfo();
  const headerStyles = getHeaderStyles(colorScheme);

  if (!userInfo) return null;

  // Role badge styling
  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'admin':
        return 'default'; // Blue
      case 'manager':
        return 'secondary'; // Green-ish
      case 'viewer':
        return 'outline'; // Gray outline
      default:
        return 'outline';
    }
  };

  const getRoleLabel = (role: string) => {
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  return (
    <div className={cn(
      "flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors",
      headerStyles.userBox
    )}>
      {/* Avatar */}
      <Avatar className="h-8 w-8">
        <AvatarFallback className={cn("text-sm font-semibold", headerStyles.avatar)}>
          {userInfo.initials}
        </AvatarFallback>
      </Avatar>

      {/* Name and Role - Hidden on small screens */}
      <div className="hidden md:flex md:flex-col md:gap-0.5">
        <span className={cn("text-sm font-medium leading-tight", headerStyles.text)}>
          {userInfo.displayName}
        </span>
        <Badge
          variant={getRoleBadgeVariant(userInfo.role)}
          className="text-xs w-fit"
        >
          {getRoleLabel(userInfo.role)}
        </Badge>
      </div>
    </div>
  );
}

/**
 * Logout button component
 */
function LogoutButton({ colorScheme }: { colorScheme: ColorScheme }) {
  const { logout } = useAuth();
  const headerStyles = getHeaderStyles(colorScheme);

  return (
    <button
      onClick={logout}
      className={cn(
        "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
        headerStyles.button
      )}
      title="Logout"
    >
      <LogOut className="h-4 w-4" />
      <span className="hidden sm:inline">Logout</span>
    </button>
  );
}

interface DashboardLayoutProps {
  children?: ReactNode;
}

/**
 * Main dashboard layout component with responsive sidebar navigation
 * 
 * Features:
 * - Responsive design with mobile menu
 * - Active route highlighting
 * - Accessibility support (ARIA labels, keyboard navigation)
 * - Data validation (prompts user to upload if no data)
 * 
 * @param {ReactNode} children - Content to render in the main area
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [location] = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isFilterPaneOpen, setIsFilterPaneOpen] = useState(true);
  const { data = [] } = useProcurementData();
  const { colorScheme } = useTheme();

  // Get style configurations based on current color scheme
  const headerStyles = getHeaderStyles(colorScheme);
  const sidebarStyles = getSidebarStyles(colorScheme);

  /**
   * Check if a navigation item is currently active
   * Handles both exact matches and root path
   */
  const isActive = (path: string): boolean => {
    if (path === '/' && location === '/') return true;
    if (path !== '/' && location.startsWith(path)) return true;
    return false;
  };

  /**
   * Toggle mobile menu state
   * Follows accessibility best practices with ARIA attributes
   */
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen((prev) => !prev);
  };

  /**
   * Close mobile menu when navigation occurs
   * Improves UX on mobile devices
   */
  const handleNavClick = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      {/* Header - Theme-aware styling */}
      <header className={cn(
        "border-b sticky top-0 z-40 transition-colors duration-300",
        headerStyles.header
      )}>
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src="/vtx_logo2.png"
              alt="Versatex Logo"
              className={cn("h-10 w-auto transition-all duration-300", headerStyles.logo)}
            />
            <h1 className={cn("text-xl font-bold transition-colors duration-300", headerStyles.text)}>
              Analytics Dashboard
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {/* User Display */}
            <UserDisplay colorScheme={colorScheme} />

            {/* Logout button */}
            <LogoutButton colorScheme={colorScheme} />

            {/* Filter pane toggle */}
            <button
              onClick={() => setIsFilterPaneOpen(!isFilterPaneOpen)}
              className={cn(
                "p-2 rounded-md transition-colors",
                headerStyles.button
              )}
              aria-label="Toggle filters"
              aria-expanded={isFilterPaneOpen}
              title="Toggle filter pane"
            >
              <SlidersHorizontal className="h-5 w-5" />
            </button>

            {/* Mobile menu toggle */}
            <button
              onClick={toggleMobileMenu}
              className={cn(
                "lg:hidden p-2 rounded-md transition-colors",
                headerStyles.button
              )}
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-navigation"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation - Theme-aware styling */}
        <aside
          id="mobile-navigation"
          className={cn(
            'fixed lg:sticky top-[73px] left-0 h-[calc(100vh-73px)] w-64 border-r',
            'overflow-y-auto transition-all duration-300 z-30',
            sidebarStyles.bg,
            isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          )}
        >
          <nav
            className="p-4 space-y-1"
            aria-label="Main navigation"
          >
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              // For Settings, render divider and Admin Panel link before it if user is admin
              if (item.path === '/settings' && isAdmin()) {
                return (
                  <div key="admin-section">
                    {/* Divider with label */}
                    <div className="pt-4 pb-2">
                      <div className="flex items-center gap-2 px-3 mb-3">
                        <Separator className={cn("flex-1", sidebarStyles.divider)} />
                        <span className={cn("text-xs font-semibold uppercase tracking-wider", sidebarStyles.dividerText)}>
                          Administration
                        </span>
                        <Separator className={cn("flex-1", sidebarStyles.divider)} />
                      </div>
                    </div>

                    {/* Admin Panel Link */}
                    <a
                      href={`${window.location.protocol}//${window.location.hostname}:8001/admin/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                        sidebarStyles.hover,
                        'focus:outline-none focus:ring-2',
                        sidebarStyles.focus,
                        sidebarStyles.inactive
                      )}
                      title="Django Admin Panel (admins only)"
                    >
                      <Shield className={cn("h-5 w-5", sidebarStyles.icon)} />
                      <span className="text-sm">Admin Panel</span>
                    </a>

                    {/* Settings Link */}
                    <Link
                      href={item.path}
                      onClick={handleNavClick}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                        sidebarStyles.hover,
                        'focus:outline-none focus:ring-2',
                        sidebarStyles.focus,
                        active ? sidebarStyles.active : sidebarStyles.inactive
                      )}
                      aria-current={active ? 'page' : undefined}
                      title={item.description}
                    >
                      <Icon className={cn('h-5 w-5', active ? sidebarStyles.iconActive : sidebarStyles.icon)} />
                      <span className="text-sm">{item.label}</span>
                    </Link>
                  </div>
                );
              }

              // For Settings (non-admin), render divider before it
              if (item.path === '/settings' && !isAdmin()) {
                return (
                  <div key="settings-section">
                    {/* Divider with label */}
                    <div className="pt-4 pb-2">
                      <div className="flex items-center gap-2 px-3 mb-3">
                        <Separator className={cn("flex-1", sidebarStyles.divider)} />
                        <span className={cn("text-xs font-semibold uppercase tracking-wider", sidebarStyles.dividerText)}>
                          Settings
                        </span>
                        <Separator className={cn("flex-1", sidebarStyles.divider)} />
                      </div>
                    </div>

                    {/* Settings Link */}
                    <Link
                      href={item.path}
                      onClick={handleNavClick}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                        sidebarStyles.hover,
                        'focus:outline-none focus:ring-2',
                        sidebarStyles.focus,
                        active ? sidebarStyles.active : sidebarStyles.inactive
                      )}
                      aria-current={active ? 'page' : undefined}
                      title={item.description}
                    >
                      <Icon className={cn('h-5 w-5', active ? sidebarStyles.iconActive : sidebarStyles.icon)} />
                      <span className="text-sm">{item.label}</span>
                    </Link>
                  </div>
                );
              }

              return (
                <Link
                  key={item.path}
                  href={item.path}
                  onClick={handleNavClick}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                    sidebarStyles.hover,
                    'focus:outline-none focus:ring-2',
                    sidebarStyles.focus,
                    active ? sidebarStyles.active : sidebarStyles.inactive
                  )}
                  aria-current={active ? 'page' : undefined}
                  title={item.description}
                >
                  <Icon className={cn('h-5 w-5', active ? sidebarStyles.iconActive : sidebarStyles.icon)} />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 lg:p-8">
          {/* Breadcrumb Navigation */}
          <Breadcrumb />
          {/* Show upload prompt if no data */}
          {data.length === 0 && location !== '/' && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>No data uploaded yet.</strong> Please{' '}
                <Link 
                  href="/"
                  className="underline font-medium hover:text-yellow-900"
                >
                  upload your procurement data
                </Link>{' '}
                to view analytics.
              </p>
            </div>
          )}

          {/* Render children or default message */}
          <div className="flex gap-6">
            <div className="flex-1 min-w-0">
              {children || (
                <div className="text-center py-12 text-gray-500">
                  <p>Select a tab from the navigation to view analytics.</p>
                </div>
              )}
            </div>

            {/* Filter Pane */}
            {isFilterPaneOpen && data.length > 0 && (
              <aside className="w-80 flex-shrink-0 hidden lg:block">
                <FilterPane />
              </aside>
            )}
          </div>
        </main>
      </div>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={toggleMobileMenu}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
