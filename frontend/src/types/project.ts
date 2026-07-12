export interface Project {
  id: string;
  userId?: string;
  title?: string;
  status: "draft" | "generating" | "completed";
  input?: string;
  characters?: Character[];
  scenes?: Scene[];
  props?: Prop[];
  storyboard?: Storyboard | null;
  videos?: any[];
  traceLog?: TraceEntry[];
  createdAt?: string;
  updatedAt?: string;
}

export interface Character {
  name: string;
  role: string;
  age: string;
  appearance: { build: string; face: string; eyes: string; hair: string; clothing: string; distinctive: string; };
  personality: string[];
  voice?: string;
  relationship?: string;
  consistencyKey: string;
}

export interface Scene {
  name: string;
  timeOfDay: string;
  environment: { type: string; style: string; size: string; furniture: string[]; decor: string[]; flooring: string; };
  lighting: { type: string; color: string; mood: string; };
  atmosphere: string;
}

export interface Prop {
  name: string;
  type: string;
  appearance: string;
  interaction: string;
  significance: string;
}

export interface Storyboard {
  projectName: string;
  globalBGM: string;
  scenes: StoryboardScene[];
}

export interface StoryboardScene {
  title: string;
  duration: string;
  mood: string;
  music: string;
  keyframe: string;
  shots: Shot[];
}

export interface Shot {
  shotNumber: number;
  shotType: string;
  cameraMove: string;
  cameraAngle: string;
  description: string;
  dialogue: string;
  duration: string;
  characters: string[];
}

export interface TraceEntry {
  agent: string;
  action: string;
  status: string;
  timestamp: string;
}
