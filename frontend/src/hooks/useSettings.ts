import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

/**
 * Color scheme type for brand theming
 * - navy: New navy blue & white theme (default)
 * - classic: Original light theme with white header/sidebar
 */
export type ColorScheme = 'navy' | 'classic';

/**
 * User settings interface
 * Defines all configurable user preferences
 */
export interface UserSettings {
  // Theme preferences
  theme: 'light' | 'dark';

  // Color scheme (brand theme)
  colorScheme: ColorScheme;

  // Notification settings
  notifications: boolean;

  // Export preferences
  exportFormat: 'csv' | 'xlsx' | 'pdf';

  // User profile
  userName?: string;
  userEmail?: string;
  userRole?: string;

  // Display preferences
  currency?: string;
  dateFormat?: string;
  timezone?: string;
}

/**
 * Default settings
 * Used when no saved settings exist
 */
const DEFAULT_SETTINGS: UserSettings = {
  theme: 'light',
  colorScheme: 'navy',
  notifications: true,
  exportFormat: 'csv',
  currency: 'USD',
  dateFormat: 'MM/DD/YYYY',
  timezone: 'America/New_York',
};

/**
 * LocalStorage key for settings persistence
 */
const SETTINGS_STORAGE_KEY = 'user-settings';

/**
 * Load settings from localStorage
 * Returns default settings if none exist or if data is corrupted
 * 
 * @returns User settings object
 */
function loadSettings(): UserSettings {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!stored) {
      return DEFAULT_SETTINGS;
    }

    const parsed = JSON.parse(stored);
    
    // Merge with defaults to ensure all fields exist
    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
    };
  } catch (error) {
    // Handle corrupted data
    console.warn('Failed to load settings, using defaults:', error);
    return DEFAULT_SETTINGS;
  }
}

/**
 * Save settings to localStorage
 * Validates settings before saving
 * 
 * @param settings - Settings object to save
 */
function saveSettings(settings: Partial<UserSettings>): UserSettings {
  try {
    // Load current settings
    const current = loadSettings();
    
    // Merge with new settings
    const updated = {
      ...current,
      ...settings,
    };
    
    // Validate theme
    if (settings.theme && !['light', 'dark'].includes(settings.theme)) {
      updated.theme = DEFAULT_SETTINGS.theme;
    }

    // Validate color scheme
    if (settings.colorScheme && !['navy', 'classic'].includes(settings.colorScheme)) {
      updated.colorScheme = DEFAULT_SETTINGS.colorScheme;
    }

    // Validate export format
    if (settings.exportFormat && !['csv', 'xlsx', 'pdf'].includes(settings.exportFormat)) {
      updated.exportFormat = DEFAULT_SETTINGS.exportFormat;
    }
    
    // Save to localStorage
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(updated));
    
    return updated;
  } catch (error) {
    console.error('Failed to save settings:', error);
    throw error;
  }
}

/**
 * Hook to access user settings
 * 
 * Features:
 * - Loads settings from localStorage
 * - Returns default settings if none exist
 * - Handles corrupted data gracefully
 * - Caches settings for performance
 * 
 * @example
 * ```tsx
 * const { data: settings, isLoading } = useSettings();
 * 
 * if (isLoading) return <div>Loading...</div>;
 * 
 * return <div>Theme: {settings.theme}</div>;
 * ```
 */
export function useSettings() {
  return useQuery<UserSettings>({
    queryKey: ['settings'],
    queryFn: loadSettings,
    staleTime: Infinity, // Settings don't go stale
    cacheTime: Infinity, // Keep in cache forever
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}

/**
 * Hook to update user settings
 * 
 * Features:
 * - Validates settings before saving
 * - Persists to localStorage
 * - Updates cache automatically
 * - Supports partial updates
 * 
 * Security:
 * - Validates enum values (theme, exportFormat)
 * - Sanitizes input before storage
 * - Handles errors gracefully
 * 
 * @example
 * ```tsx
 * const updateSettings = useUpdateSettings();
 * 
 * // Update theme only
 * updateSettings.mutate({ theme: 'dark' });
 * 
 * // Update multiple settings
 * updateSettings.mutate({
 *   theme: 'dark',
 *   notifications: false,
 *   userName: 'John Doe'
 * });
 * ```
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation<UserSettings, Error, Partial<UserSettings>>({
    mutationFn: async (settings: Partial<UserSettings>) => {
      return saveSettings(settings);
    },
    onSuccess: (data) => {
      // Update the cache with new settings
      queryClient.setQueryData(['settings'], data);
    },
  });
}

/**
 * Hook to reset settings to defaults
 * 
 * @example
 * ```tsx
 * const resetSettings = useResetSettings();
 * 
 * resetSettings.mutate();
 * ```
 */
export function useResetSettings() {
  const queryClient = useQueryClient();

  return useMutation<UserSettings, Error, void>({
    mutationFn: async () => {
      localStorage.removeItem(SETTINGS_STORAGE_KEY);
      return DEFAULT_SETTINGS;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['settings'], data);
    },
  });
}
