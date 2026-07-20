# GIN-21 — AI Residence Copilot: Designer Handoff & UI/UX Requirements

**Status**: CEO Product Direction — Ready for Designer Handoff
**Product**: AI Residence Copilot (GIN-12) — Vietnamese Rental Listing Analyzer
**Target**: v1.1 Ship → v2.0 Differentiation

---

## 1. Founder Read — What This Product Actually Is

**Core truth**: Vietnamese renters waste hours visiting listings that hide fees, fake addresses, scam signals, and commute mismatches. They paste a messy Zalo/Facebook/Chotot link into our tool and get an instant Vietnamese verdict: "Go see it / Ask more / Skip it" + a copy-paste message for the landlord.

**Real user**: 22-35, motorbike commuter, budget 3-15M VND/mo, browses listings on phone while on Xe Om or lunch break. Risk-averse about deposits. Speaks Vietnamese, thinks in VND.

**Painful problem**: Every listing omits 3-5 critical facts (electricity rate, water rate, parking, deposit terms, exact address). Visiting one bad listing costs 2 hours + 50k VND + mental fatigue. Scams cost millions.

**10-star version hiding inside**: Paste → instant verdict + landlord message → one-tap compare 3 listings → save to "My Shortlist" → share shortlist with roommate/partner → get notified when similar listings appear → community-verified "this landlord is legit" badge.

**Current reality**: Working MVP. Paste text → get analysis → save to localStorage history → compare view. Mobile responsive is barely functional. No share, no notifications, no community, no search. Deploy blocked (P0).

---

## 2. Selected Mode: SCOPE EXPANSION (v1.1) → SCOPE REDUCTION (v2.0 Strategy)

**v1.1 (this handoff): Scope Expansion on polish & trust**
- Fix mobile UX (P1 blocker for Vietnam mobile-first users)
- Copy questions button works reliably (P1 — core "aha" moment)
- Telemetry to learn what users actually do (P1 — we fly blind)
- Deploy to production (P0 — not real until live)
- **Designer scope**: Mobile-first polish, trust signals, copy polish, compare view usability

**v2.0 (next quarter): Scope Reduction to differentiated core**
- Kill: generic history sidebar, generic compare table
- Keep: Instant verdict, landlord message, hidden cost breakdown
- Add: Shareable shortlink, "Watch this area" alerts, Landlord reputation lookup
- **Designer scope later**: New IA, notification design, share flows, trust badge system

**Why this mode**: Current product works but feels like a dev tool. Vietnam renters need a consumer-grade mobile experience. We ship v1.1 polish NOW to unblock deploy + learn. Then we cut scope ruthlessly for v2.0 differentiation.

---

## 3. Product Direction — What We Build

### v1.1 (Designer Handoff Scope — 2 weeks)

| Area | Decision | Rationale |
|------|----------|-----------|
| **Mobile-first layout** | Single-column, thumb-friendly, bottom-sheet history, sticky CTA | 85%+ traffic mobile in VN |
| **Analysis result** | Card-based, scannable, verdict badge prominent, cost estimate sticky | Decision in <5 sec |
| **Copy questions** | One-tap, toast confirmation, haptic feedback | Core viral loop — "send this to landlord" |
| **Compare view** | Horizontal swipe cards on mobile, table on desktop | Compare 2-3 listings side-by-side |
| **Trust signals** | "AI analyzed 47 data points", "Verified price range for Quận 4", disclaimer subtle but present | Combat "AI hallucination" skepticism |
| **Empty states** | Illustrative, actionable ("Paste your first listing") | Onboard without tutorial |
| **Loading state** | Skeleton cards with shimmer, progressive reveal | Perceived speed > actual speed |
| **Error states** | Vietnamese, actionable ("Thử dán link Chợ Tốt"), retry prominent | Reduce drop-off |

### v1.1 Non-Goals (Explicitly Out of Scope)
- User accounts / cloud sync
- Search / listing discovery
- Notifications / alerts
- Landlord reputation database
- Sharing / collaboration
- PWA / offline
- Dark/light theme toggle (dark-only brand is fine)

---

## 4. User Experience — What It Should Feel Like

| Moment | Feeling | How We Achieve It |
|--------|---------|-------------------|
| **Landing** | "This gets me" | Vietnamese headline, example listing pre-filled, one tap to analyze |
| **Pasting** | Effortless | Auto-detect URL vs text, smart paste from clipboard |
| **Analyzing** | "It's reading it like I would" | Streaming tokens, "Đang kiểm tra điện/nước...", "Đang tính đường đi..." |
| **Result** | Clarity + confidence | Big verdict badge, match score, hidden cost number bold |
| **Copy questions** | "Done, sent" | One tap → toast "Đã sao chép 5 câu hỏi" → open Zalo/Messenger |
| **Compare** | "Now I can decide" | Swipe between listings, differences highlighted |
| **History** | "My shortlist" | Bottom sheet, swipe to delete, long-press to compare |
| **Error** | "Okay, what now?" | Specific Vietnamese guidance, not "Error 500" |

---

## 5. What We Build — Product Components (v1.1)

