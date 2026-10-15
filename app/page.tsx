"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDownUp, ArrowRight, ArrowUpRight, Bookmark, CalendarDays, Check, ChevronDown, Code2, Compass, ExternalLink, Info, LoaderCircle, MapPin, Plus, Radar, Search, SlidersHorizontal, Sparkles, Target, Upload, X, Zap } from "lucide-react";
import { api, Brief, DEFAULTS, Event, Interest, INTERESTS, Preferences, RankedEvent, SearchResult } from "@/lib/types";

const dateLabel = (date: string, options: Intl.DateTimeFormatOptions = { day: "numeric", month: "short" }) => new Intl.DateTimeFormat("en-GB", { ...options, timeZone: "Europe/London" }).format(new Date(date));
const provenance = (event: Event) => event.provenance === "example" ? "Example event" : event.provenance === "public_import" ? "Public page import" : "User import · unverified";

function Modal({ title, children, onClose, wide = false }: { title: string; children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { dialog?.close(); document.body.style.overflow = previous; };
  }, []);
  return <dialog ref={ref} className={wide ? "modal wide" : "modal"} onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }} aria-labelledby="modal-title">
    <div className="modal-heading"><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20} /></button></div>
    {children}
  </dialog>;
}

function EventCard({ item, index, saved, onSave, onOpen }: { item: RankedEvent; index: number; saved: boolean; onSave: () => void; onOpen: () => void }) {
  const { event, score } = item;
  return <article className="event-card" style={{ animationDelay: `${index * 55}ms` }}>
    <div className={`card-art art-${index % 4}`} aria-hidden="true"><div className="art-grid" /><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="art-orbit orbit-three" /><span className="art-code">{index % 4 === 0 ? <Code2 /> : index % 4 === 1 ? <Zap /> : index % 4 === 2 ? <Target /> : <Sparkles />}</span><span className="art-caption">{event.kind.toUpperCase()} / {event.city.toUpperCase()}</span></div>
    <div className="card-body">
      <div className="card-meta"><span className={`provenance ${event.provenance === "example" ? "example" : "imported"}`}><span />{provenance(event)}</span><button className={`icon-button save-button ${saved ? "is-saved" : ""}`} aria-label={`${saved ? "Unsave" : "Save"} ${event.title}`} aria-pressed={saved} onClick={onSave}><Bookmark size={18} fill={saved ? "currentColor" : "none"} /></button></div>
      <button className="card-title" onClick={onOpen}><h3>{event.title}</h3></button>
      <div className="event-meta"><span><CalendarDays size={14} />{dateLabel(event.start_at)}</span><span><MapPin size={14} />{event.city}</span><span>{event.cost}</span></div>
      <p className="event-description">{event.description}</p>
      <div className="tag-row">{event.tags.slice(0, 3).map(tag => <span className={score.matched_interests.includes(tag) ? "tag matched" : "tag"} key={tag}>{tag}</span>)}{!event.tags.length && <span className="tag">{event.kind}</span>}</div>
      <div className="card-bottom"><div className="score"><span className="score-number">{score.total.toFixed(1)}</span><div><span className="score-label">MATCH SCORE</span><span className="score-caption">{score.total >= 9 ? "Strong fit" : "Worth a look"} <Sparkles size={11} /></span></div></div><button className="details-button" onClick={onOpen}>View match <ArrowUpRight size={16} /></button></div>
    </div>
  </article>;
}

