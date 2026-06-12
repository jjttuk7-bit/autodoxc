import { useState } from "react";
import { ChevronRight, X } from "lucide-react";
import { useSession } from "../../state/session-store";
import { Button } from "../ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

export default function SidePanel() {
  const [open, setOpen] = useState(false);
  const { skeleton } = useSession();

  if (!open) {
    return (
      <Button
        variant="outline"
        size="sm"
        className="self-start mt-4 mx-1"
        onClick={() => setOpen(true)}
      >
        <ChevronRight className="h-3 w-3" />
        근거·골격
      </Button>
    );
  }

  return (
    <aside className="w-[380px] border-l border-gray-200 bg-white flex flex-col">
      <Tabs defaultValue="skeleton" className="flex flex-col flex-1">
        <div className="flex items-center justify-between border-b border-gray-200">
          <TabsList className="border-b-0">
            <TabsTrigger value="evidence">근거</TabsTrigger>
            <TabsTrigger value="skeleton">골격</TabsTrigger>
            <TabsTrigger value="library">라이브러리</TabsTrigger>
          </TabsList>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 mr-2"
            onClick={() => setOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 text-sm">
          <TabsContent value="evidence">
            <div className="text-gray-400 italic">
              수집된 근거가 여기 표시됩니다. (데모에서는 비활성)
            </div>
          </TabsContent>

          <TabsContent value="skeleton">
            <ul className="space-y-1">
              {skeleton.length === 0 && (
                <li className="text-gray-400 italic">아직 골격이 없습니다.</li>
              )}
              {skeleton.map((s) => (
                <li
                  key={s.id}
                  className="px-2 py-1 rounded hover:bg-gray-50 text-gray-700"
                >
                  {s.title}
                  <div className="text-xs text-gray-400 mt-0.5">{s.role}</div>
                </li>
              ))}
            </ul>
          </TabsContent>

          <TabsContent value="library">
            <div className="text-gray-400 italic">
              개인 라이브러리. DA2 연동 후 활성화.
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </aside>
  );
}
