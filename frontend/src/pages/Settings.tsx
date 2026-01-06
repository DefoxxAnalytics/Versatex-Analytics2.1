import { useState, useEffect } from 'react';
import {
  useSettings,
  useUpdateSettings,
  useResetSettings,
  type ColorScheme,
  type AIProvider,
  type ForecastingModel,
} from '@/hooks/useSettings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import {
  User,
  Bell,
  Download,
  Palette,
  RotateCcw,
  Save,
  Sun,
  Moon,
  Brain,
  Sparkles,
  Key,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

/**
 * Settings Page Component
 *
 * Features:
 * - User profile management
 * - Theme preferences (light/dark mode)
 * - Color scheme preferences (Navy/Classic)
 * - Notification settings
 * - Export format preferences
 * - Settings persistence
 * - Reset to defaults
 *
 * Security:
 * - Input validation
 * - XSS prevention through React escaping
 * - Sanitized localStorage operations
 *
 * Accessibility:
 * - Proper labels for all inputs
 * - Keyboard navigation
 * - ARIA attributes
 * - Focus management
 */
export default function Settings() {
  const { data: settings, isLoading } = useSettings();
  const updateSettings = useUpdateSettings();
  const resetSettings = useResetSettings();
  const { setTheme, setColorScheme } = useTheme();

  // Local state for form inputs - initialized empty, synced via useEffect
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userRole, setUserRole] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);

  // Sync local state when settings load (once)
  useEffect(() => {
    if (settings && !isInitialized) {
      setUserName(settings.userName || '');
      setUserEmail(settings.userEmail || '');
      setUserRole(settings.userRole || '');
      setIsInitialized(true);
    }
  }, [settings, isInitialized]);

  /**
   * Handle profile update
   * Validates and saves user profile information
   */
  const handleProfileUpdate = () => {
    // Basic validation
    if (userEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userEmail)) {
      toast.error('Please enter a valid email address');
      return;
    }

    updateSettings.mutate(
      {
        userName: userName.trim(),
        userEmail: userEmail.trim(),
        userRole: userRole.trim(),
      },
      {
        onSuccess: () => {
          toast.success('Profile updated successfully');
        },
        onError: () => {
          toast.error('Failed to update profile');
        },
      }
    );
  };

  /**
   * Handle theme change (light/dark mode)
   * Updates both settings and applies theme immediately
   */
  const handleThemeChange = (theme: 'light' | 'dark') => {
    // Apply theme immediately for instant feedback
    if (setTheme) {
      setTheme(theme);
    }

    // Save to settings for persistence
    updateSettings.mutate(
      { theme },
      {
        onSuccess: () => {
          toast.success(`Theme changed to ${theme} mode`);
        },
      }
    );
  };

  /**
   * Handle color scheme change (Navy/Classic)
   * Updates both settings and applies scheme immediately
   */
  const handleColorSchemeChange = (scheme: ColorScheme) => {
    // Apply color scheme immediately for instant feedback
    if (setColorScheme) {
      setColorScheme(scheme);
    }

    // Save to settings for persistence
    updateSettings.mutate(
      { colorScheme: scheme },
      {
        onSuccess: () => {
          const schemeName = scheme === 'navy' ? 'Navy Blue' : 'Classic';
          toast.success(`Color scheme changed to ${schemeName}`);
        },
      }
    );
  };

  /**
   * Handle notification toggle
   */
  const handleNotificationToggle = (enabled: boolean) => {
    updateSettings.mutate(
      { notifications: enabled },
      {
        onSuccess: () => {
          toast.success(`Notifications ${enabled ? 'enabled' : 'disabled'}`);
        },
      }
    );
  };

  /**
   * Handle export format change
   */
  const handleExportFormatChange = (format: 'csv' | 'xlsx' | 'pdf') => {
    updateSettings.mutate(
      { exportFormat: format },
      {
        onSuccess: () => {
          toast.success(`Default export format set to ${format.toUpperCase()}`);
        },
      }
    );
  };

  /**
   * Handle reset to defaults
   */
  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      resetSettings.mutate(undefined, {
        onSuccess: () => {
          setUserName('');
          setUserEmail('');
          setUserRole('');
          // Reset theme context state
          if (setTheme) setTheme('light');
          if (setColorScheme) setColorScheme('navy');
          toast.success('Settings reset to defaults');
        },
        onError: () => {
          toast.error('Failed to reset settings');
        },
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your account settings and preferences
        </p>
      </div>

      <Separator />

      {/* User Profile Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-blue-600" />
            <CardTitle>User Profile</CardTitle>
          </div>
          <CardDescription>
            Update your personal information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="userName">Name</Label>
            <Input
              id="userName"
              type="text"
              placeholder="Enter your name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="userEmail">Email</Label>
            <Input
              id="userEmail"
              type="email"
              placeholder="Enter your email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="userRole">Role</Label>
            <Input
              id="userRole"
              type="text"
              placeholder="e.g., Procurement Manager"
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              maxLength={100}
            />
          </div>

          <Button
            onClick={handleProfileUpdate}
            disabled={updateSettings.isPending}
            className="w-full sm:w-auto"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Profile
          </Button>
        </CardContent>
      </Card>

      {/* Theme Preferences */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-purple-600" />
            <CardTitle>Theme Preferences</CardTitle>
          </div>
          <CardDescription>
            Customize the look and feel of the application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Color Scheme Selection */}
          <div className="space-y-3">
            <Label htmlFor="colorScheme">Color Scheme</Label>
            <Select
              value={settings?.colorScheme || 'navy'}
              onValueChange={(value) => handleColorSchemeChange(value as ColorScheme)}
            >
              <SelectTrigger id="colorScheme" className="w-full sm:w-[280px]">
                <SelectValue placeholder="Select color scheme" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="navy">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-[#1e3a8a] border border-blue-900" />
                    <span>Navy Blue & White</span>
                  </div>
                </SelectItem>
                <SelectItem value="classic">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-white border border-gray-300" />
                    <span>Classic (Original)</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Choose between the modern navy theme or the original classic look
            </p>
          </div>

          <Separator />

          {/* Light/Dark Mode Selection */}
          <div className="space-y-3">
            <Label htmlFor="theme">Appearance</Label>
            <Select
              value={settings?.theme || 'light'}
              onValueChange={(value) => handleThemeChange(value as 'light' | 'dark')}
            >
              <SelectTrigger id="theme" className="w-full sm:w-[280px]">
                <SelectValue placeholder="Select appearance" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">
                  <div className="flex items-center gap-2">
                    <Sun className="h-4 w-4" />
                    <span>Light Mode</span>
                  </div>
                </SelectItem>
                <SelectItem value="dark">
                  <div className="flex items-center gap-2">
                    <Moon className="h-4 w-4" />
                    <span>Dark Mode</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Select light or dark mode for the interface
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-yellow-600" />
            <CardTitle>Notifications</CardTitle>
          </div>
          <CardDescription>
            Manage your notification preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="notifications" className="text-base">
                Enable Notifications
              </Label>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Receive alerts and updates
              </p>
            </div>
            <Switch
              id="notifications"
              checked={settings?.notifications || false}
              onCheckedChange={handleNotificationToggle}
            />
          </div>
        </CardContent>
      </Card>

      {/* Export Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5 text-green-600" />
            <CardTitle>Export Preferences</CardTitle>
          </div>
          <CardDescription>
            Set your default export format
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="exportFormat">Default Export Format</Label>
            <Select
              value={settings?.exportFormat || 'csv'}
              onValueChange={(value) => handleExportFormatChange(value as 'csv' | 'xlsx' | 'pdf')}
            >
              <SelectTrigger id="exportFormat" className="w-full sm:w-[200px]">
                <SelectValue placeholder="Select format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                <SelectItem value="pdf">PDF</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* AI & Predictive Analytics Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" />
            <CardTitle>AI & Predictive Analytics</CardTitle>
          </div>
          <CardDescription>
            Configure AI-powered insights and forecasting settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Forecasting Model Selection */}
          <div className="space-y-3">
            <Label htmlFor="forecastingModel">Forecasting Model</Label>
            <Select
              value={settings?.forecastingModel || 'standard'}
              onValueChange={(value) => {
                updateSettings.mutate(
                  { forecastingModel: value as ForecastingModel },
                  {
                    onSuccess: () => {
                      toast.success(`Forecasting model set to ${value === 'standard' ? 'Standard ML' : 'Simple (Moving Average)'}`);
                    },
                  }
                );
              }}
            >
              <SelectTrigger id="forecastingModel" className="w-full sm:w-[280px]">
                <SelectValue placeholder="Select forecasting model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simple">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    <span>Simple (Moving Average)</span>
                  </div>
                </SelectItem>
                <SelectItem value="standard">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    <span>Standard ML (Recommended)</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Standard ML provides more accurate forecasts with trend and seasonality detection
            </p>
          </div>

          <Separator />

          {/* External AI Enhancement */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="useExternalAI" className="text-base">
                  Enable External AI Enhancement
                </Label>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Use Claude or OpenAI to enhance insights with strategic recommendations
                </p>
              </div>
              <Switch
                id="useExternalAI"
                checked={settings?.useExternalAI || false}
                onCheckedChange={(checked) => {
                  updateSettings.mutate(
                    { useExternalAI: checked },
                    {
                      onSuccess: () => {
                        toast.success(`External AI ${checked ? 'enabled' : 'disabled'}`);
                      },
                    }
                  );
                }}
              />
            </div>

            {/* Show AI Provider and API Key only when external AI is enabled */}
            {settings?.useExternalAI && (
              <div className="space-y-4 pl-4 border-l-2 border-indigo-200 dark:border-indigo-800">
                {/* AI Provider Selection */}
                <div className="space-y-2">
                  <Label htmlFor="aiProvider">AI Provider</Label>
                  <Select
                    value={settings?.aiProvider || 'anthropic'}
                    onValueChange={(value) => {
                      updateSettings.mutate(
                        { aiProvider: value as AIProvider },
                        {
                          onSuccess: () => {
                            const name = value === 'anthropic' ? 'Anthropic (Claude)' : 'OpenAI (GPT)';
                            toast.success(`AI provider set to ${name}`);
                          },
                        }
                      );
                    }}
                  >
                    <SelectTrigger id="aiProvider" className="w-full sm:w-[280px]">
                      <SelectValue placeholder="Select AI provider" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="anthropic">
                        <div className="flex items-center gap-2">
                          <Brain className="h-4 w-4" />
                          <span>Anthropic (Claude)</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="openai">
                        <div className="flex items-center gap-2">
                          <Sparkles className="h-4 w-4" />
                          <span>OpenAI (GPT)</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* API Key Input */}
                <div className="space-y-2">
                  <Label htmlFor="aiApiKey">API Key</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="aiApiKey"
                        type="password"
                        placeholder={settings?.aiApiKey ? '••••••••••••••••' : 'Enter your API key'}
                        className="pl-10"
                        maxLength={200}
                        onBlur={(e) => {
                          if (e.target.value) {
                            updateSettings.mutate(
                              { aiApiKey: e.target.value },
                              {
                                onSuccess: () => {
                                  toast.success('API key saved securely');
                                  e.target.value = '';
                                },
                              }
                            );
                          }
                        }}
                      />
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Your API key is stored encrypted and never displayed
                  </p>
                </div>
              </div>
            )}
          </div>

          <Separator />

          {/* Forecast Horizon */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="forecastHorizon">Forecast Horizon</Label>
              <span className="text-sm font-medium">
                {settings?.forecastHorizonMonths || 6} months
              </span>
            </div>
            <Slider
              id="forecastHorizon"
              min={3}
              max={24}
              step={1}
              value={[settings?.forecastHorizonMonths || 6]}
              onValueChange={(value) => {
                updateSettings.mutate(
                  { forecastHorizonMonths: value[0] },
                  {
                    onSuccess: () => {
                      toast.success(`Forecast horizon set to ${value[0]} months`);
                    },
                  }
                );
              }}
              className="w-full"
            />
            <p className="text-sm text-muted-foreground">
              How far ahead to forecast spending trends (3-24 months)
            </p>
          </div>

          <Separator />

          {/* Anomaly Sensitivity */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="anomalySensitivity">Anomaly Detection Sensitivity</Label>
              <span className="text-sm font-medium">
                {settings?.anomalySensitivity || 2} (
                {(settings?.anomalySensitivity || 2) <= 2
                  ? 'High'
                  : (settings?.anomalySensitivity || 2) <= 3
                    ? 'Medium'
                    : 'Low'}
                )
              </span>
            </div>
            <Slider
              id="anomalySensitivity"
              min={1}
              max={5}
              step={0.5}
              value={[settings?.anomalySensitivity || 2]}
              onValueChange={(value) => {
                updateSettings.mutate(
                  { anomalySensitivity: value[0] },
                  {
                    onSuccess: () => {
                      const level = value[0] <= 2 ? 'High' : value[0] <= 3 ? 'Medium' : 'Low';
                      toast.success(`Anomaly sensitivity set to ${level}`);
                    },
                  }
                );
              }}
              className="w-full"
            />
            <p className="text-sm text-muted-foreground">
              Lower values detect more anomalies, higher values only flag extreme outliers
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Reset Settings */}
      <Card className="border-red-200 dark:border-red-900">
        <CardHeader>
          <div className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5 text-red-600" />
            <CardTitle className="text-red-600">Reset Settings</CardTitle>
          </div>
          <CardDescription>
            Reset all settings to their default values
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={handleReset}
            disabled={resetSettings.isPending}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
