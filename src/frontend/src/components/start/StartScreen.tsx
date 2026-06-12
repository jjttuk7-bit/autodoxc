import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

const EXAMPLES = [
  "외국인 고용 계획서 써야 해. 항공우주 부품 제조업체에서 5축 가공 기술자 1명.",
  "내용증명 보내려고 해. 임차인이 6개월간 임대료 미납.",
  "행정심판 청구서 — 영업정지 처분 이의 신청.",
] as const;

export default function StartScreen() {
  const { startSession, error } = useSession();
  const [text, setText] = useState("");
  const trimmed = text.trim();

  const submit = () => {
    if (!trimmed) return;
    void startSession(trimmed);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 bg-gray-50">
      <div className="w-full max-w-2xl">
        <div className="flex items-center gap-2 text-gray-500 text-sm mb-4">
          <Sparkles className="h-4 w-4" />
          어떤 행정문서를 작성하시나요?
        </div>

        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="사건이나 상황을 자유롭게 말씀해 주세요. 양식 파일이 있으면 첨부해 주세요. (드래그앤드롭은 곧 지원)"
          rows={5}
          className="bg-white text-base resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              submit();
            }
          }}
          autoFocus
        />

        <div className="flex items-center justify-between mt-3">
          <div className="text-xs text-gray-400">
            <kbd className="px-1 py-0.5 bg-gray-100 rounded border border-gray-200">
              Ctrl
            </kbd>{" "}
            +{" "}
            <kbd className="px-1 py-0.5 bg-gray-100 rounded border border-gray-200">
              Enter
            </kbd>{" "}
            로 시작
          </div>
          <Button onClick={submit} disabled={!trimmed}>
            <Send className="h-3 w-3" />
            시작
          </Button>
        </div>

        <div className="mt-8 text-xs text-gray-500">
          <div className="mb-2 text-gray-400">예시</div>
          <div className="flex flex-col gap-1.5">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                className="text-left text-sm text-gray-600 hover:text-gray-900 bg-white border border-gray-200 hover:border-gray-300 rounded px-3 py-2 transition-colors"
                onClick={() => {
                  setText(ex);
                }}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
