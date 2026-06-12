import { create } from "zustand";
import type {
  AskUserEvent,
  DocType,
  DraftSection,
  SkeletonNode,
  StreamEvent,
} from "../api/types";
import { createSession, startSessionStream } from "../api/client";

type UIState = "idle" | "composing" | "drafting" | "editing" | "saved";

interface SessionStore {
  uiState: UIState;
  sessionId: string | null;
  docType: DocType | null;
  skeleton: SkeletonNode[];
  sections: Map<string, DraftSection>;
  pendingQuestion: AskUserEvent | null;
  systemMessages: string[];
  error: string | null;

  setUIState: (s: UIState) => void;
  setSkeleton: (docType: DocType, skel: SkeletonNode[]) => void;
  upsertSection: (s: DraftSection) => void;
  setPendingQuestion: (q: AskUserEvent | null) => void;
  pushSystem: (m: string) => void;
  startSession: (userInput: string) => Promise<void>;
  reset: () => void;
}

const initial = () => ({
  uiState: "idle" as UIState,
  sessionId: null,
  docType: null,
  skeleton: [],
  sections: new Map<string, DraftSection>(),
  pendingQuestion: null,
  systemMessages: [],
  error: null,
});

export const useSession = create<SessionStore>((set, get) => ({
  ...initial(),

  setUIState: (uiState) => set({ uiState }),
  setSkeleton: (docType, skeleton) => set({ docType, skeleton }),
  upsertSection: (s) =>
    set((state) => {
      const next = new Map(state.sections);
      next.set(s.skeleton_id, s);
      return { sections: next };
    }),
  setPendingQuestion: (pendingQuestion) => set({ pendingQuestion }),
  pushSystem: (m) =>
    set((state) => ({ systemMessages: [...state.systemMessages, m] })),
  reset: () => set(initial()),

  startSession: async (userInput) => {
    const { setSkeleton, upsertSection, setPendingQuestion, pushSystem } = get();
    set({
      ...initial(),
      uiState: "composing",
      systemMessages: [`입력 받음: ${userInput.slice(0, 40)}…`],
    });

    let sessionId: string;
    try {
      const created = await createSession(userInput);
      sessionId = created.session_id;
      set({ sessionId });
      pushSystem(`세션 생성: ${sessionId}`);
    } catch (e) {
      set({ uiState: "idle", error: `세션 생성 실패: ${String(e)}` });
      return;
    }

    const handler = (e: StreamEvent) => {
      switch (e.kind) {
        case "skeleton_ready":
          setSkeleton(e.doc_type, e.skeleton);
          set({ uiState: "drafting" });
          pushSystem(`문서 유형: ${e.doc_type.ko_name}`);
          break;
        case "draft_section":
          upsertSection(e.section);
          break;
        case "ask_user":
          setPendingQuestion(e);
          break;
        case "facts_extracted":
          pushSystem(
            `사실관계 ${e.fact_count}건 (미해결 ${e.unresolved_count})`
          );
          break;
        case "fills_applied":
          pushSystem(`자동 채움 ${e.fills_count}건`);
          break;
        case "editing_ready":
          set({ uiState: "editing" });
          pushSystem("초안 완료 — 편집 가능");
          break;
      }
    };

    try {
      await startSessionStream(sessionId, handler);
    } catch (e) {
      pushSystem(`스트림 오류: ${String(e)}`);
      set({ error: String(e) });
    }
  },
}));
