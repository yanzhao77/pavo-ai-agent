import type { Shot, Character } from '@/types/project';

const EMOJI_MAP: Record<string, string> = {
  male: '🧑', female: '👩', child: '🧒', elderly: '👴', elderly_f: '👵',
};
const DEFAULT_EMOJI = '🧑';

const MOOD_GRADIENTS: Record<string, string> = {
  lonely: 'linear-gradient(135deg, #1a1a2e, #16213e)',
  romantic: 'linear-gradient(135deg, #2d1b69, #11998e)',
  happy: 'linear-gradient(135deg, #f093fb, #f5576c)',
  sad: 'linear-gradient(135deg, #2c3e50, #3498db)',
  peaceful: 'linear-gradient(135deg, #a8edea, #fed6e3)',
  tense: 'linear-gradient(135deg, #232526, #414345)',
  warm: 'linear-gradient(135deg, #f12711, #f5af19)',
  dark: 'linear-gradient(135deg, #0f0c29, #302b63)',
};
const DEFAULT_GRADIENT = 'linear-gradient(135deg, #667eea, #764ba2)';

export const generateCharacterAvatar = (
  name: string,
  traits?: string[]
): { emoji: string; bgGradient: string } => {
  const gender = traits?.find((t) => ['male', 'female', 'child', 'elderly'].includes(t));
  const emoji = EMOJI_MAP[gender || ''] || DEFAULT_EMOJI;
  const idx = [...(name || '')].reduce((s, c) => s + c.charCodeAt(0), 0);
  const gradients = Object.values(MOOD_GRADIENTS);
  const bgGradient = gradients[idx % gradients.length];
  return { emoji, bgGradient };
};

export const generateSceneThumbnail = (
  mood = '',
  setting = ''
): { gradient: string; tags: string[] } => {
  const key = Object.keys(MOOD_GRADIENTS).find((k) => mood.toLowerCase().includes(k));
  return {
    gradient: key ? MOOD_GRADIENTS[key] : DEFAULT_GRADIENT,
    tags: [mood, setting].filter(Boolean),
  };
};

export const generateProjectCover = (
  storyboard: Shot[],
  _characters?: Character[]
): { colorPalette: string[]; composition: string } => {
  if (!storyboard?.length) {
    return { colorPalette: ['#6366f1', '#111111'], composition: '默认抽象构图' };
  }
  const firstShot = storyboard[0];
  const mood = firstShot.description?.toLowerCase() || '';
  if (mood.includes('night') || mood.includes('dark')) {
    return { colorPalette: ['#0f0c29', '#302b63', '#24243e'], composition: '暗调叙事' };
  }
  if (mood.includes('warm') || mood.includes('sun')) {
    return { colorPalette: ['#f12711', '#f5af19'], composition: '暖调叙事' };
  }
  return { colorPalette: ['#6366f1', '#8b5cf6', '#111111'], composition: '中性叙事' };
};
