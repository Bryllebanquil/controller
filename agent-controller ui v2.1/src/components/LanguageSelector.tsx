import React, { useState, useEffect } from 'react';
import { localizationService } from '../utils/localization';
import { Globe } from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

interface LanguageSelectorProps {
  className?: string;
}

export function LanguageSelector({ className }: LanguageSelectorProps) {
  const [currentLanguage, setCurrentLanguage] = useState(localizationService.getCurrentLanguage());
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);

  useEffect(() => {
    setAvailableLanguages(localizationService.getAvailableLanguages());
  }, []);

  const handleLanguageChange = (language: string) => {
    localizationService.setLanguage(language);
    setCurrentLanguage(language);
    
    // Dispatch custom event so components can re-render
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language } }));
  };

  const getLanguageName = (code: string): string => {
    const names: { [key: string]: string } = {
      en: 'English',
      es: 'Español',
      fr: 'Français',
      de: 'Deutsch',
      zh: '中文',
      ja: '日本語',
      ru: 'Русский',
      pt: 'Português',
      it: 'Italiano',
      ko: '한국어'
    };
    return names[code] || code;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className={className}>
          <Globe className="h-4 w-4 mr-2" />
          {getLanguageName(currentLanguage)}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {availableLanguages.map((language) => (
          <DropdownMenuItem
            key={language}
            onClick={() => handleLanguageChange(language)}
            className={language === currentLanguage ? 'font-semibold' : ''}
          >
            {getLanguageName(language)}
            {language === currentLanguage && (
              <span className="ml-auto text-primary">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Hook for components to listen to language changes
export const useLanguage = () => {
  const [language, setLanguage] = useState(localizationService.getCurrentLanguage());

  useEffect(() => {
    const handleLanguageChange = (event: CustomEvent) => {
      setLanguage(event.detail.language);
    };

    window.addEventListener('languageChanged', handleLanguageChange as EventListener);
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange as EventListener);
    };
  }, []);

  return {
    language,
    setLanguage: (newLanguage: string) => {
      localizationService.setLanguage(newLanguage);
      window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: newLanguage } }));
    }
  };
};