### 5.1 Landing / Input Screen
- **Hero**: "Dán tin đăng thuê nhà. Nhận đánh giá nhanh bằng tiếng Việt."
- **Textarea**: Pre-filled with realistic VN listing example (placeholder)
- **Smart paste**: Detects Chợ Tốt / Facebook / Zalo links → offers to fetch (v1.1: just paste text)
- **Preferences accordion**: Budget, Workplace district, Max commute — collapsed by default
- **Primary CTA**: "Phân tích tin đăng" — full width, sticky on mobile scroll
- **Trust line**: "AI phân tích 47 chỉ số: giá, phí ẩn, đường đi, dấu hiệu lừa đảo" + subtle shield icon

### 5.2 Analysis Result — Mobile Card Stack (Top to Bottom)
1. **Verdict Header** (sticky top 100px on scroll)
   - Match score (big, 48px)
   - Verdict badge: "Nên đi xem" (green) / "Cần hỏi thêm" (amber) / "Nên bỏ qua" (red)
   - Risk level pill + Price reasonableness pill
2. **Summary** — 2-3 sentences, Vietnamese, scannable
3. **Hidden Cost Estimate** — bold number, "Ước tính thêm: 1.2Mđ/tháng" + expandable breakdown
4. **Pros / Cons / Missing Info** — 3-column cards (mobile: stacked accordions)
5. **Red Flags** — red-left-border list, max 4, each with 🔴 dot
6. **Questions for Landlord** — **COPY BUTTON PRIMARY** here, numbered list, copy all → toast
7. **Vietnamese Message** — copy button, styled as chat bubble preview
8. **Scoring Rationale** — expandable "Tại sao chấm điểm này?"
9. **Commute Check** — if preferences provided, shows "~25 phút xe máy giờ cao điểm"
10. **Disclaimer** — muted, small, "Chỉ hỗ trợ quyết định, không phải tư vấn pháp lý/tài chính"
11. **Save to History** — secondary button, shows "Đã lưu" state

### 5.3 History / Shortlist (Bottom Sheet on Mobile, Sidebar on Desktop)
- **Grouped**: Today / Yesterday / This Week / Older
- **Row**: Verdict badge + Score + Listing preview (60 chars) + Timestamp
- **Actions**: Tap → select (checkbox), Swipe left → delete, Long press → compare
- **Compare CTA**: Appears when 2+ selected — "So sánh (2)" sticky bottom
- **Empty state**: Illustration + "Chưa có tin đăng nào. Dán tin đầu tiên để bắt đầu."

### 5.4 Compare View
- **Mobile**: Horizontal swipe cards (snap), indicator dots, each card = full analysis condensed
- **Desktop**: Fixed-label table (current implementation, refine typography)
- **Rows**: Listing preview, Verdict+Score, Risk, Price, Hidden Cost, Red Flags (top 3), Summary, Questions (top 3), Commute, Timestamp
- **Sticky header**: "So sánh tin đăng (3)" + Close button

### 5.5 Loading / Streaming State
- Skeleton cards for each result section
- Progressive text: "Đang đọc tin đăng..." → "Đang kiểm tra giá điện/nước..." → "Đang tính thời gian di chuyển..." → "Đang soạn tin nhắn..."
- Cancel button visible

### 5.6 Error States
- **Network**: "Mất kết nối. Thử lại?" + retry button
- **Invalid input**: "Tin đăng quá ngắn. Cần ít nhất 20 ký tự." / "Link không hợp lệ."
- **API error**: "AI đang bận. Thử lại trong giây lát." + retry
- **Rate limit**: "Quá nhiều yêu cầu. Đợi 30 giây." + countdown

---

## 6. What We Do NOT Build (v1.1 Boundaries)

| Feature | Reason | v2.0? |
|---------|--------|-------|
| User accounts / cloud sync | Infra cost, auth complexity, not core value | Maybe |
| Listing search / discovery | Different product, SEO play | No |
| Push notifications / email alerts | Needs backend, user identity | Yes (v2.0) |
| Landlord reputation DB | Data moat, legal risk, later | Yes (v2.0) |
| Share to friend / roommate | Needs link generation, no auth | Yes (v2.0) |
| PWA / offline | Nice-to-have, not blocker | Later |
| Light mode | Brand is dark, VN renters use dark at night | Never |
| Multi-language | Vietnamese only for v1 | Maybe (expat) |
| PDF export | Low value, copy-paste works | No |
| Favorites / tags | Over-engineering for MVP | No |

---

## 7. Success Definition (v1.1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deploy to production** | Done | Vercel URL live, HTTPS, custom domain |
| **Mobile usability** | Lighthouse Mobile ≥ 90 | Performance, Accessibility, Best Practices, SEO |
| **Copy questions success rate** | ≥ 60% of analyses | Telemetry event `copied_questions` / `analysis_complete` |
| **Compare usage** | ≥ 15% of sessions with ≥2 analyses | Telemetry `compare_opened` / `session` |
| **Return visit (7-day)** | ≥ 20% | LocalStorage history non-empty on return |
| **Error rate** | < 2% of analyses | Telemetry `analysis_error` / `analysis_requested` |
| **Vietnamese copy quality** | Zero English strings in result UI | Manual QA + telemetry `locale_mismatch` |

