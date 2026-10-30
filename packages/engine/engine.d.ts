export const UniversalUI: {
  version: string;
  currentTheme: string;
  presets: Record<string, Record<string, string>>;
  setTheme(themeName: string, customTokensObject?: Record<string, string>): string;
  getRegisteredComponents(): string[];
};

export const primitiveTags: string[];

export {};
