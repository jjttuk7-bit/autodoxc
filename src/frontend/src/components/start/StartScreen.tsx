import { useRef, useState } from "react";
import { Paperclip, Send, Sparkles, X } from "lucide-react";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

const ACCEPT = ".docx,.pdf,.txt,.md";
const MAX_MB = 10;

const EXAMPLES = [
  "외국인 고용 계획서 써야 해. 항공우주 부품 제조업체에서 5축 가공 기술자 1명.",
  "내용증명 보내려고 해. 임차인이 6개월간 임대료 미납.",
  "행정심판 청구서 — 영업정지 처분 이의 신청.",
] as const;

export default function StartScreen() {
  const { startSession, error } = useSession();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const trimmed = text.trim();
  // 첨부가 있으면 텍스트 없이도 시작 가능 (양식이 골격이 됨)
  const canSubmit = trimmed.length > 0 || file !== null;

  const pickFile = (f: File | null) => {
    setFileError(null);
    if (!f) {
      setFile(null);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setFileError(`파일이 너무 큽니다 (최대 ${MAX_MB}MB)`);
      return;
    }
    setFile(f);
  };

  const submit = () => {
    if (!canSubmit) return;
    void startSession(trimmed || "첨부한 양식으로 문서를 작성합니다.", file);
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
          placeholder="사건이나 상황을 자유롭게 말씀해 주세요. 양식 파일이 있으면 아래 '양식 첨부'로 올리면 그 구조가 골격이 됩니다."
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
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT}
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900 border border-gray-200 hover:border-gray-300 rounded px-2 py-1 transition-colors"
            >
              <Paperclip className="h-3 w-3" />
              양식 첨부
            </button>
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
          </div>
          <Button onClick={submit} disabled={!canSubmit}>
            <Send className="h-3 w-3" />
            시작
          </Button>
        </div>

        {file && (
          <div className="mt-2 inline-flex items-center gap-2 text-xs text-gray-600 bg-gray-100 border border-gray-200 rounded px-2 py-1">
            <Paperclip className="h-3 w-3 text-gray-400" />
            <span className="truncate max-w-xs">{file.name}</span>
            <button
              type="button"
              onClick={() => {
                pickFile(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              className="text-gray-400 hover:text-gray-700"
              aria-label="첨부 제거"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}

        {fileError && (
          <div className="mt-2 text-xs text-red-600">{fileError}</div>
        )}

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
