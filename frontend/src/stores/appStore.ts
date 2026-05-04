import { create } from "zustand";
import type { App } from "@/types/app";

interface AppState {
  currentApp: App | null;
  apps: App[];
  isCreating: boolean;

  setCurrentApp: (app: App | null) => void;
  setApps: (apps: App[]) => void;
  setIsCreating: (isCreating: boolean) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentApp: null,
  apps: [],
  isCreating: false,

  setCurrentApp: (app) => set({ currentApp: app }),
  setApps: (apps) => set({ apps }),
  setIsCreating: (isCreating) => set({ isCreating }),
  reset: () => set({ currentApp: null, apps: [], isCreating: false }),
}));