---

## 8. Risks & Tradeoffs

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mobile compare UX too cramped | High | High | Prototype swipe cards in Figma first, test on 375px width |
| Copy button fails on iOS Safari | Medium | High | Fallback `execCommand('copy')`, test on real device |
| Vietnamese copy feels robotic | Medium | High | Designer + native speaker review all strings |
| Streaming API adds complexity | Medium | Medium | Keep mock fallback, ship non-streaming v1.1 if needed |
| Deploy blocked by env/config | Low | Critical | Verify Vercel build + env vars before designer handoff |
| Scope creep from "nice-to-have" | High | Medium | CEO sign-off on this doc = scope freeze for v1.1 |

---

## 9. CEO Decision

**APPROVED WITH CHANGES**

- **v1.1 Scope**: Mobile-first polish, copy questions reliability, telemetry, deploy. **Designer handoff starts now.**
- **Designer delivers**: Figma file with 5 screens (Landing, Result Mobile, Result Desktop, Compare Mobile, History Bottom Sheet) + component library + design tokens + copy doc (VN/EN).
- **Engineering gates**: 
  1. Designer handoff complete → dev starts
  2. Dev complete → internal dogfood (VN team tests 10 real listings)
  3. Dogfood pass → deploy to production
  4. Production live → telemetry baseline → v2.0 planning

**Scope freeze**: No new features added to v1.1 after this doc. Bug fixes only.

---

## 10. CTO Handoff — Technical Planning Required

**Technical lead**: Lock these before dev starts:

1. **Mobile layout strategy**: CSS Grid/Flex vs CSS Container Queries for compare swipe cards. Recommend: `overflow-x: auto` + `scroll-snap` + `-webkit-overflow-scrolling: touch`.

2. **Copy-to-clipboard reliability**: Implement `Clipboard API` with `execCommand` fallback. Test iOS 15+, Android Chrome, Samsung Internet.

3. **Telemetry events schema** (add to `src/lib/telemetry.ts`):
   - `analysis_requested` { hasUrl, hasPrefs }
   - `analysis_complete` { provider, model, verdict, riskLevel, matchScore, latencyMs }
   - `analysis_error` { errorCode, stage }
   - `copied_questions` { count }
   - `copied_vietnamese_message` { }
   - `saved_to_history` { }
   - `compare_opened` { itemCount }
   - `history_item_deleted` { }
   - `history_cleared` { }
   - `preferences_toggled` { opened: boolean }

4. **Streaming vs non-streaming**: Current `/api/analyze` returns full JSON. For v1.1, keep non-streaming (simpler, reliable). Streaming = v2.0.

5. **Design token extraction**: Move all hardcoded colors/spacing/radii in `analyzer.tsx`, `history-sidebar.tsx`, `compare-view.tsx` → Tailwind config / CSS variables. Designer provides tokens; engineer implements.

6. **Vercel deploy checklist**: 
   - `OPENAI_API_KEY` in Vercel env
   - `NEXT_TELEMETRY_DISABLED=1`
   - Build passes `pnpm build` locally first
   - Custom domain `copilot.gin1111.dev` or similar

7. **Analytics endpoint**: Decide where telemetry posts (Vercel Analytics? PostHog? Custom `/api/telemetry`?). Recommend: lightweight `/api/telemetry` → log to file / ship to PostHog later.

**Deliverable from CTO**: Technical spec (1-pager) confirming above + effort estimate (story points) for each v1.1 component. Due before designer handoff review.

---

## Appendix: Current Component Inventory (For Designer Reference)

| Component | File | Current State | v1.1 Action |
|-----------|------|---------------|-------------|
| Analyzer (input + result) | `src/components/analyzer.tsx` | Works, desktop-first, inline styles | **Redesign**: Mobile-first card stack, streaming skeleton, trust signals, copy polish |
| History Sidebar | `src/components/history-sidebar.tsx` | Desktop sidebar, mobile bottom sheet (basic) | **Refine**: Better grouping, swipe delete, long-press compare, empty state illustration |
| Compare View | `src/components/compare-view.tsx` | Desktop table, mobile broken (overflow) | **Redesign**: Mobile swipe cards, desktop table polish |
| Telemetry | `src/lib/telemetry.ts` | Stub events, no transport | **Implement**: Event schema + `/api/telemetry` endpoint |
| API Analyze | `src/app/api/analyze/route.ts` | OpenAI + mock fallback, non-streaming | **Stabilize**: Error handling, rate limit, latency logging |
| Schema/Zod | `src/lib/schema.ts` | Complete, strict | **Freeze**: No changes v1.1 |
| Prompt | `src/lib/prompt.ts` | Few-shot, Vietnamese output | **Tune**: Designer + PM review output quality on 20 real listings |

---

**Next Action**: Designer starts Figma file from this spec. CTO writes 1-pager tech spec. PM (me) schedules dogfood session with VN team for week of deploy.

— CEO, Gin Corp