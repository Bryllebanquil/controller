import { useState, useEffect } from 'react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Checkbox } from './ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Search, 
  Filter, 
  X, 
  ChevronDown,
  SortAsc,
  SortDesc
} from 'lucide-react';

interface FilterOptions {
  status: string[];
  platform: string[];
  capabilities: string[];
}

interface SearchAndFilterProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onFiltersChange: (filters: FilterOptions) => void;
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  availableFilters: {
    platforms: string[];
    capabilities: string[];
  };
  resultCount: number;
}

export function SearchAndFilter({
  searchTerm,
  onSearchChange,
  onFiltersChange,
  onSortChange,
  availableFilters,
  resultCount
}: SearchAndFilterProps) {
  const [filters, setFilters] = useState<FilterOptions>({
    status: [],
    platform: [],
    capabilities: []
  });
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const activeFiltersCount = Object.values(filters).flat().length;

  useEffect(() => {
    onFiltersChange(filters);
  }, [filters, onFiltersChange]);

  useEffect(() => {
    onSortChange(sortBy, sortOrder);
  }, [sortBy, sortOrder, onSortChange]);

  const handleFilterChange = (category: keyof FilterOptions, value: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      [category]: checked 
        ? [...prev[category], value]
        : prev[category].filter(item => item !== value)
    }));
  };

  const clearFilters = () => {
    setFilters({
      status: [],
      platform: [],
      capabilities: []
    });
  };

  const handleSortOrderToggle = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  };

  // Quick search suggestions
  const searchSuggestions = [
    'Windows',
    'Linux',
    'macOS',
    'online',
    'offline',
    'screen',
    'camera',
    'audio'
  ];

  const getFilteredSuggestions = () => {
    if (!searchTerm) return [];
    return searchSuggestions.filter(suggestion => 
      suggestion.toLowerCase().includes(searchTerm.toLowerCase()) &&
      suggestion.toLowerCase() !== searchTerm.toLowerCase()
    ).slice(0, 3);
  };

  return (
    <div className="space-y-4">
      {/* Search and main controls */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
        <div className="relative flex-1 w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search agents, platforms, IPs..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9"
          />
          
          {/* Search suggestions */}
          {getFilteredSuggestions().length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-popover border rounded-md shadow-lg z-50">
              {getFilteredSuggestions().map((suggestion) => (
                <button
                  key={suggestion}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors first:rounded-t-md last:rounded-b-md"
                  onClick={() => onSearchChange(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2 sm:flex-nowrap sm:justify-end">
          {/* Advanced Filters */}
          <Popover open={isFilterOpen} onOpenChange={setIsFilterOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="relative">
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {activeFiltersCount > 0 && (
                  <Badge className="ml-2 h-5 w-5 p-0 text-xs">
                    {activeFiltersCount}
                  </Badge>
                )}
                <ChevronDown className="h-3 w-3 ml-1" />
              </Button>
            </PopoverTrigger>
            
            <PopoverContent className="w-80 z-50" align="start">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium">Filters</h4>
                  {activeFiltersCount > 0 && (
                    <Button variant="ghost" size="sm" onClick={clearFilters}>
                      Clear all
                    </Button>
                  )}
                </div>

                {/* Status Filter */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Status
                  </label>
                  <div className="mt-2 space-y-2">
                    {['online', 'offline'].map((status) => (
                      <div key={status} className="flex items-center space-x-2">
                        <Checkbox
                          id={`status-${status}`}
                          checked={filters.status.includes(status)}
                          onCheckedChange={(checked) => 
                            handleFilterChange('status', status, checked as boolean)
                          }
                        />
                        <label htmlFor={`status-${status}`} className="text-sm capitalize">
                          {status}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Platform Filter */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Platform
                  </label>
                  <div className="mt-2 space-y-2">
                    {availableFilters.platforms.map((platform) => (
                      <div key={platform} className="flex items-center space-x-2">
                        <Checkbox
                          id={`platform-${platform}`}
                          checked={filters.platform.includes(platform)}
                          onCheckedChange={(checked) => 
                            handleFilterChange('platform', platform, checked as boolean)
                          }
                        />
                        <label htmlFor={`platform-${platform}`} className="text-sm">
                          {platform}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Capabilities Filter */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Capabilities
                  </label>
                  <div className="mt-2 space-y-2">
                    {availableFilters.capabilities.map((capability) => (
                      <div key={capability} className="flex items-center space-x-2">
                        <Checkbox
                          id={`capability-${capability}`}
                          checked={filters.capabilities.includes(capability)}
                          onCheckedChange={(checked) => 
                            handleFilterChange('capabilities', capability, checked as boolean)
                          }
                        />
                        <label htmlFor={`capability-${capability}`} className="text-sm capitalize">
                          {capability}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </PopoverContent>
          </Popover>

          {/* Sort Controls */}
          <div className="flex items-center gap-2">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="status">Status</SelectItem>
                <SelectItem value="platform">Platform</SelectItem>
                <SelectItem value="lastSeen">Last Seen</SelectItem>
                <SelectItem value="performance">Performance</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleSortOrderToggle}
            >
              {sortOrder === 'asc' ? (
                <SortAsc className="h-4 w-4" />
              ) : (
                <SortDesc className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Active filters and results */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {/* Active filter badges */}
          {Object.entries(filters).map(([category, values]) =>
            values.map((value) => (
              <Badge key={`${category}-${value}`} variant="secondary" className="text-xs">
                {category}: {value}
                <button
                  onClick={() => handleFilterChange(category as keyof FilterOptions, value, false)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))
          )}
        </div>
        
        <Badge variant="outline">
          {resultCount} result{resultCount !== 1 ? 's' : ''}
        </Badge>
      </div>
    </div>
  );
}
