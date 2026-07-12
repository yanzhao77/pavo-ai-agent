# -*- coding: utf-8 -*-
import os

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tech_doc_v2.md')

MARKDOWN = r"""# AI Video Generation Agent - Technical Development Document

> Based on Pavo AI platform analysis, built on Agnes AI Unified Model Gateway (https://apihub.agnes-ai.com/v1)
> Version: v2.0 | Date: 2026-07-12

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Core Module Design](#3-core-module-design)
4. [Data Model Design](#4-data-model-design)
5. [AI Prompt Engineering Strategy](#5-ai-prompt-engineering-strategy)
6. [Technology Stack](#6-technology-stack)
7. [API Design](#7-api-design)
8. [Security Guidelines](#8-security-guidelines)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Project Overview

### 1.1 Goal

Build an AI Agent system that automatically generates complete video projects from user story input.

### 1.2 Platform Dependency

All AI capabilities are accessed via the **Agnes AI Unified Model Gateway** (https://apihub.agnes-ai.com/v1) with a single API Key.

"""

def write_doc():
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(MARKDOWN)
    print(f"Written to {OUTPUT_PATH}")

if __name__ == '__main__':
    write_doc()
