import type { Section } from "../types";

export const sections: Section[] = [
  {
    id: "overview",
    title: "Overview",
    summary: "Frame the subject, audience, and decision this project supports.",
    body: [
      "Replace this starter content with the strongest available evidence and a clear statement of scope.",
      "Keep rendering components thin; put topic-specific structure and claims in this data module.",
    ],
  },
  {
    id: "analysis",
    title: "Analysis",
    summary: "Compare the important options, mechanisms, or trade-offs.",
    body: [
      "Use explicit criteria instead of broad feature lists. Separate verified facts from interpretation.",
      "Add new fields to the Section type only when the selected presentation genuinely requires them.",
    ],
  },
  {
    id: "conclusion",
    title: "Conclusion",
    summary: "State what the evidence supports and what remains unproved.",
    body: [
      "End with a bounded conclusion rather than a generic summary.",
      "If more work is needed, name the smallest artifact or test that would resolve the uncertainty.",
    ],
  },
];
