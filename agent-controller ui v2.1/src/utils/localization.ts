// Simple localization system for admin privilege indicator
// Supports multiple languages for badge text and ARIA labels

export interface TranslationKeys {
  admin_badge: string;
  user_badge: string;
  admin_aria_label: string;
  user_aria_label: string;
}

export interface Translations {
  [key: string]: TranslationKeys;
}

export const translations: Translations = {
  en: {
    admin_badge: "ADMIN",
    user_badge: "USER",
    admin_aria_label: "Administrator privileges",
    user_aria_label: "Standard user privileges"
  },
  es: {
    admin_badge: "Administrador",
    user_badge: "Usuario Estándar",
    admin_aria_label: "Privilegios de administrador",
    user_aria_label: "Privilegios de usuario estándar"
  },
  fr: {
    admin_badge: "Administrateur",
    user_badge: "Utilisateur Standard",
    admin_aria_label: "Privilèges d'administrateur",
    user_aria_label: "Privilèges d'utilisateur standard"
  },
  de: {
    admin_badge: "Administrator",
    user_badge: "Standardbenutzer",
    admin_aria_label: "Administratorrechte",
    user_aria_label: "Standardbenutzerrechte"
  },
  zh: {
    admin_badge: "管理员",
    user_badge: "标准用户",
    admin_aria_label: "管理员权限",
    user_aria_label: "标准用户权限"
  },
  ja: {
    admin_badge: "管理者",
    user_badge: "標準ユーザー",
    admin_aria_label: "管理者権限",
    user_aria_label: "標準ユーザー権限"
  },
  ru: {
    admin_badge: "Администратор",
    user_badge: "Стандартный пользователь",
    admin_aria_label: "Права администратора",
    user_aria_label: "Права стандартного пользователя"
  },
  pt: {
    admin_badge: "Administrador",
    user_badge: "Usuário Padrão",
    admin_aria_label: "Privilégios de administrador",
    user_aria_label: "Privilégios de usuário padrão"
  },
  it: {
    admin_badge: "Amministratore",
    user_badge: "Utente Standard",
    admin_aria_label: "Privilegi di amministratore",
    user_aria_label: "Privilegi di utente standard"
  },
  ko: {
    admin_badge: "관리자",
    user_badge: "표준 사용자",
    admin_aria_label: "관리자 권한",
    user_aria_label: "표준 사용자 권한"
  }
};

export class LocalizationService {
  private currentLanguage: string;
  private translations: Translations;

  constructor(translations: Translations, defaultLanguage: string = 'en') {
    this.translations = translations;
    this.currentLanguage = this.detectLanguage() || defaultLanguage;
  }

  private detectLanguage(): string | null {
    // Try to detect language from browser
    if (typeof navigator !== 'undefined') {
      const browserLang = navigator.language?.split('-')[0];
      if (browserLang && this.translations[browserLang]) {
        return browserLang;
      }
    }
    return null;
  }

  setLanguage(language: string): void {
    if (this.translations[language]) {
      this.currentLanguage = language;
    } else {
      console.warn(`Language '${language}' not available, falling back to English`);
      this.currentLanguage = 'en';
    }
  }

  getCurrentLanguage(): string {
    return this.currentLanguage;
  }

  t(key: keyof TranslationKeys): string {
    const translation = this.translations[this.currentLanguage];
    if (!translation) {
      console.warn(`No translation found for language '${this.currentLanguage}'`);
      return this.translations['en'][key]; // Fallback to English
    }
    
    const value = translation[key];
    if (!value) {
      console.warn(`Translation key '${key}' not found for language '${this.currentLanguage}'`);
      return this.translations['en'][key]; // Fallback to English
    }
    
    return value;
  }

  getAvailableLanguages(): string[] {
    return Object.keys(this.translations);
  }

  // Helper method to get badge text based on admin status
  getBadgeText(isAdmin: boolean): string {
    return isAdmin ? this.t('admin_badge') : this.t('user_badge');
  }

  // Helper method to get ARIA label based on admin status
  getAriaLabel(isAdmin: boolean, agentName: string): string {
    const privilegeText = isAdmin ? this.t('admin_aria_label') : this.t('user_aria_label');
    return `${privilegeText}: ${agentName}`;
  }
}

// Create singleton instance
export const localizationService = new LocalizationService(translations);

// Default export
export default localizationService;