function EventDetails({ item, preferences, grok, onClose }: { item: RankedEvent; preferences: Preferences; grok: boolean; onClose: () => void }) {
  const { event, score } = item;
  const [brief, setBrief] = useState<Brief | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);
  async function prepare(useGrok: boolean) {
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    setBusy(true); setError("");
    try { setBrief(await api<Brief>(`events/${event.id}/brief`, { preferences, use_grok: useGrok }, controller.signal)); }
    catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <Modal title={event.title} onClose={onClose} wide>
    <div className="detail-content">
      <div className="detail-kicker"><span className={`provenance ${event.provenance === "example" ? "example" : "imported"}`}><span />{provenance(event)}</span><span>{event.kind} · {event.format.replace("_", " ")}</span></div>
      {event.provenance === "example" && <div className="notice"><Info size={17} /><span>This is a fictional demonstration. Its date moves with the demo. There is no real registration.</span></div>}
      <p className="detail-description">{event.description}</p>
      <div className="detail-facts"><div><CalendarDays size={17} /><span>{dateLabel(event.start_at, { weekday: "short", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" })}<small>Europe/London time</small></span></div><div><MapPin size={17} /><span>{event.venue}<small>{event.city} · {event.cost}</small></span></div></div>
      <section className="score-panel"><div className="section-heading"><div><span className="eyebrow">NO BLACK BOX</span><h3>Why this match?</h3></div><strong>{score.total.toFixed(1)}<span> / 10</span></strong></div>
        {score.dimensions.map(d => <div className="dimension" key={d.label}><div className="dimension-top"><b>{d.label}</b><span>{d.earned} / {d.possible}</span></div><div className="meter"><div style={{ width: `${d.earned / d.possible * 100}%` }} /></div><p>{d.evidence}</p></div>)}
        <p className="fine-print">{score.engine}. A relevance score based on supplied text, not a guarantee of quality, acceptance or availability.</p>
      </section>
      <section className="brief-section"><div className="section-heading"><div><span className="eyebrow">SHOW UP READY</span><h3>Your preparation brief</h3></div><Sparkles size={20} /></div><p>Turn a promising match into a plan. A Grok brief sends this listing and your selected preferences to xAI.</p>
        <div className="button-row"><button className="primary" disabled={busy} onClick={() => prepare(false)}>{busy ? <LoaderCircle className="spin" size={16} /> : <Code2 size={16} />}Generate local brief</button><button className="secondary" disabled={busy || !grok} onClick={() => prepare(true)}><Sparkles size={16} />{grok ? "Generate with Grok" : "Grok · not configured"}</button></div>
        {error && <p className="error" role="alert">{error}</p>}
        {brief && <div className="brief-result" aria-live="polite"><span className="small-label">{brief.provider === "grok" ? "GROK-GENERATED" : "LOCAL TEMPLATE"}</span><p>{brief.summary}</p><h4>Application starter</h4><blockquote>{brief.application_pitch}</blockquote><h4>Before you go</h4><ul>{brief.preparation.map(p => <li key={p}>{p}</li>)}</ul><p className="fine-print">{brief.notice}</p></div>}
      </section>
      <section className="sources"><h3>Source & provenance</h3><p>Organizer: {event.organizer}</p>{event.retrieved_at && <p>Retrieved {dateLabel(event.retrieved_at, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })} (London). Recheck the original page for changes.</p>}{event.provenance === "user_import" && <p>Supplied by a user. The event and its details have not been independently verified.</p>}
        {event.provenance !== "example" ? <><a className="primary link-button" href={event.url} target="_blank" rel="noreferrer noopener">Open original listing <ExternalLink size={15} /></a>{event.source_urls.filter(url => url !== event.url).map(url => <a className="source-link" href={url} target="_blank" rel="noreferrer noopener" key={url}>{url}<ExternalLink size={13} /></a>)}</> : <p className="fine-print">Created by HackRadar for this demo. No external listing.</p>}
      </section>
    </div>
  </Modal>;
}

function ImportModal({ onClose, onImported }: { onClose: () => void; onImported: () => void }) {
  const [mode, setMode] = useState<"url" | "json">("url");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMessage(""); setError("");
    try {
      const payload = mode === "url" ? { url: value.trim() } : JSON.parse(value);
      const result = await api<{ added: number; duplicates: number }>(`import/${mode}`, payload);
      setMessage(`${result.added} event${result.added === 1 ? "" : "s"} added · ${result.duplicates} duplicate${result.duplicates === 1 ? "" : "s"} merged. Your current filters still apply.`);
      onImported();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return <Modal title="Add to your radar" onClose={onClose}>
    <div className="import-content"><p>Bring in an event you found. We’ll check for duplicates and score it against your preferences.</p><div className="segmented"><button disabled={busy} className={mode === "url" ? "active" : ""} onClick={() => { setMode("url"); setValue(""); setError(""); setMessage(""); }}>Public event link</button><button disabled={busy} className={mode === "json" ? "active" : ""} onClick={() => { setMode("json"); setValue(""); setError(""); setMessage(""); }}>JSON import</button></div>
      <form onSubmit={submit}><label className="field-label" htmlFor="import-value">{mode === "url" ? "Event URL" : "Event JSON"}</label>{mode === "url" ? <input id="import-value" type="url" required placeholder="https://lu.ma/your-event" value={value} onChange={e => setValue(e.target.value)} /> : <textarea id="import-value" required rows={11} spellCheck={false} placeholder={'{"events": [{\n  "title": "Your event title",\n  "description": "Describe the event and its themes",\n  "start_at": "2026-11-01T10:00:00+00:00",\n  "city": "London",\n  "url": "https://your-organizer.org/event",\n  "tags": ["AI Agents"],\n  "kind": "hackathon"\n}]}'} value={value} onChange={e => setValue(e.target.value)} />}
        <p className="fine-print">{mode === "url" ? "Supports publicly accessible Event JSON-LD on Luma, Eventbrite and MLH. Respects robots rules. Some pages block access or lack structured data; those cannot be imported." : "Use an authorized export. Up to 100 events, with timezone-aware dates. User imports are labeled unverified; they are never presented as retrieved facts."}</p>
        <button className="primary full" disabled={busy || !value.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <Upload size={16} />}{busy ? "Reading source…" : "Import & deduplicate"}</button>
      </form>{message && <p className="success" role="status"><Check size={16} />{message}</p>}{error && <p className="error" role="alert">{error}</p>}
    </div>
  </Modal>;
}

export default function Home() {
  const [preferences, setPreferences] = useState<Preferences>(DEFAULTS);
  const [draft, setDraft] = useState<Preferences>(DEFAULTS);
  const [ready, setReady] = useState(false);
  const [saved, setSaved] = useState<string[]>([]);
  const [tab, setTab] = useState<"discover" | "saved">("discover");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("score");
  const [data, setData] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<RankedEvent | null>(null);
  const [modal, setModal] = useState<"import" | "method" | null>(null);
  const [grok, setGrok] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem("hackradar-preferences-v1") || "null");
      if (stored && typeof stored.city === "string" && stored.city.trim() && stored.city.length <= 80 && Array.isArray(stored.interests) && stored.interests.length > 0 && stored.interests.every((v: Interest) => INTERESTS.includes(v)) && [7, 14, 30, 60, 90].includes(stored.days) && typeof stored.min_score === "number" && stored.min_score >= 0 && stored.min_score <= 10 && typeof stored.include_examples === "boolean" && typeof stored.include_online === "boolean") { setPreferences(stored); setDraft(stored); }
      const bookmarks = JSON.parse(localStorage.getItem("hackradar-saved-v1") || "[]");
      if (Array.isArray(bookmarks)) setSaved(bookmarks.filter(v => typeof v === "string"));
    } catch { /* Storage can be disabled or contain old data; defaults are safe. */ }
    setReady(true);
  }, []);
  useEffect(() => { if (ready) { try { localStorage.setItem("hackradar-preferences-v1", JSON.stringify(preferences)); localStorage.setItem("hackradar-saved-v1", JSON.stringify(saved)); } catch { /* In-memory state still works. */ } } }, [preferences, saved, ready]);
  useEffect(() => { api<{ grok_configured: boolean }>("status").then(s => setGrok(s.grok_configured)).catch(() => {}); }, [refresh]);
  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    setLoading(true); setError("");
    const timeout = setTimeout(() => {
      api<SearchResult>("search", { preferences, query, sort }, controller.signal).then(setData).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 200);
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [preferences, query, sort, refresh, ready]);
  const toggleSaved = useCallback((id: string) => setSaved(items => items.includes(id) ? items.filter(item => item !== id) : [...items, id]), []);
  const visible = data?.results.filter(r => tab === "discover" || saved.includes(r.event.id)) || [];
  function reset() { setDraft(DEFAULTS); setPreferences(DEFAULTS); setQuery(""); setSort("score"); }
  function toggleInterest(interest: Interest) { setDraft(p => ({ ...p, interests: p.interests.includes(interest) ? p.interests.length === 1 ? p.interests : p.interests.filter(i => i !== interest) : [...p.interests, interest] })); }

  return <>
    <header className="site-header"><div className="header-inner"><a href="/" className="brand" aria-label="HackRadar home"><span className="brand-icon"><Radar size={23} /></span>hackradar<span className="brand-ai">AI</span></a><nav aria-label="Main navigation"><button className={tab === "discover" ? "active" : ""} onClick={() => setTab("discover")}><Compass size={16} />Discover</button><button className={tab === "saved" ? "active" : ""} onClick={() => setTab("saved")}><Bookmark size={16} />Saved<span className="count-pill">{saved.length}</span></button></nav><button className="header-method" onClick={() => setModal("method")}>How it works <ArrowUpRight size={15} /></button><div className="profile-avatar" aria-label="Local personal workspace">YOU</div></div></header>
    <main className="shell">
      <section className="hero"><div className="hero-copy"><div className="hero-kicker"><span className="live-dot" />LESS SEARCHING. MORE SHIPPING.</div><h1>Find your next<br /><span>great build.</span></h1><p>Hackathons that fit your interests, your ambitions,<br className="desktop-break" /> and your calendar. Every match, explained.</p><div className="hero-footer"><span><MapPin size={14} />{preferences.city}</span><i /><span>Next {preferences.days} days</span><i /><span>Built for builders</span></div></div>
        <div className="radar-scene" aria-hidden="true"><div className="radar-axis axis-x" /><div className="radar-axis axis-y" /><div className="radar-ring ring-1" /><div className="radar-ring ring-2" /><div className="radar-ring ring-3" /><div className="radar-ring ring-4" /><div className="radar-sweep" /><div className="radar-center"><Radar size={22} /></div><span className="radar-dot dot-a" /><span className="radar-dot dot-b" /><span className="radar-dot dot-c" /><div className="radar-label label-a"><span className="mini-icon"><Code2 size={15} /></span>AI Agents <span className="mini-check"><Check size={12} /></span></div><div className="radar-label label-b"><span className="mini-icon"><Zap size={15} /></span>Your next opportunity<ArrowUpRight size={14} /></div><span className="radar-coordinate">51.5072° N / 0.1276° W</span></div>
      </section>
      <section className="workspace-heading"><div><span className="eyebrow">YOUR OPPORTUNITY RADAR</span><h2>{tab === "saved" ? "Worth keeping an eye on." : "Good things on your horizon."}</h2></div><button className="secondary add-event" onClick={() => setModal("import")}><Plus size={17} />Add an event</button></section>
      <div className="workspace">
        <aside className={`filter-panel ${filtersOpen ? "mobile-open" : ""}`}><div className="filter-heading"><h3><SlidersHorizontal size={17} />Your preferences</h3><button className="text-button" onClick={reset}>Reset</button></div>
          <form onSubmit={e => { e.preventDefault(); setPreferences({ ...draft, city: draft.city.trim() }); setFiltersOpen(false); }}>
            <label className="field-label" htmlFor="city">Where are you building?</label><div className="input-icon"><MapPin size={16} /><input id="city" required maxLength={80} value={draft.city} onChange={e => setDraft(p => ({ ...p, city: e.target.value }))} /></div>
            <label className="check-label"><input type="checkbox" checked={draft.include_online} onChange={e => setDraft(p => ({ ...p, include_online: e.target.checked }))} /><span>Include online events</span></label>
            <label className="field-label" htmlFor="days">Your time window</label><div className="select-wrap"><CalendarDays size={16} /><select id="days" value={draft.days} onChange={e => setDraft(p => ({ ...p, days: Number(e.target.value) }))}>{[7, 14, 30, 60, 90].map(days => <option value={days} key={days}>Next {days} days</option>)}</select><ChevronDown size={15} /></div>
            <fieldset><legend className="field-label">What gets you building?</legend><div className="interest-options">{INTERESTS.map(interest => <button type="button" className={draft.interests.includes(interest) ? "interest selected" : "interest"} aria-pressed={draft.interests.includes(interest)} key={interest} onClick={() => toggleInterest(interest)}>{draft.interests.includes(interest) ? <Check size={13} /> : <Plus size={13} />}{interest}</button>)}</div><p className="tiny-note">Choose at least one interest.</p></fieldset>
            <div className="range-label"><label className="field-label" htmlFor="min-score">Minimum match</label><output>{draft.min_score.toFixed(1)}<span> / 10</span></output></div><input id="min-score" type="range" min="0" max="10" step="0.5" value={draft.min_score} onChange={e => setDraft(p => ({ ...p, min_score: Number(e.target.value) }))} /><div className="range-ends"><span>Explore more</span><span>Best fit</span></div>
            <div className="filter-divider" /><label className="check-label examples-check"><input type="checkbox" checked={draft.include_examples} onChange={e => setDraft(p => ({ ...p, include_examples: e.target.checked }))} /><span>Show example events<small>Fictional data to explore the demo</small></span></label>
            <button type="submit" className="primary full apply-button" disabled={!draft.city.trim()}>Update my radar <ArrowRight size={16} /></button>
          </form><div className="sidebar-note"><Sparkles size={18} /><h4>A match, with receipts.</h4><p>Every score comes with a breakdown. You decide what’s worth your time.</p><button className="text-button" onClick={() => setModal("method")}>See how we score <ArrowUpRight size={13} /></button></div>
        </aside>
        <section className="results" aria-label="Matching events" aria-busy={loading}>
          <div className="results-toolbar"><div className="search-box"><Search size={18} /><input type="search" aria-label="Search events" placeholder="Search your next opportunity…" value={query} onChange={e => setQuery(e.target.value)} /></div><div className="sort-box"><ArrowDownUp size={15} /><select aria-label="Sort events" value={sort} onChange={e => setSort(e.target.value)}><option value="score">Best match</option><option value="date">Soonest first</option></select><ChevronDown size={14} /></div><button className="mobile-filter secondary" onClick={() => setFiltersOpen(p => !p)} aria-expanded={filtersOpen}><SlidersHorizontal size={17} />Filters</button></div>
          <div className="results-summary"><p aria-live="polite">{loading ? "Tuning your radar…" : <><strong>{visible.length} {tab === "saved" ? "saved matches" : "matches"}</strong><span> for your next chapter</span></>}</p><span className="rules-badge"><span />Transparent scoring</span></div>
          {preferences.include_examples && <div className="demo-banner"><Info size={16} /><p><strong>You’re exploring the demo.</strong> Example events are fictional. Import a real listing to make this radar yours.</p><button onClick={() => setModal("import")} aria-label="Import a real listing"><ArrowRight size={17} /></button></div>}
          {tab === "saved" && <p className="fine-print saved-note">Saved on this browser. Your search and preference filters still apply.</p>}
          {error ? <div className="empty-state" role="alert"><Radar size={34} /><h3>The radar is offline</h3><p>{error}</p><button className="primary" onClick={() => setRefresh(n => n + 1)}>Try again</button></div> : loading ? <div className="event-grid">{[0, 1, 2, 3].map(n => <div className="skeleton" key={n}><div /><span /><span /><span /></div>)}</div> : visible.length ? <div className="event-grid">{visible.map((item, index) => <EventCard key={item.event.id} item={item} index={index} saved={saved.includes(item.event.id)} onSave={() => toggleSaved(item.event.id)} onOpen={() => setSelected(item)} />)}</div> : <div className="empty-state"><Radar size={36} /><h3>{tab === "saved" ? "A little room for possibility." : "Nothing on this frequency. Yet."}</h3><p>{tab === "saved" ? "Save an event from Discover, or widen your filters to find your saved matches." : "Try a wider date window, a lower score, or add a public event. If examples are hidden, only your imports appear."}</p><button className="primary" onClick={tab === "saved" ? () => setTab("discover") : reset}>{tab === "saved" ? "Discover events" : "Reset preferences"}<ArrowRight size={15} /></button></div>}
          {!loading && !error && data && <p className="results-footnote"><Check size={13} />{data.total_scanned} listings in your radar · {data.imported} imported · dates checked in Europe/London</p>}
        </section>
      </div>
      <footer className="footer"><span className="footer-brand"><Radar size={17} />hackradar AI <span>Find your people. Build your thing.</span></span><span>Made for the next great idea.<Code2 size={15} /></span></footer>
    </main>
    {selected && <EventDetails item={selected} preferences={preferences} grok={grok} onClose={() => setSelected(null)} />}
    {modal === "import" && <ImportModal onClose={() => setModal(null)} onImported={() => setRefresh(n => n + 1)} />}
    {modal === "method" && <Modal title="A match, with receipts." onClose={() => setModal(null)}><div className="method-content"><div className="method-icon"><Radar size={32} /></div><p>HackRadar helps you decide where to spend your next weekend. Every event gets the same reproducible, 10-point score.</p><div className="method-rows"><div><span>Interest overlap<small>Equal weight per selected interest; explicit phrases in the listing.</small></span><b>5.0</b></div><div><span>Location fit<small>2.5 for your city; 2.0 for enabled online attendance.</small></span><b>2.5</b></div><div><span>In your date window<small>London calendar dates, including today and the last day.</small></span><b>1.5</b></div><div><span>Time to build<small>Hackathon 1.0 · workshop 0.5 · meetup 0.25.</small></span><b>1.0</b></div></div><p>Location and dates are also hard filters. Your minimum score is inclusive. Keyword matching can miss synonyms and does not understand negation; it is a starting point for your judgment.</p><div className="notice"><Info size={18} /><span>Scores use transparent rules. Optional Grok generates preparation advice; it never secretly changes a score. Public imports preserve provenance but aren’t independently verified. No background web search or scheduled scan runs in this MVP.</span></div></div></Modal>}
  </>;
}
