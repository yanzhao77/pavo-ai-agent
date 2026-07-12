"use client";

import { useState, useCallback } from "react";
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove, sortableKeyboardCoordinates, SortableContext, horizontalListSortingStrategy,
} from "@dnd-kit/sortable";
import { SortableShot } from "./SortableShot";
import { Save, ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import type { Project } from "@/types/project";

interface FlattenedShot {
  id: string;
  sceneIndex: number;
  shotIndex: number;
  shotNumber: number;
  shotType: string;
  characters: string[];
  description: string;
  duration: string;
}

interface TimelineProps {
  project: Project;
  onSave: (updatedStoryboard: any) => Promise<void>;
}

export function Timeline({ project, onSave }: TimelineProps) {
  const storyboard = project.storyboard;
  const [saving, setSaving] = useState(false);
  const [currentScene, setCurrentScene] = useState(0);

  if (!storyboard?.scenes?.length) {
    return (
      <div className="text-center text-gray-400 text-sm py-12">
        No storyboard generated yet
      </div>
    );
  }

  const scenes = storyboard.scenes;

  // Flatten shots for current scene
  const getShots = (): FlattenedShot[] => {
    const scene = scenes[currentScene];
    if (!scene?.shots) return [];
    return scene.shots.map((shot: any, idx: number) => ({
      id: `shot-${currentScene}-${idx}`,
      sceneIndex: currentScene,
      shotIndex: idx,
      shotNumber: shot.shotNumber || idx + 1,
      shotType: shot.shotType || "",
      characters: shot.characters || [],
      description: shot.description || "",
      duration: shot.duration || "5s",
    }));
  };

  const [shots, setShots] = useState<FlattenedShot[]>(getShots);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    setShots((prev) => {
      const oldIndex = prev.findIndex((s) => s.id === active.id);
      const newIndex = prev.findIndex((s) => s.id === over.id);
      return arrayMove(prev, oldIndex, newIndex);
    });
  };

  const handleDurationChange = (id: string, newDuration: string) => {
    setShots((prev) =>
      prev.map((s) => (s.id === id ? { ...s, duration: newDuration } : s))
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updatedScenes = scenes.map((scene: any, si: number) => {
        if (si !== currentScene) return scene;
        const sceneShots = shots.map((s, idx) => ({
          ...scene.shots[s.shotIndex],
          shotNumber: idx + 1,
          duration: s.duration,
        }));
        return { ...scene, shots: sceneShots };
      });
      await onSave({
        ...storyboard,
        scenes: updatedScenes,
      });
    } finally {
      setSaving(false);
    }
  };

  const shotIds = shots.map((s) => s.id);

  return (
    <div className="space-y-4">
      {/* Scene navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            const newIdx = Math.max(0, currentScene - 1);
            setCurrentScene(newIdx);
            const scene = scenes[newIdx];
            setShots(scene?.shots?.map((shot: any, idx: number) => ({
              id: `shot-${newIdx}-${idx}`,
              sceneIndex: newIdx, shotIndex: idx,
              shotNumber: shot.shotNumber || idx + 1,
              shotType: shot.shotType || "",
              characters: shot.characters || [],
              description: shot.description || "",
              duration: shot.duration || "5s",
            })) || []);
          }}
          disabled={currentScene === 0}
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-medium text-gray-700">
          {scenes[currentScene]?.title || "Scene " + (currentScene + 1)}
        </span>
        <span className="text-xs text-gray-400">({shots.length} shots)</span>
        <button
          onClick={() => {
            const newIdx = Math.min(scenes.length - 1, currentScene + 1);
            setCurrentScene(newIdx);
            const scene = scenes[newIdx];
            setShots(scene?.shots?.map((shot: any, idx: number) => ({
              id: `shot-${newIdx}-${idx}`,
              sceneIndex: newIdx, shotIndex: idx,
              shotNumber: shot.shotNumber || idx + 1,
              shotType: shot.shotType || "",
              characters: shot.characters || [],
              description: shot.description || "",
              duration: shot.duration || "5s",
            })) || []);
          }}
          disabled={currentScene >= scenes.length - 1}
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
        >
          <ArrowRight className="w-4 h-4" />
        </button>
        <div className="flex-1" />
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
          Save
        </button>
      </div>

      {/* Timeline */}
      <div className="overflow-x-auto pb-4">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={shotIds} strategy={horizontalListSortingStrategy}>
            <div className="flex gap-3 min-w-min px-1">
              {shots.map((shot) => (
                <SortableShot
                  key={shot.id}
                  id={shot.id}
                  shotNumber={shot.shotNumber}
                  shotType={shot.shotType}
                  characters={shot.characters}
                  description={shot.description}
                  duration={shot.duration}
                  onDurationChange={handleDurationChange}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      {/* Shot count summary */}
      <div className="text-xs text-gray-400 text-center">
        Drag shots to reorder • Use slider to adjust duration • Click Save to persist
      </div>
    </div>
  );
}
