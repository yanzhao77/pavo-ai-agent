"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Clock } from "lucide-react";

interface SortableShotProps {
  id: string;
  shotNumber: number;
  shotType: string;
  characters: string[];
  description: string;
  duration: string;
  onDurationChange: (id: string, newDuration: string) => void;
}

export function SortableShot({
  id, shotNumber, shotType, characters, description, duration, onDurationChange,
}: SortableShotProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const parseDuration = (d: string): number => {
    const match = d.match(/(d+)/);
    return match ? parseInt(match[1]) : 5;
  };

  const durSecs = parseDuration(duration);

  const handleDurationSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const secs = parseInt(e.target.value);
    const newDuration = duration.includes("-")
      ? `0-${secs}s`
      : `${secs}s`;
    onDurationChange(id, newDuration);
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white rounded-lg border border-gray-200 p-3 min-w-[200px] max-w-[220px] shrink-0 ${
        isDragging ? "shadow-lg" : "shadow-sm"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <button {...attributes} {...listeners} className="cursor-grab text-gray-400 hover:text-gray-600">
          <GripVertical className="w-4 h-4" />
        </button>
        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
          #{shotNumber}
        </span>
        <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{shotType}</span>
      </div>

      <p className="text-xs text-gray-500 line-clamp-2 mb-2">{description}</p>

      {characters.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {characters.map((c, i) => (
            <span key={i} className="text-[10px] bg-purple-50 text-purple-600 px-1 rounded">{c}</span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Clock className="w-3 h-3" />
        <span className="font-mono">{duration}</span>
        <input
          type="range"
          min="1"
          max="20"
          value={durSecs}
          onChange={handleDurationSlider}
          className="w-16 h-1 accent-blue-500"
          title="Adjust duration"
        />
        <span className="text-gray-400 w-6 text-right">{durSecs}s</span>
      </div>
    </div>
  );
}
