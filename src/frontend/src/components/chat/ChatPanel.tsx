import { ChevronDown, SkipForward } from "lucide-react";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../ui/collapsible";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";

export default function ChatPanel() {
  const { systemMessages, pendingQuestion, submitAnswer } = useSession();

  const q = pendingQuestion?.question;

  return (
    <aside className="w-[360px] border-r border-gray-200 bg-white flex flex-col">
      <div className="px-4 py-2 border-b border-gray-200 text-sm font-medium text-gray-600">
        대화
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
        {systemMessages.map((m, i) => (
          <div
            key={i}
            className="text-xs text-gray-500 bg-gray-50 rounded px-2 py-1"
          >
            {m}
          </div>
        ))}

        {q && (
          <div className="border-l-4 border-amber-400 bg-amber-50 rounded-r p-3 space-y-2">
            <div className="text-xs text-amber-700 font-medium">
              한 가지만 확인할게요
            </div>
            <div className="text-gray-900">{q.prompt}</div>
            <Collapsible>
              <CollapsibleTrigger className="text-xs text-gray-500 hover:text-gray-700 inline-flex items-center gap-1">
                <ChevronDown className="h-3 w-3" />
                왜 묻나요?
              </CollapsibleTrigger>
              <CollapsibleContent className="text-xs text-gray-500 mt-1 leading-relaxed">
                {q.why}
              </CollapsibleContent>
            </Collapsible>
            <div className="flex gap-2 pt-1">
              <Input
                placeholder="답변 입력…"
                className="h-7 text-xs"
                onKeyDown={(e) => {
                  const value = e.currentTarget.value.trim();
                  if (e.key === "Enter" && value) {
                    e.preventDefault();
                    void submitAnswer(value, false);
                    e.currentTarget.value = "";
                  }
                }}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => void submitAnswer("", true)}
              >
                <SkipForward className="h-3 w-3" />
                건너뜀
              </Button>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 p-3">
        <Textarea
          placeholder="사실관계나 추가 정보를 자유롭게 입력하세요…"
          rows={3}
          className="text-sm resize-none"
        />
      </div>
    </aside>
  );
}
