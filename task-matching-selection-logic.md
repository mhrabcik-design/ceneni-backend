# Task: Matching Selection Logic & UI

## Status
- [x] Analysis & Brainstorming (In progress)
- [x] Backend: Update `/match` API to return candidates for low scores
- [x] GAS: UI Implementation (Menu/Sidebar)
- [x] GAS: Selection Handling
- [x] Testing

## Goal
Implement a mechanism where items with low fuzzy match scores (< 40%) are not auto-priced, but instead offer the user a selection menu of potential candidates.

## Requirements
- If `match_score` < 0.4, return empty price in Sheets but provide Top 5 candidates.
- UI: A menu or sidebar section that appears on interaction.
- UI: Clicking a candidate fills the price, original name, and metadata (note).
- Cleanup: Normalization of names must be applied to these candidates as well.
