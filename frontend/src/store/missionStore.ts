import { create } from "zustand";
import type { Mission, Alert } from "../types";
import * as api from "../api/client";

interface MissionStore {
  missions: Mission[];
  alerts: Alert[];
  activeMission: Mission | null;
  loading: boolean;
  error: string | null;

  fetchMissions: (status?: string) => Promise<void>;
  fetchAlerts: (status?: string) => Promise<void>;
  setActiveMission: (m: Mission | null) => void;
  refreshMission: (id: number) => Promise<void>;
  addMission: (m: Mission) => void;
  updateMission: (m: Mission) => void;
}

export const useMissionStore = create<MissionStore>((set, get) => ({
  missions: [],
  alerts: [],
  activeMission: null,
  loading: false,
  error: null,

  fetchMissions: async (status) => {
    set({ loading: true, error: null });
    try {
      const missions = await api.listMissions(status);
      set({ missions, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  fetchAlerts: async (status) => {
    try {
      const alerts = await api.listAlerts(status);
      set({ alerts });
    } catch {
      /* silent */
    }
  },

  setActiveMission: (m) => set({ activeMission: m }),

  refreshMission: async (id) => {
    const m = await api.getMission(id);
    set((s) => ({
      activeMission: s.activeMission?.id === id ? m : s.activeMission,
      missions: s.missions.map((x) => (x.id === id ? m : x)),
    }));
  },

  addMission: (m) =>
    set((s) => ({ missions: [m, ...s.missions] })),

  updateMission: (m) =>
    set((s) => ({
      missions: s.missions.map((x) => (x.id === m.id ? m : x)),
      activeMission: s.activeMission?.id === m.id ? m : s.activeMission,
    })),
}));
