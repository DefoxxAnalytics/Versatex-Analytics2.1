/**
 * Organization Switcher component for superusers
 *
 * Allows superusers to switch between organizations to view their analytics data.
 * Non-superusers will not see this component.
 */
import { Building2, ChevronDown, Check, RotateCcw } from 'lucide-react';
import { useOrganization } from '@/contexts/OrganizationContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import type { ColorScheme } from '@/hooks/useSettings';

interface OrganizationSwitcherProps {
  colorScheme?: ColorScheme;
}

export function OrganizationSwitcher({
  colorScheme = 'navy',
}: OrganizationSwitcherProps) {
  const {
    activeOrganization,
    userOrganization,
    organizations,
    canSwitch,
    isViewingOtherOrg,
    isLoading,
    switchOrganization,
    resetToDefault,
  } = useOrganization();

  // Don't render if user can't switch
  if (!canSwitch || isLoading) {
    return null;
  }

  // Get button styles based on color scheme
  const buttonStyles =
    colorScheme === 'navy'
      ? 'text-white hover:bg-blue-700 border-blue-700'
      : 'text-gray-700 hover:bg-gray-100 border-gray-200';

  const activeStyles = isViewingOtherOrg
    ? colorScheme === 'navy'
      ? 'bg-amber-500/20 border-amber-400/50 text-amber-100'
      : 'bg-amber-50 border-amber-200 text-amber-800'
    : '';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            'flex items-center gap-2 h-9 px-3 transition-colors',
            buttonStyles,
            activeStyles
          )}
        >
          <Building2 className="h-4 w-4" />
          <span className="max-w-[120px] truncate hidden sm:inline">
            {activeOrganization?.name || 'Select Org'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground" />
          Switch Organization
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Reset to default option */}
        {isViewingOtherOrg && userOrganization && (
          <>
            <DropdownMenuItem
              onClick={resetToDefault}
              className="flex items-center gap-2 text-blue-600 dark:text-blue-400"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset to My Organization</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
          </>
        )}

        {/* Organization list */}
        <div className="max-h-64 overflow-y-auto">
          {organizations.map((org) => {
            const isActive = activeOrganization?.id === org.id;
            const isUserOrg = userOrganization?.id === org.id;

            return (
              <DropdownMenuItem
                key={org.id}
                onClick={() => switchOrganization(org.id)}
                className={cn(
                  'flex items-center justify-between gap-2',
                  isActive && 'bg-accent'
                )}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate">{org.name}</span>
                  {isUserOrg && (
                    <span className="text-xs text-muted-foreground">(You)</span>
                  )}
                </div>
                {isActive && <Check className="h-4 w-4 text-primary" />}
              </DropdownMenuItem>
            );
          })}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
