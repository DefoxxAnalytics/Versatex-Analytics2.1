/**
 * Organization Context for superuser multi-organization access
 *
 * Allows superusers to switch between organizations to view their data
 * in the frontend dashboard.
 */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from './AuthContext';
import { api, Organization } from '@/lib/api';

interface OrganizationContextType {
  /** Currently active organization (defaults to user's own org) */
  activeOrganization: Organization | null;
  /** User's own organization */
  userOrganization: Organization | null;
  /** List of all organizations (only populated for superusers) */
  organizations: Organization[];
  /** Whether the user can switch organizations (superuser only) */
  canSwitch: boolean;
  /** Whether we're viewing a different org than user's own */
  isViewingOtherOrg: boolean;
  /** Loading state */
  isLoading: boolean;
  /** Switch to a different organization */
  switchOrganization: (orgId: number) => void;
  /** Reset to user's own organization */
  resetToDefault: () => void;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(
  undefined
);

const STORAGE_KEY = 'active_organization_id';

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { user, isSuperAdmin, isAuth } = useAuth();
  const queryClient = useQueryClient();

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [activeOrganization, setActiveOrganization] =
    useState<Organization | null>(null);
  const [userOrganization, setUserOrganization] = useState<Organization | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);

  // Track if we've already initialized to prevent duplicate fetches
  const initializedRef = useRef(false);
  const lastUserIdRef = useRef<number | null>(null);

  // Determine if user can switch organizations
  const canSwitch = isSuperAdmin && organizations.length > 1;

  // Check if viewing a different org
  const isViewingOtherOrg =
    activeOrganization !== null &&
    userOrganization !== null &&
    activeOrganization.id !== userOrganization.id;

  /**
   * Initialize organization state - runs once per user session
   */
  useEffect(() => {
    const initializeOrganizations = async () => {
      // Skip if not authenticated
      if (!isAuth || !user) {
        setIsLoading(false);
        return;
      }

      // Skip if already initialized for this user
      const userId = user.id;
      if (initializedRef.current && lastUserIdRef.current === userId) {
        return;
      }

      // Mark as initializing
      initializedRef.current = true;
      lastUserIdRef.current = userId;
      setIsLoading(true);

      try {
        // Build user's org from profile data (no API call needed)
        const userOrg: Organization | null = user.profile?.organization
          ? {
              id: user.profile.organization,
              name: user.profile.organization_name || 'Unknown',
              slug: '',
              description: '',
              is_active: true,
              created_at: '',
            }
          : null;

        setUserOrganization(userOrg);

        // For superusers, fetch all organizations (single API call)
        if (isSuperAdmin) {
          try {
            const response = await api.get('/auth/organizations/');
            const allOrgs = (response.data.results ?? response.data) as Organization[];
            setOrganizations(allOrgs);

            // Check for persisted organization selection
            const storedOrgId = localStorage.getItem(STORAGE_KEY);
            if (storedOrgId) {
              const storedOrg = allOrgs.find(
                (org) => org.id === parseInt(storedOrgId, 10)
              );
              if (storedOrg) {
                setActiveOrganization(storedOrg);
              } else {
                // Stored org no longer exists, reset to user's org
                localStorage.removeItem(STORAGE_KEY);
                setActiveOrganization(userOrg);
              }
            } else {
              setActiveOrganization(userOrg);
            }
          } catch {
            // On fetch error, just use user's org
            setOrganizations(userOrg ? [userOrg] : []);
            setActiveOrganization(userOrg);
          }
        } else {
          // Non-superusers only see their own org
          setOrganizations(userOrg ? [userOrg] : []);
          setActiveOrganization(userOrg);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeOrganizations();
  }, [isAuth, user, isSuperAdmin]);

  /**
   * Clear organization state on logout
   */
  useEffect(() => {
    if (!isAuth) {
      setOrganizations([]);
      setActiveOrganization(null);
      setUserOrganization(null);
      localStorage.removeItem(STORAGE_KEY);
      // Reset initialization tracking so next login re-fetches
      initializedRef.current = false;
      lastUserIdRef.current = null;
    }
  }, [isAuth]);

  /**
   * Switch to a different organization
   */
  const switchOrganization = useCallback(
    (orgId: number) => {
      if (!canSwitch) return;

      const newOrg = organizations.find((org) => org.id === orgId);
      if (!newOrg) return;

      setActiveOrganization(newOrg);
      localStorage.setItem(STORAGE_KEY, String(orgId));

      // Invalidate all queries to refetch with new organization
      queryClient.invalidateQueries();

      // Dispatch custom event for any listeners
      window.dispatchEvent(
        new CustomEvent('organizationChanged', {
          detail: { organizationId: orgId, organization: newOrg },
        })
      );
    },
    [canSwitch, organizations, queryClient]
  );

  /**
   * Reset to user's own organization
   */
  const resetToDefault = useCallback(() => {
    if (!userOrganization) return;

    setActiveOrganization(userOrganization);
    localStorage.removeItem(STORAGE_KEY);

    // Invalidate all queries to refetch with user's organization
    queryClient.invalidateQueries();

    // Dispatch custom event
    window.dispatchEvent(
      new CustomEvent('organizationChanged', {
        detail: {
          organizationId: userOrganization.id,
          organization: userOrganization,
        },
      })
    );
  }, [userOrganization, queryClient]);

  return (
    <OrganizationContext.Provider
      value={{
        activeOrganization,
        userOrganization,
        organizations,
        canSwitch,
        isViewingOtherOrg,
        isLoading,
        switchOrganization,
        resetToDefault,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error(
      'useOrganization must be used within an OrganizationProvider'
    );
  }
  return context;
}

/**
 * Helper to get organization_id parameter for API calls
 * Returns empty object if viewing user's own org (default behavior)
 */
export function getOrganizationParam(): { organization_id?: number } {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored ? { organization_id: parseInt(stored, 10) } : {};
}
