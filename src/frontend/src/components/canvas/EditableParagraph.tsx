import { useEffect, useRef, useState } from "react";
import { Check, X } from "lucide-react";
import type { DraftParagraph, ParagraphStatus } from "../../api/types";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";

interface Props {
  paragraph: DraftParagraph;
  onSave: (newText: string) => void;
}

function statusClass(s: ParagraphStatus): string {
  switch (s) {
    case "confirmed":
      return "text-gray-900";
    case "inferred":
      return "text-gray-900 bg-yellow-100 border-b border-dotted border-yellow-500";
    case "defaulted":
      return "text-gray-500";
    case "evidence_backed":
      return "text-gray-900 border-r-2 border-blue-500 pr-2";
    case "empty":
      return "text-gray-400 italic bg-gray-50 border border-dashed border-gray-300 rounded px-1";
  }
}

const EDITABLE_STATUSES: ReadonlySet<ParagraphStatus> = new Set<ParagraphStatus>(
  ["empty", "inferred", "defaulted"]
);

const PLACEHOLDER_REGEX = /\[\[([^\]]+)\]\]/g;

/** [[필드명]] 패턴을 시각 마크(작은 회색 박스)로 변환. 사용자가 텍스트 일부로
 *  오해하지 않게 — 행정문서에서 흔히 쓰는 괄호+밑줄 시안 채택. */
function renderWithPlaceholders(text: string) {
  const parts: Array<{ kind: "text" | "ph"; value: string }> = [];
  let lastIndex = 0;
  PLACEHOLDER_REGEX.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = PLACEHOLDER_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ kind: "text", value: text.slice(lastIndex, match.index) });
    }
    parts.push({ kind: "ph", value: match[1] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push({ kind: "text", value: text.slice(lastIndex) });
  }
  if (parts.length === 0) {
    return text;
  }
  return parts.map((part, i) => {
    if (part.kind === "ph") {
      return (
        <span
          key={i}
          className="inline-block px-2 py-0.5 mx-0.5 bg-amber-50 border border-amber-300 rounded text-amber-800 not-italic text-[0.85em] align-baseline font-medium"
          title="자리표시자 — 클릭하여 편집 후 채워주세요"
        >
          {part.value}
        </span>
      );
    }
    return <span key={i}>{part.value}</span>;
  });
}

/** 편집 진입 시 textarea value에서 자리표시자 마크만 제거 (속의 라벨 유지).
 *  예: "청구인: [[청구인 성명]] (주소: [[청구인 주소]])"
 *      → "청구인: 청구인 성명 (주소: 청구인 주소)" 로 시작 — 사용자가 라벨을 자기 데이터로 교체. */
function stripPlaceholderMarks(text: string): string {
  return text.replace(PLACEHOLDER_REGEX, (_m, label) => label);
}

export default function EditableParagraph({ paragraph, onSave }: Props) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(paragraph.text);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setValue(paragraph.text);
  }, [paragraph.text]);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [editing]);

  const status = paragraph.annotations.status;
  const isEditable = EDITABLE_STATUSES.has(status);

  const enterEdit = () => {
    if (!isEditable) return;
    // 편집 진입 시 자리표시자 마크 제거 — 사용자가 [[]] 보지 않고 채우게
    setValue(stripPlaceholderMarks(paragraph.text));
    setEditing(true);
  };

  if (editing) {
    return (
      <div className="my-1 border-2 border-blue-400 rounded p-1 bg-blue-50">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="border-0 bg-transparent focus-visible:ring-0 resize-none text-sm leading-relaxed"
          rows={2}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSave(value);
              setEditing(false);
            }
            if (e.key === "Escape") {
              e.preventDefault();
              setValue(paragraph.text);
              setEditing(false);
            }
          }}
        />
        <div className="flex items-center justify-between mt-1 px-1">
          <div className="text-[10px] text-gray-500">
            <kbd className="px-1 py-0.5 bg-white rounded border">Enter</kbd> 저장 ·{" "}
            <kbd className="px-1 py-0.5 bg-white rounded border">Esc</kbd> 취소 ·{" "}
            <kbd className="px-1 py-0.5 bg-white rounded border">Shift+Enter</kbd> 줄바꿈
          </div>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-6 px-2"
              onClick={() => {
                setValue(paragraph.text);
                setEditing(false);
              }}
            >
              <X className="h-3 w-3" />
            </Button>
            <Button
              size="sm"
              className="h-6 px-2"
              onClick={() => {
                onSave(value);
                setEditing(false);
              }}
            >
              <Check className="h-3 w-3" />
              저장
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <p
      className={`leading-relaxed py-1 ${statusClass(status)} ${
        isEditable
          ? "cursor-pointer hover:ring-1 hover:ring-blue-300 hover:ring-offset-1 rounded transition-shadow"
          : ""
      }`}
      onClick={enterEdit}
      title={isEditable ? "클릭하여 편집" : undefined}
    >
      {renderWithPlaceholders(paragraph.text)}
    </p>
  );
}
