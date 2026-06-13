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
      onClick={() => {
        if (isEditable) setEditing(true);
      }}
      title={isEditable ? "클릭하여 편집" : undefined}
    >
      {paragraph.text}
    </p>
  );
}
