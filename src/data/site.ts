export const site = {
  meta: {
    title: "Fable Harness - Project-local operating layer for AI agents",
    description:
      "Fable Harness gives AI coding agents project-local memory, planning, verification, decision loops, parallel work discipline, and selective rollback.",
    url: "https://fable.aao.sh",
    image: "/assets/art/community-agent-assembly.webp",
    repoUrl: "https://github.com/aao-sh/fable-harness",
    licenseUrl: "https://github.com/aao-sh/fable-harness/blob/main/LICENSE",
  },
  sections: {
    why: { id: "why", label: "Why" },
    install: { id: "install", label: "Install" },
    workflows: { id: "workflows", label: "Workflows" },
    evidence: { id: "evidence", label: "Evidence" },
    community: { id: "community", label: "Community" },
    faq: { id: "faq", label: "FAQ" },
  },
  hero: {
    eyebrow: "The Trace Engine",
    title: "Fable Harness",
    description: "A system that teaches AI agents to organize memory context into traces and manageable notes.",
    promptCommand:
      "Install the Fable-Harness skill (https://github.com/aao-sh/fable-harness) and run it to set up this workspace.",
    primaryCta: "Install by prompt",
    secondaryCta: "GitHub repo",
    metrics: [
      { value: "Local", label: "context and memory stay in the workspace" },
      { value: "Traceable", label: "decisions become reviewable evidence" },
      { value: "Reversible", label: "rollback plans avoid broad resets" },
    ],
  },
  why: {
    kicker: "Why use it",
    title: "Stop asking agents to remember what the repo should prove.",
    intro:
      "Large agent tasks fall apart when context lives only in chat. Fable Harness turns the workspace itself into the working surface: decisions, notes, traces, checks, and rollback plans live beside the project.",
    problems: [
      "Chat-only memory disappears between sessions.",
      "Unsupported claims creep into progress reports.",
      "Plans drift away from files, tests, and evidence.",
      "Rollback requests become too broad or destructive.",
    ],
    solution:
      "Fable keeps the loop grounded: orient from local evidence, inspect before deciding, act in scoped steps, verify with commands, and report limits without pretending.",
  },
  workflows: [
    {
      slug: "memory",
      title: "Memory",
      mechanism: "Archive cylinder",
      description:
        "Compact semantic notes preserve durable project knowledge while traces remain audit evidence.",
      bestFor:
        "Remembering decisions, reloading context, searching prior work, and promoting trace evidence.",
    },
    {
      slug: "planning",
      title: "Planning",
      mechanism: "Drafting compass",
      description:
        "Plans start from instructions, notes, docs, source files, citations, and graph orientation.",
      bestFor:
        "Grounding work before implementation and interviewing the user only when local evidence is not enough.",
    },
    {
      slug: "decision-loop",
      title: "Decision Loop",
      mechanism: "Calibrated orrery",
      description:
        "Orient, inspect, decide, act, verify, and report with explicit closure checks.",
      bestFor:
        "Non-trivial or mutating work where hidden process state would be risky.",
    },
    {
      slug: "task-parallelism",
      title: "Task Parallelism",
      mechanism: "Split-drive governor",
      description:
        "Independent domains can move in waves while dependent loop steps stay ordered.",
      bestFor:
        "Complex work across separate files, domains, or responsibilities.",
    },
    {
      slug: "rollback",
      title: "Rollback",
      mechanism: "Reverse ratchet",
      description:
        "Selective rollback plans, checkpoints, backups, and reverse patches keep unrelated work intact.",
      bestFor:
        "Undoing a file, hunk, or agent change without erasing unrelated progress.",
    },
  ],
  evidence: {
    kicker: "Evidence loop",
    title: "A repeatable operating cycle for agent work.",
    phases: [
      {
        title: "Orient",
        detail: "Load instructions, memory notes, docs, repo facts, and current state.",
      },
      {
        title: "Inspect",
        detail: "Read the files and surfaces that can answer discoverable questions.",
      },
      {
        title: "Decide",
        detail: "Choose a scoped next move and record the reason when it matters.",
      },
      {
        title: "Act",
        detail: "Change only the relevant surface and preserve unrelated work.",
      },
      {
        title: "Verify",
        detail: "Run commands before claiming behavior, coverage, or completion.",
      },
      {
        title: "Report",
        detail: "Separate evidence, decisions, limits, and remaining risk.",
      },
    ],
  },
  install: {
    kicker: "Install",
    title: "Start with the prompt. Keep manual install close.",
    promptLabel: "Prompt install",
    manualLabel: "Manual fallback",
    manualNote:
      "Requires Python 3.9 or newer. The npm entry point launches the installer, but Python still runs under the hood.",
  },
  plugins: [
    {
      name: "Product Design",
      value:
        "Brief lock, visual alternatives, implementation from a selected direction, and UX/accessibility audit.",
    },
    {
      name: "Creative Production",
      value:
        "Mood boards, logo exploration, original steampunk art direction, and generative polish.",
    },
    {
      name: "Figma",
      value:
        "Componentized mockup, responsive layout review, design tokens, and handoff surfaces.",
    },
    {
      name: "Canva",
      value:
        "Optional derivative social cards or presentation material after the core site is done.",
    },
  ],
  community: {
    kicker: "Community",
    title: "Join the community and help build open source together.",
    links: [
      { label: "Discord", href: "https://discord.aao.sh", icon: "discord" },
      { label: "Telegram", href: "https://telegram.aao.sh", icon: "telegram" },
      { label: "GitHub", href: "https://github.com/aao-sh", icon: "github" },
      {
        label: "Organization",
        href: "https://aao.sh",
        icon: "organization",
        iconSrc: "/assets/brand/aao-icon-white.svg",
      },
    ],
  },
  faqs: [
    {
      question: "What does Fable Harness change?",
      answer:
        "It adds a project-local control layer for agent work: instructions, memory workflows, traces, plans, closure checks, and rollback discipline.",
    },
    {
      question: "Which agents does it support?",
      answer:
        "The README describes Codex, Claude Code, and compatible agents, with install targets for Codex, Claude, any AGENTS.md surface, both, or auto detection.",
    },
    {
      question: "Is Superpowers required?",
      answer:
        "The installer can skip Superpowers, but the README marks that path as not recommended. The strongest workflow uses both.",
    },
    {
      question: "How is project-local memory different from global memory?",
      answer:
        "Global memory can guide general preferences. Project-local memory stores decisions, traces, notes, and retrieval state inside the workspace where future agents can audit it.",
    },
  ],
};

export type Site = typeof site;
export type Workflow = (typeof site.workflows)[number];
