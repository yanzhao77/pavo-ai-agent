# Pavo AI Agent User Guide

> Version 2.0 | 2026-07-12

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Quick Start](#2-quick-start)
3. [Interface Guide](#3-interface-guide)
4. [Core Features](#4-core-features)
5. [Advanced Features](#5-advanced-features)
6. [FAQ](#6-faq)
7. [Best Practices](#7-best-practices)

---

## 1. Introduction

Pavo AI Agent is an AI-powered video storyboard generation platform. Users describe a story idea in natural language, and a coordinated pipeline of 7 specialized AI agents collaboratively generates:

- **Character Profiles** — name, age, appearance, personality, voice
- **Scene Designs** — environment, lighting, atmosphere, time of day
- **Prop Catalogs** — core props with appearance, interaction, narrative significance
- **Shot-by-shot Storyboards** — scene & shot breakdown with camera instructions
- **Video Generation** — convert storyboard prompts into AI-generated video (optional)

### Use Cases

- Short video content creation (TikTok, YouTube Shorts, Instagram Reels)
- Advertising creative & script planning
- Pre-production storyboarding for film & video
- Storyboard visualization for education
- Personal creative expression

---

## 2. Quick Start

### 2.1 Prerequisites

Make sure the system is running (see the README "Getting Started" section).

### 2.2 First Time Use

**Step 1: Login**

Open `http://localhost:3000` in your browser, enter any username to login. The system generates an auth token stored locally in your browser.

**Step 2: Enter a Story**

Type your story idea in the Chat Panel (left side) input box. For example:

> *A father comes home tired from work. His 5-year-old son brings him a wooden foot basin and carefully washes his feet.*

Press the send button or hit Enter.

**Step 3: Watch Agents Work**

The chat panel shows real-time progress of all 7 agents:

```
[Planner] Analyzing story... ✓
[Character] Generating characters... ✓
[Scene] Generating scenes... ✓
[Prop] Generating props... ✓
[Storyboard] Generating storyboard... ✓
[Reviewer] Reviewing quality... ✓
[Fixer] Fixing issues... ✓
```

The preview panel updates as each step completes.

**Step 4: View Results**

When generation finishes (10-30 seconds), the preview panel shows the complete storyboard across multiple tabs:

- **Storyboard** — Scene-by-scene, shot-by-shot view
- **Characters** — 2-4 generated character profiles
- **Scenes** — 2-4 scene designs
- **Props** — Core props list

### 2.3 Example Stories

| Genre | Sample Input |
|-------|-------------|
| Family | A father comes home tired from work. His 5-year-old son brings him a foot basin and washes his feet |
| Mystery | Midnight at the library. An old book opens by itself, and a shadow steps out of it |
| Healing | A rainy caf&eacute;, a stray cat pushes the door open and sits on the only empty seat |
| Inspirational | 5 AM, an old man shoots baskets alone in an empty gymnasium |

---

## 3. Interface Guide

### 3.1 Layout

```
+------------------+----------------------------------+
|   Chat Panel     |         Preview Panel            |
|                  |                                  |
|  [Story Input]   |  [Storyboard] [Characters]       |
|                  |   [Scenes] [Props]               |
|  Agent Progress  |                                  |
|  ✓ Planner       |  Scene 1: Act 1 - Homecoming    |
|  ✓ Character     |  +--------------------------+   |
|  ✓ Scene         |  | Shot 1: Medium | Static   |   |
|  ...             |  | Father opens door...      |   |
|                  |  +--------------------------+   |
|                  |  | Shot 2: Close | Push in   |   |
|                  |  | Son carries basin...      |   |
|                  |  +--------------------------+   |
+------------------+----------------------------------+
```

### 3.2 Chat Panel (Left)

- **Input Box** — Type story ideas, press Enter to send
- **Agent Log** — Real-time agent execution status
- **Loading State** — Animation during generation

### 3.3 Preview Panel (Right)

Four tabs available:

**Storyboard Tab**
- Organized by scenes (Acts), each scene contains multiple shots
- Each shot shows: number, type, camera move, angle, description, dialogue, duration, characters
- Drag & drop to reorder shots

**Characters Tab**
- Each character shown as a card
- Includes: name, role, age, appearance, personality, voice, relationships

**Scenes Tab**
- Each scene shown as a card
- Includes: name, time of day, environment, lighting, atmosphere

**Props Tab**
- Each prop shown as a card
- Includes: name, type, appearance, interaction, significance

---

## 4. Core Features

### 4.1 Story Input

The system accepts natural language descriptions of any length. Good inputs typically include:

- **Core characters** — Who is in the story?
- **Core event** — What happens?
- **Scene hints** — Where does it take place?
- **Emotional tone** — Warm, suspenseful, touching?

### 4.2 Agent Pipeline

The system uses 7 specialized AI agents working in sequence:

| Phase | Agent | Output | Description |
|-------|-------|--------|-------------|
| 1 | Planner | Story Analysis | Extract theme, emotions, elements, duration |
| 2 | Character | Profiles | Generate 2-4 characters from story analysis |
| 3 | Scene | Designs | Generate 2-4 scenes based on characters & story |
| 4 | Prop | Catalog | Identify and design core props |
| 5 | Storyboard | Shots | Complete shot-by-shot script |
| 6 | Reviewer | Quality Report | Check consistency and completeness |
| 7 | Fixer | Corrections | Auto-fix identified issues |

### 4.3 Storyboard Structure

Follows the Chinese classical **Qi-Cheng-Zhuan-He** narrative structure:

- **3-4 acts** with natural progression
- **30-60 seconds** total duration (ideal for short video)
- **Each scene has BGM and SFX** text descriptions
- **Each shot specifies**:
  - Shot Type: Wide / Full / Medium / Medium-Close / Close / Extreme Close
  - Camera Move: Static / Track / Push In / Pull Out / Pan-Tilt / Follow
  - Camera Angle: Eye-level / Slight High Angle / Profile
  - Description, dialogue, duration, characters

### 4.4 Export

Three export formats available:

- **Markdown** — For documentation & sharing
- **Plain Text** — For copying to other tools
- **PDF** — For printing & formal delivery

Export from the storyboard preview page.

---

## 5. Advanced Features

### 5.1 Regenerate Module

Regenerate specific modules individually if you are not satisfied:

```bash
POST /api/projects/{projectId}/regenerate
{
  "module": "characters"  // options: characters, scenes, storyboard
}
```

### 5.2 Version History

Each significant change creates a version snapshot. You can:

- **List versions** — Browse all historical versions
- **Restore any version** — One-click rollback

### 5.3 Video Generation

After storyboard generation, trigger video rendering:

1. Click "Generate Video"
2. System constructs video prompts for each shot
3. Calls Agnes AI video model per shot
4. Generated videos stored in MinIO

> **Note**: Video generation requires API key with video model access and takes longer.

### 5.4 Manual Editing

The preview panel supports:

- Drag & drop shots to reorder
- Direct field editing (coming soon)

---


---

## 5. MCP Client Integration (v2.3 New)

### 5.1 Available Tools (12)

| Tool | Description |
|------|-------------|
| pavo_create_project | Create project & start pipeline |
| pavo_get_project | Get project data |
| pavo_list_projects | List projects |
| pavo_generate_storyboard | Regenerate module |
| pavo_save_memory | Save user preferences |
| pavo_search_memory | Search memories |
| pavo_list_memories | List all memories |
| pavo_delete_memory | Delete memory |

### 5.2 Workflow Visualization

The pipeline graph shows 7 agents with color-coded status: green (completed), blue (running), red (failed). Click any node to see details. Timeline at bottom shows duration proportions.
## 6. FAQ

### Q: The storyboard is not detailed enough?

A: Provide more detailed story descriptions including appearance details, scene specifics, emotional changes. Use "regenerate" for specific modules.

### Q: How is character consistency maintained?

A: Each character has a `consistencyKey` field (appearance summary) that is automatically prepended to all subsequent prompts.

### Q: How long can the script be?

A: Default is 30-60 seconds. Specify longer duration in your input, e.g., "This is a 3-minute story".

### Q: Video generation failed?

A: Check API key video model permissions, verify MinIO is running. Try regenerating individual shots.

### Q: How do I share my project?

A: Use the Export function for Markdown or PDF output.

---

## 7. Best Practices

### 7.1 Input Tips

- **Be specific**: "a little girl in a red dress" > "a little girl"
- **Include emotional cues**: "tired but warm" guides the AI better than pure action
- **Set the scene**: "a rainy bus stop" is richer than "a place"
- **Specify length**: include duration hints if needed

### 7.2 Iteration Workflow

1. **First draft** — Input core story, get initial storyboard
2. **Review & adjust** — Note areas for improvement
3. **Module regeneration** — Regenerate specific modules
4. **Export & deliver** — Export to Markdown or PDF

### 7.3 Recommendations

- Start with simple stories (1-2 characters, 1-2 scenes)
- Progress to complex stories once familiar
- Use version history to experiment freely
- Build a storyboard library using exports

---

> For more details, see the [Technical Documentation](technical-documentation-en.md) or [用户指南（中文）](user-guide.md)
