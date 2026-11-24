use std::{
    collections::{BTreeMap, BTreeSet, HashMap, HashSet},
    env, fs,
    io::{self, IsTerminal, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};

use crossterm::{
    event::{
        self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind, KeyModifiers,
    },
    execute,
};
use rataflow::{
    Background, Edge, FitViewOptions, Flow, FlowEvent, MiniMap, Node, NodeContent,
    NodeRenderContext, StepEdge, Sugiyama,
};
use ratatui::{
    Frame,
    buffer::Buffer,
    layout::{Constraint, Layout, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Block, BorderType, Clear, List, ListItem, ListState, Paragraph, Widget, Wrap},
};
use serde::{Deserialize, Serialize};

const BG: Color = Color::Rgb(15, 19, 26);
const MUTED: Color = Color::Rgb(143, 155, 174);
const GOLD: Color = Color::Rgb(235, 192, 86);
const CYAN: Color = Color::Rgb(98, 203, 219);
const RED: Color = Color::Rgb(241, 113, 112);
const GREEN: Color = Color::Rgb(130, 195, 147);
const REFRESH: Duration = Duration::from_secs(3);

type Graph = Flow<Task, StepEdge>;
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(default)]
struct Task {
    id: String,
    title: String,
    status: String,
    assignee: String,
    body: String,
    result: String,
    block_kind: String,
    block_reason: String,
    last_failure_error: String,
    consecutive_failures: i64,
    priority: i64,
    comments: Vec<String>,
}

impl Task {
    fn attention(&self) -> bool {
        self.status == "blocked" || self.status == "review" || self.failed()
    }

    fn failed(&self) -> bool {
        matches!(self.status.as_str(), "failed" | "crashed" | "timed_out")
            || (!matches!(self.status.as_str(), "done" | "archived")
                && self.consecutive_failures > 0)
    }

    fn color(&self) -> Color {
        if self.failed() || self.status == "blocked" {
            RED
        } else if self.status == "review" {
            GOLD
        } else if self.status == "running" {
            CYAN
        } else if self.status == "done" {
            GREEN
        } else {
            MUTED
        }
    }

    fn rank(&self) -> u8 {
        if self.failed() {
            0
        } else {
            match self.status.as_str() {
                "blocked" => 1,
                "review" => 2,
                "running" => 3,
                "done" => 5,
                _ => 4,
            }
        }
    }
}

// Strip terminal control bytes from all external text before rendering.
fn clean(value: &str) -> String {
    value
        .chars()
        .filter(|c| !c.is_control() || *c == '\n')
        .collect()
}

impl NodeContent for Task {
    fn render(&self, ctx: &NodeRenderContext, buf: &mut Buffer) {
        let color = if ctx.selected { GOLD } else { self.color() };
        let block = Block::bordered()
            .border_type(BorderType::Rounded)
            .title(clean(&format!(" {} ", self.id)))
            .border_style(Style::default().fg(color))
            .style(Style::default().bg(BG));
        let inner = block.inner(ctx.area);
        block.render(ctx.area, buf);
        let label = if self.failed() {
            format!("{} / FAILURE", self.status)
        } else {
            self.status.clone()
        };
        let pulse = if self.status == "running" {
            ["|", "/", "-", "\\"][ctx.animation_phase % 4]
        } else {
            " "
        };
        Paragraph::new(vec![
            Line::styled(
                clean(&self.title).replace('\n', " "),
                Style::default().fg(Color::White).bold(),
            ),
            Line::styled(
                clean(&format!(
                    "{pulse}{label} @{}",
                    if self.assignee.is_empty() {
                        "unassigned"
                    } else {
                        &self.assignee
                    }
                ))
                .replace('\n', " "),
                Style::default().fg(self.color()),
            ),
        ])
        .render(inner, buf);
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct Board {
    slug: String,
    name: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct Snapshot {
    scope: String,
    board: String,
    boards: Vec<Board>,
    tasks: Vec<Task>,
    links: Vec<[String; 2]>,
    error: Option<String>,
}

#[derive(Clone, Default)]
struct Source {
    root: Option<String>,
    db: Option<String>,
}

impl Source {
    fn fetch(&self, board: &str) -> std::result::Result<Snapshot, String> {
        let mut cmd = Command::new("python3");
        cmd.args(["-c", include_str!("../reader.py"), "--board", board])
            .stdin(Stdio::null());
        if let Some(root) = &self.root {
            cmd.args(["--root", root]);
        }
        if let Some(db) = &self.db {
            cmd.args(["--db", db]);
        }
        let output = cmd
            .output()
            .map_err(|e| format!("Cannot run python3: {e}"))?;
        if !output.status.success() {
            return Err(format!(
                "Board reader failed ({}): {}",
                output.status,
                clean(&String::from_utf8_lossy(&output.stderr))
            ));
        }
        serde_json::from_slice(&output.stdout).map_err(|e| format!("Invalid board snapshot: {e}"))
    }
}

fn state_path() -> Option<PathBuf> {
    if let Some(dir) = env::var_os("HERDR_PLUGIN_STATE_DIR") {
        return Some(PathBuf::from(dir).join("boards.json"));
    }
    env::var_os("XDG_STATE_HOME")
        .map(PathBuf::from)
        .or_else(|| env::var_os("HOME").map(|h| PathBuf::from(h).join(".local/state")))
        .map(|p| p.join("herdr/hermes-kanban/boards.json"))
}

fn read_selections(path: &Path) -> Result<BTreeMap<String, String>> {
    match fs::read(path) {
        Ok(bytes) => Ok(serde_json::from_slice(&bytes)?),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(BTreeMap::new()),
        Err(e) => Err(e.into()),
    }
}

fn remember(path: &Path, scope: &str, board: &str) -> Result<()> {
    let mut selections = read_selections(path)?;
    if selections.get(scope).is_some_and(|value| value == board) {
        return Ok(());
    }
    selections.insert(scope.to_owned(), board.to_owned());
    let parent = path.parent().ok_or("Invalid state path")?;
    fs::create_dir_all(parent)?;
    let tmp = parent.join(format!(".boards-{}.tmp", std::process::id()));
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&tmp)?;
    let result = (|| -> Result<()> {
        file.write_all(&serde_json::to_vec(&selections)?)?;
        file.sync_all()?;
        fs::rename(&tmp, path)?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(tmp);
    }
    result
}

#[derive(Default)]
struct Filters {
    show_done: bool,
    attention: bool,
    statuses: BTreeSet<String>,
    assignees: BTreeSet<String>,
    query: String,
}

impl Filters {
    fn matches(&self, task: &Task) -> bool {
        (self.show_done || task.status != "done")
            && (!self.attention || task.attention())
            && (self.statuses.is_empty() || self.statuses.contains(&task.status))
            && (self.assignees.is_empty() || self.assignees.contains(&task.assignee))
            && format!(
                "{} {} {} {} {}",
                task.id, task.title, task.status, task.assignee, task.body
            )
            .to_lowercase()
            .contains(&self.query.to_lowercase())
    }
}

#[derive(Clone)]
enum FilterOption {
    Done,
    Attention,
    Status(String),
    Assignee(String),
}

struct App {
    snapshot: Snapshot,
    lanes: bool,
    filters: Filters,
    filter_picker: Option<ListState>,
    filter_options: Vec<FilterOption>,
    search: Option<String>,
    lane_hits: Vec<(Rect, String)>,
    graph: Graph,
    selected_board: String,
    error: Option<String>,
    notice: Option<String>,
    updated: Option<Instant>,
    details: bool,
    scroll: u16,
    picker: Option<ListState>,
    help: bool,
    follow: bool,
    center: bool,
    loading: bool,
    state: Option<PathBuf>,
}

impl App {
    fn new(snapshot: Snapshot, state: Option<PathBuf>) -> Self {
        let selected_board = snapshot.board.clone();
        let mut app = Self {
            snapshot: Snapshot {
                tasks: vec![],
                links: vec![],
                ..snapshot.clone()
            },
            lanes: false,
            filters: Filters::default(),
            filter_picker: None,
            filter_options: vec![],
            search: None,
            lane_hits: vec![],
            graph: Flow::new(),
            selected_board,
            error: None,
            notice: None,
            updated: None,
            details: false,
            scroll: 0,
            picker: None,
            help: false,
            follow: false,
            center: false,
            loading: false,
            state,
        };
        app.accept(snapshot);
        app
    }

    fn accept(&mut self, mut next: Snapshot) {
        self.loading = false;
        if next.board != self.selected_board {
            return;
        }
        self.snapshot.boards = next.boards.clone();
        if let Some(error) = &next.error {
            self.error = Some(error.clone());
            return;
        }
        next.tasks.sort_by(|a, b| {
            (a.rank(), std::cmp::Reverse(a.priority), &a.id).cmp(&(
                b.rank(),
                std::cmp::Reverse(b.priority),
                &b.id,
            ))
        });
        if !self.rebuild(&next) {
            return;
        }
        self.error = None;
        self.updated = Some(Instant::now());
        self.snapshot = next;
        if let Some(path) = &self.state
            && let Err(e) = remember(path, &self.snapshot.scope, &self.snapshot.board)
        {
            self.notice = Some(format!("Selection not saved: {e}"));
        }
    }

    fn rebuild(&mut self, next: &Snapshot) -> bool {
        let first = self.graph.nodes().next().is_none();
        let selection = self.graph.first_selected_node_id();
        let positions: HashMap<_, _> = self
            .graph
            .nodes()
            .map(|n| (n.id.clone(), n.position))
            .collect();
        let mut bottom = self
            .graph
            .nodes()
            .map(|n| n.position.y + n.height + 3.0)
            .fold(0.0_f64, f64::max);
        let mut changed = None;
        let mut nodes = Vec::new();
        for (i, task) in next
            .tasks
            .iter()
            .filter(|t| self.filters.matches(t))
            .enumerate()
        {
            if let Some(old) = self.snapshot.tasks.iter().find(|t| t.id == task.id)
                && old.status != task.status
                && (task.attention() || task.status == "running")
                && changed.is_none()
            {
                changed = Some(task.id.clone());
            }
            let pos = positions.get(&task.id).copied().unwrap_or_else(|| {
                if first {
                    ((i % 3) as f64 * 36.0, (i / 3) as f64 * 6.0).into()
                } else {
                    let p = (0.0, bottom).into();
                    bottom += 6.0;
                    p
                }
            });
            let mut node = Node::new(&task.id, pos, (30.0, 4.0), task.clone());
            node.deletable = false;
            node.connectable = false;
            node.draggable = false;
            nodes.push(node);
        }
        let ids: HashSet<_> = next
            .tasks
            .iter()
            .filter(|t| self.filters.matches(t))
            .map(|t| t.id.as_str())
            .collect();
        let edges = next
            .links
            .iter()
            .filter(|[a, b]| ids.contains(a.as_str()) && ids.contains(b.as_str()))
            .map(|[a, b]| {
                Edge::new(format!("{a}:{b}"), a, b)
                    .with_deletable(false)
                    .with_selectable(false)
            })
            .collect();
        match Flow::with_graph(nodes, edges) {
            Ok(mut graph) => {
                graph.edges_reconnectable = false;
                if first && !next.links.is_empty() {
                    graph.apply_layout(
                        Sugiyama::horizontal()
                            .with_node_spacing(3.0)
                            .with_rank_spacing(6.0),
                    );
                }
                if !first {
                    graph.viewport = self.graph.viewport;
                }
                let target = if self.follow {
                    changed.as_ref().or(selection.as_ref())
                } else {
                    selection.as_ref()
                };
                if let Some(id) = target.filter(|id| ids.contains(id.as_str())).or_else(|| {
                    next.tasks
                        .iter()
                        .find(|t| self.filters.matches(t))
                        .map(|t| &t.id)
                }) {
                    graph.select_node(id);
                }
                if first {
                    graph.request_fit_view_with_options(
                        FitViewOptions::default().with_max_zoom(1.0),
                    );
                }
                self.center |= self.follow && changed.is_some();
                self.graph = graph;
                true
            }
            Err(e) => {
                self.error = Some(format!("Invalid graph: {e}"));
                false
            }
        }
    }

    fn select_board(&mut self, slug: String) {
        self.selected_board = slug.clone();
        self.snapshot.board = slug;
        self.snapshot.tasks.clear();
        self.snapshot.links.clear();
        self.graph = Flow::new();
        self.updated = None;
        self.error = None;
        self.details = false;
        self.picker = None;
        self.loading = true;
    }

    fn task(&self) -> Option<&Task> {
        let id = self.graph.first_selected_node_id()?;
        self.snapshot.tasks.iter().find(|t| t.id == id)
    }

    fn next_attention(&mut self) {
        let ids: Vec<_> = self
            .snapshot
            .tasks
            .iter()
            .filter(|t| t.attention() && self.filters.matches(t))
            .map(|t| t.id.clone())
            .collect();
        if ids.is_empty() {
            self.notice = Some("No cards need attention.".into());
            return;
        }
        let index = self
            .graph
            .first_selected_node_id()
            .and_then(|id| ids.iter().position(|v| *v == id));
        self.graph.clear_selection();
        self.graph
            .select_node(&ids[index.map_or(0, |i| (i + 1) % ids.len())]);
        self.graph.reset_zoom();
        self.center = true;
        self.scroll = 0;
    }

    fn apply_filters(&mut self) {
        self.rebuild(&self.snapshot.clone());
        self.graph
            .request_fit_view_with_options(FitViewOptions::default().with_max_zoom(1.0));
        self.scroll = 0;
    }

    fn search_key(&mut self, key: event::KeyEvent) {
        match key.code {
            KeyCode::Enter => {
                self.search = None;
            }
            KeyCode::Esc => {
                self.filters.query = self.search.take().unwrap();
            }
            KeyCode::Backspace => {
                self.filters.query.pop();
            }
            KeyCode::Char(c)
                if !key
                    .modifiers
                    .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT) =>
            {
                self.filters.query.push(c)
            }
            _ => {}
        }
        self.apply_filters();
    }

    fn open_filters(&mut self) {
        self.filter_options = vec![FilterOption::Done, FilterOption::Attention];
        let statuses: BTreeSet<_> = self
            .snapshot
            .tasks
            .iter()
            .map(|t| t.status.clone())
            .chain(self.filters.statuses.iter().cloned())
            .collect();
        let assignees: BTreeSet<_> = self
            .snapshot
            .tasks
            .iter()
            .map(|t| t.assignee.clone())
            .chain(self.filters.assignees.iter().cloned())
            .collect();
        self.filter_options
            .extend(statuses.into_iter().map(FilterOption::Status));
        self.filter_options
            .extend(assignees.into_iter().map(FilterOption::Assignee));
        self.filter_picker = Some(ListState::default().with_selected(Some(0)));
    }

    fn toggle_filter(&mut self, index: usize) {
        match &self.filter_options[index] {
            FilterOption::Done => self.filters.show_done = !self.filters.show_done,
            FilterOption::Attention => self.filters.attention = !self.filters.attention,
            FilterOption::Status(value) => {
                if !self.filters.statuses.remove(value) {
                    self.filters.statuses.insert(value.clone());
                    if value == "done" {
                        self.filters.show_done = true;
                    }
                }
            }
            FilterOption::Assignee(value) => {
                if !self.filters.assignees.remove(value) {
                    self.filters.assignees.insert(value.clone());
                }
            }
        }
        self.apply_filters();
    }

    fn lane_groups(&self) -> Vec<(String, Vec<String>)> {
        let mut groups: BTreeMap<String, Vec<String>> = BTreeMap::new();
        for task in self
            .snapshot
            .tasks
            .iter()
            .filter(|t| self.filters.matches(t))
        {
            groups
                .entry(task.status.clone())
                .or_default()
                .push(task.id.clone());
        }
        let order = [
            "triage",
            "todo",
            "scheduled",
            "ready",
            "running",
            "blocked",
            "review",
            "done",
        ];
        let mut groups: Vec<_> = groups.into_iter().collect();
        groups.sort_by_key(|(status, _)| {
            order
                .iter()
                .position(|s| *s == status)
                .unwrap_or(order.len())
        });
        groups
    }

    fn lane_move(&mut self, code: KeyCode) {
        let groups = self.lane_groups();
        if groups.is_empty() {
            return;
        }
        let selected = self.graph.first_selected_node_id().unwrap_or_default();
        let (col, row) = groups
            .iter()
            .enumerate()
            .find_map(|(col, (_, ids))| {
                ids.iter()
                    .position(|id| *id == selected)
                    .map(|row| (col, row))
            })
            .unwrap_or((0, 0));
        let id = match code {
            KeyCode::Left | KeyCode::Char('h') => {
                &groups[col.saturating_sub(1)].1[row.min(groups[col.saturating_sub(1)].1.len() - 1)]
            }
            KeyCode::Right | KeyCode::Char('l') => {
                let col = (col + 1).min(groups.len() - 1);
                &groups[col].1[row.min(groups[col].1.len() - 1)]
            }
            KeyCode::Up | KeyCode::Char('k') => &groups[col].1[row.saturating_sub(1)],
            KeyCode::Down | KeyCode::Char('j') => {
                &groups[col].1[(row + 1).min(groups[col].1.len() - 1)]
            }
            KeyCode::Tab | KeyCode::BackTab => {
                let ids: Vec<_> = groups.iter().flat_map(|(_, ids)| ids.iter()).collect();
                let i = ids.iter().position(|id| **id == selected).unwrap_or(0);
                ids[(i + if code == KeyCode::Tab {
                    1
                } else {
                    ids.len() - 1
                }) % ids.len()]
            }
            _ => return,
        }
        .clone();
        self.graph.clear_selection();
        self.graph.select_node(&id);
        self.scroll = 0;
    }

    fn draw_lanes(&mut self, frame: &mut Frame, area: Rect) {
        let groups = self.lane_groups();
        let selected = self.graph.first_selected_node_id().unwrap_or_default();
        let columns = (area.width as usize / 28).max(1).min(groups.len().max(1));
        let selected_col = groups
            .iter()
            .position(|(_, ids)| ids.contains(&selected))
            .unwrap_or(0);
        let start = selected_col.saturating_sub(columns - 1);
        let rects =
            Layout::horizontal(vec![Constraint::Ratio(1, columns as u32); columns]).split(area);
        for (column, ((status, ids), bounds)) in
            groups.iter().skip(start).zip(rects.iter()).enumerate()
        {
            let block = panel("").title(clean(&format!(
                " {status} ({}) [{}/{}] ",
                ids.len(),
                start + column + 1,
                groups.len()
            )));
            let inner = block.inner(*bounds);
            frame.render_widget(block, *bounds);
            let capacity = (inner.height as usize / 4).max(1);
            let row = ids.iter().position(|id| *id == selected).unwrap_or(0);
            let offset = row.saturating_sub(capacity - 1);
            for (i, id) in ids.iter().skip(offset).take(capacity).enumerate() {
                let task = self.snapshot.tasks.iter().find(|t| t.id == *id).unwrap();
                let card = Rect::new(
                    inner.x,
                    inner.y + i as u16 * 4,
                    inner.width,
                    4.min(inner.height),
                );
                let border = Block::bordered().title(clean(id)).border_style(
                    Style::default().fg(if *id == selected { GOLD } else { task.color() }),
                );
                frame.render_widget(
                    Paragraph::new(vec![
                        Line::raw(clean(&task.title).replace('\n', " ")),
                        Line::styled(
                            clean(&format!(
                                "@{}{}",
                                if task.assignee.is_empty() {
                                    "unassigned"
                                } else {
                                    &task.assignee
                                },
                                if task.failed() { " / FAILURE" } else { "" }
                            ))
                            .replace('\n', " "),
                            Style::default().fg(task.color()),
                        ),
                    ])
                    .block(border),
                    card,
                );
                self.lane_hits.push((card, id.clone()));
            }
        }
    }

    fn draw(&mut self, frame: &mut Frame) {
        self.lane_hits.clear();
        let area = frame.area();
        frame.render_widget(
            Block::default().style(Style::default().bg(BG).fg(Color::White)),
            area,
        );
        if area.width < 45 || area.height < 12 {
            frame.render_widget(
                Paragraph::new("Enlarge popup to at least 45 x 12. q / Esc closes.")
                    .wrap(Wrap { trim: true }),
                area,
            );
            return;
        }
        let rows = Layout::vertical([
            Constraint::Length(4),
            Constraint::Min(1),
            Constraint::Length(2),
        ])
        .split(area);
        let name = self
            .snapshot
            .boards
            .iter()
            .find(|b| b.slug == self.selected_board)
            .map(|b| b.name.as_str())
            .unwrap_or(&self.selected_board);
        let attention = self.snapshot.tasks.iter().filter(|t| t.attention()).count();
        let running = self
            .snapshot
            .tasks
            .iter()
            .filter(|t| t.status == "running")
            .count();
        let done = self
            .snapshot
            .tasks
            .iter()
            .filter(|t| t.status == "done")
            .count();
        let header = vec![
            Line::from(vec![
                Span::styled(" HERMES / KANBAN  ", Style::default().fg(GOLD).bold()),
                Span::raw(clean(name)),
                Span::styled("   [b] boards", Style::default().fg(MUTED)),
            ]),
            Line::from(vec![
                Span::styled(
                    format!(" {attention} NEED ATTENTION"),
                    Style::default().fg(if attention > 0 { RED } else { GREEN }),
                ),
                Span::styled(
                    format!(
                        "   {running} running   {done} done   {} cards   {}",
                        self.snapshot.tasks.len(),
                        if self.follow { "FOLLOW" } else { "EXPLORE" }
                    ),
                    Style::default().fg(MUTED),
                ),
            ]),
            Line::styled(
                clean(&format!(
                    " {} | {}/{} visible | done:{} attention:{} status:{:?} assignee:{:?} /{}",
                    if self.lanes { "LANES" } else { "GRAPH" },
                    self.graph.nodes().count(),
                    self.snapshot.tasks.len(),
                    if self.filters.show_done {
                        "show"
                    } else {
                        "hide"
                    },
                    self.filters.attention,
                    self.filters.statuses,
                    self.filters.assignees,
                    self.filters.query
                )),
                Style::default().fg(CYAN),
            ),
        ];
        frame.render_widget(Paragraph::new(header), rows[0]);
        let show_details = self.details && self.task().is_some();
        let parts = if show_details && area.width >= 100 {
            Layout::horizontal([Constraint::Min(40), Constraint::Length(46)])
                .split(rows[1])
                .to_vec()
        } else {
            vec![rows[1]]
        };
        let graph_area = parts[0];
        if self.lanes {
            self.draw_lanes(frame, graph_area);
        } else {
            frame.render_widget(Background::new(&self.graph), graph_area);
            frame.render_widget(&mut self.graph, graph_area);
            if self.center {
                self.graph.center_on_selected();
                self.center = false;
            }
            if area.width >= 100 && area.height >= 30 && !show_details {
                let mini = Rect::new(graph_area.right() - 27, graph_area.bottom() - 12, 27, 12);
                frame.render_widget(Clear, mini);
                frame.render_widget(MiniMap::new(&self.graph).block(panel(" Map ")), graph_area);
            }
        }
        if self.graph.nodes().next().is_none() {
            let text = if self.loading {
                "Loading board..."
            } else if self.error.is_some() {
                "Board unavailable. Press b to select a board, r to retry."
            } else {
                "No matching cards. d toggles done; F filters; x resets; b switches board."
            };
            frame.render_widget(
                Paragraph::new(text).wrap(Wrap { trim: true }),
                graph_area.inner(ratatui::layout::Margin {
                    horizontal: 3,
                    vertical: 2,
                }),
            );
        }
        if show_details {
            let detail_area = if parts.len() > 1 { parts[1] } else { rows[1] };
            let task = self.task().unwrap();
            let parents: Vec<_> = self
                .snapshot
                .links
                .iter()
                .filter(|[_, b]| *b == task.id)
                .map(|[a, _]| a.as_str())
                .collect();
            let children: Vec<_> = self
                .snapshot
                .links
                .iter()
                .filter(|[a, _]| *a == task.id)
                .map(|[_, b]| b.as_str())
                .collect();
            let body = format!(
                "{}\n\nStatus: {}\nAssignee: {}\nPriority: {}\n\n{}{}{}\nParents: {}\nChildren: {}\n\n{}\n\nResult\n{}\n\nRecent comments\n{}",
                task.title,
                task.status,
                task.assignee,
                task.priority,
                if task.status == "blocked" {
                    format!("Block: {}\n{}\n", task.block_kind, task.block_reason)
                } else {
                    String::new()
                },
                if task.failed() {
                    format!(
                        "Reported failures: {}\n{}\n",
                        task.consecutive_failures, task.last_failure_error
                    )
                } else {
                    String::new()
                },
                if task.status == "review" {
                    "Review requested\n"
                } else {
                    ""
                },
                parents.join(", "),
                children.join(", "),
                task.body,
                task.result,
                task.comments.join("\n\n")
            );
            frame.render_widget(Clear, detail_area);
            frame.render_widget(
                Paragraph::new(clean(&body))
                    .wrap(Wrap { trim: false })
                    .scroll((self.scroll, 0))
                    .block(panel(&format!(" {} / Esc back ", clean(&task.id))))
                    .style(Style::default().bg(BG).fg(Color::White)),
                detail_area,
            );
        }
        let freshness = if let Some(error) = &self.error {
            format!(
                " STALE: {} | last success {}",
                clean(error),
                self.updated.map_or("never".into(), |t| format!(
                    "{}s ago",
                    t.elapsed().as_secs()
                ))
            )
        } else {
            format!(
                " {} | updated {} | {} | zoom {:.0}%",
                if self.loading {
                    "REFRESHING"
                } else {
                    "LIVE / read-only"
                },
                self.updated.map_or("never".into(), |t| format!(
                    "{}s ago",
                    t.elapsed().as_secs()
                )),
                self.notice.as_deref().unwrap_or("3s refresh"),
                self.graph.viewport.zoom * 100.0
            )
        };
        frame.render_widget(Paragraph::new(vec![
            Line::styled(freshness, Style::default().fg(if self.error.is_some() { RED } else { MUTED })),
            Line::styled(" v view  F filters  / search  d done  x reset  Enter details  b boards  ? help  q quit", Style::default().fg(GOLD)),
        ]), rows[2]);
        if let Some(state) = &mut self.picker {
            let bounds = modal(area, 70, 70);
            frame.render_widget(Clear, bounds);
            let items: Vec<_> = self
                .snapshot
                .boards
                .iter()
                .map(|b| {
                    ListItem::new(clean(&format!(
                        "{}  {}",
                        if b.slug == self.selected_board {
                            "*"
                        } else {
                            " "
                        },
                        b.name
                    )))
                })
                .collect();
            frame.render_stateful_widget(
                List::new(items)
                    .block(panel(" Boards / Enter select / Esc back "))
                    .style(Style::default().bg(BG).fg(Color::White))
                    .highlight_style(Style::default().bg(Color::Rgb(50, 62, 76)).fg(GOLD)),
                bounds,
                state,
            );
        }
        if let Some(state) = &mut self.filter_picker {
            let items: Vec<_> = self
                .filter_options
                .iter()
                .map(|option| {
                    let (on, label) = match option {
                        FilterOption::Done => (self.filters.show_done, "Show done".into()),
                        FilterOption::Attention => {
                            (self.filters.attention, "Attention only".into())
                        }
                        FilterOption::Status(v) => {
                            (self.filters.statuses.contains(v), format!("Status: {v}"))
                        }
                        FilterOption::Assignee(v) => (
                            self.filters.assignees.contains(v),
                            format!("Assignee: {}", if v.is_empty() { "unassigned" } else { v }),
                        ),
                    };
                    ListItem::new(clean(&format!("[{}] {label}", if on { "x" } else { " " })))
                })
                .collect();
            let bounds = modal(area, 85, 80);
            frame.render_widget(Clear, bounds);
            frame.render_stateful_widget(
                List::new(items)
                    .block(panel(" Filters: Space toggle / x reset / Enter close "))
                    .style(Style::default().bg(BG))
                    .highlight_style(Style::default().fg(GOLD).bold()),
                bounds,
                state,
            );
        }
        if self.search.is_some() {
            let bounds = Rect::new(area.x + 2, area.y + area.height / 2, area.width - 4, 3);
            frame.render_widget(Clear, bounds);
            frame.render_widget(
                Paragraph::new(clean(&self.filters.query))
                    .block(panel(" Search: Enter apply / Esc cancel "))
                    .style(Style::default().bg(BG)),
                bounds,
            );
        }
        if self.help {
            let bounds = modal(area, 80, 80);
            frame.render_widget(Clear, bounds);
            frame.render_widget(Paragraph::new("v: graph / Kanban lanes\nF: multiple filters; Space toggles, x resets\n/: search; Enter applies, Esc cancels\nd: show/hide done (hidden by default)\nx: reset all filters\nLanes: arrows/hjkl move, Tab cycles\nTab / Shift-Tab, arrows: select card\nEnter or click: card details\nj/k, PgUp/PgDn: scroll open details\nEscape: close details/picker/help, then popup\nh/j/k/l or drag canvas: pan\n+ / - or mouse wheel: zoom\no / 0: fit graph   c: center selection\nn: next card needing attention\nf: follow status changes; navigation pauses follow\nb: switch board (remembered locally)\nr: refresh now   q / Ctrl-C: quit\n\nEdges show recorded parent/child links.\nRed: blocked/reported failure. Gold: review.\nCyan spinner: recorded running status.\nUnknown states remain visible.\nRefresh errors keep last snapshot and mark STALE.\nGraph view does not modify Hermes data.")
                .wrap(Wrap { trim: true }).block(panel(" Hermes Kanban / ? or Esc back "))
                .style(Style::default().bg(BG).fg(Color::White)), bounds);
        }
    }
}

fn panel(title: &str) -> Block<'_> {
    Block::bordered()
        .border_type(BorderType::Rounded)
        .title(title)
        .border_style(Style::default().fg(MUTED))
}
fn modal(area: Rect, width: u16, height: u16) -> Rect {
    let w = area.width * width / 100;
    let h = area.height * height / 100;
    Rect::new(
        area.x + (area.width - w) / 2,
        area.y + (area.height - h) / 2,
        w,
        h,
    )
}

fn run(app: &mut App, source: Source) -> Result<()> {
    let (request_tx, request_rx) = mpsc::channel::<String>();
    let (result_tx, result_rx) = mpsc::channel();
    let worker = thread::spawn(move || {
        for board in request_rx {
            let result = source.fetch(&board);
            if result_tx.send((board, result)).is_err() {
                break;
            }
        }
    });
    let mut terminal = ratatui::init();
    let result = (|| -> Result<()> {
        execute!(io::stdout(), EnableMouseCapture)?;
        let mut last_fetch = Instant::now();
        let mut last_tick = Instant::now();
        let mut pending = false;
        let mut refresh = false;
        loop {
            while let Ok((board, result)) = result_rx.try_recv() {
                pending = false;
                if board != app.selected_board {
                    refresh = true;
                    continue;
                }
                match result {
                    Ok(snapshot) => app.accept(snapshot),
                    Err(error) => {
                        app.error = Some(error);
                        app.loading = false;
                    }
                }
            }
            if !pending && (refresh || last_fetch.elapsed() >= REFRESH) {
                request_tx.send(app.selected_board.clone())?;
                pending = true;
                app.loading = true;
                refresh = false;
                last_fetch = Instant::now();
            }
            let now = Instant::now();
            if app.error.is_none() {
                app.graph.tick_animation(now - last_tick);
            }
            last_tick = now;
            terminal.draw(|f| app.draw(f))?;
            if !event::poll(Duration::from_millis(50))? {
                continue;
            }
            loop {
                match event::read()? {
                    Event::Key(key) if key.kind != KeyEventKind::Release => {
                        if (key.code == KeyCode::Char('q') && app.search.is_none())
                            || (key.modifiers.contains(KeyModifiers::CONTROL)
                                && key.code == KeyCode::Char('c'))
                        {
                            return Ok(());
                        }
                        if app.search.is_some() {
                            app.search_key(key);
                        } else if let Some(state) = &mut app.filter_picker {
                            let len = app.filter_options.len();
                            let index = state.selected().unwrap_or(0);
                            match key.code {
                                KeyCode::Esc | KeyCode::Enter => app.filter_picker = None,
                                KeyCode::Down | KeyCode::Char('j') => {
                                    state.select(Some((index + 1) % len))
                                }
                                KeyCode::Up | KeyCode::Char('k') => {
                                    state.select(Some((index + len - 1) % len))
                                }
                                KeyCode::Char(' ') => app.toggle_filter(index),
                                KeyCode::Char('x') => {
                                    app.filters = Filters::default();
                                    app.apply_filters();
                                }
                                _ => {}
                            }
                        } else if app.help {
                            if matches!(key.code, KeyCode::Esc | KeyCode::Char('?')) {
                                app.help = false;
                            }
                        } else if let Some(state) = &mut app.picker {
                            let len = app.snapshot.boards.len();
                            match key.code {
                                KeyCode::Esc => app.picker = None,
                                KeyCode::Down | KeyCode::Char('j') if len > 0 => {
                                    state.select(Some((state.selected().unwrap_or(0) + 1) % len))
                                }
                                KeyCode::Up | KeyCode::Char('k') if len > 0 => state
                                    .select(Some((state.selected().unwrap_or(0) + len - 1) % len)),
                                KeyCode::Enter => {
                                    if let Some(board) =
                                        state.selected().and_then(|i| app.snapshot.boards.get(i))
                                    {
                                        app.select_board(board.slug.clone());
                                        refresh = true;
                                    }
                                }
                                _ => {}
                            }
                        } else {
                            match key.code {
                                KeyCode::Esc if app.details => app.details = false,
                                KeyCode::Esc => return Ok(()),
                                KeyCode::Char('?') => app.help = true,
                                KeyCode::Char('v') => app.lanes = !app.lanes,
                                KeyCode::Char('F') => app.open_filters(),
                                KeyCode::Char('/') => app.search = Some(app.filters.query.clone()),
                                KeyCode::Char('d') => {
                                    app.filters.show_done = !app.filters.show_done;
                                    app.apply_filters();
                                }
                                KeyCode::Char('x') => {
                                    app.filters = Filters::default();
                                    app.apply_filters();
                                }
                                KeyCode::Char('b') => {
                                    app.picker = Some(
                                        ListState::default().with_selected(
                                            app.snapshot
                                                .boards
                                                .iter()
                                                .position(|b| b.slug == app.selected_board)
                                                .or(Some(0)),
                                        ),
                                    );
                                }
                                KeyCode::Char('r') => refresh = true,
                                KeyCode::Char('n') => {
                                    app.follow = false;
                                    app.next_attention();
                                }
                                KeyCode::Enter => {
                                    app.details = !app.details;
                                    app.scroll = 0;
                                }
                                KeyCode::Down | KeyCode::Char('j') if app.details => {
                                    app.scroll = app.scroll.saturating_add(1)
                                }
                                KeyCode::Up | KeyCode::Char('k') if app.details => {
                                    app.scroll = app.scroll.saturating_sub(1)
                                }
                                KeyCode::PageDown if app.details => {
                                    app.scroll = app.scroll.saturating_add(10)
                                }
                                KeyCode::PageUp if app.details => {
                                    app.scroll = app.scroll.saturating_sub(10)
                                }
                                KeyCode::Char('f') => {
                                    app.follow = !app.follow;
                                    app.center = true;
                                }
                                KeyCode::Char('o') | KeyCode::Char('0') => {
                                    app.follow = false;
                                    app.graph.request_fit_view_with_options(
                                        FitViewOptions::default().with_max_zoom(1.0),
                                    );
                                }
                                KeyCode::Char('c') => app.center = true,
                                KeyCode::Char('+') | KeyCode::Char('=') => {
                                    app.follow = false;
                                    app.graph.zoom_in();
                                }
                                KeyCode::Char('-') | KeyCode::Char('_') => {
                                    app.follow = false;
                                    app.graph.zoom_out();
                                }
                                _ => {
                                    app.follow = false;
                                    if app.lanes {
                                        app.lane_move(key.code);
                                    } else {
                                        app.graph.handle_key_event(key);
                                    }
                                    app.scroll = 0;
                                }
                            }
                        }
                    }
                    Event::Mouse(mouse)
                        if app.picker.is_none()
                            && app.filter_picker.is_none()
                            && app.search.is_none()
                            && !app.help
                            && !app.details =>
                    {
                        app.follow = false;
                        if app.lanes {
                            if mouse.kind == event::MouseEventKind::Down(event::MouseButton::Left)
                                && let Some((_, id)) = app.lane_hits.iter().find(|(rect, _)| {
                                    rect.contains((mouse.column, mouse.row).into())
                                })
                            {
                                app.graph.clear_selection();
                                app.graph.select_node(id);
                                app.details = true;
                                app.scroll = 0;
                            }
                        } else {
                            for event in app.graph.handle_mouse_event(mouse).into_events() {
                                if matches!(event, FlowEvent::NodeClicked { .. }) {
                                    app.details = true;
                                    app.scroll = 0;
                                }
                            }
                        }
                    }
                    _ => {}
                }
                if !event::poll(Duration::ZERO)? {
                    break;
                }
            }
        }
    })();
    let _ = execute!(io::stdout(), DisableMouseCapture);
    ratatui::restore();
    drop(request_tx);
    let _ = worker.join();
    result
}

fn main() -> Result<()> {
    let mut source = Source::default();
    let mut board = String::new();
    let mut mode = String::new();
    let mut lanes = false;
    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--root" => source.root = Some(args.next().ok_or("--root requires a path")?),
            "--db" => source.db = Some(args.next().ok_or("--db requires a path")?),
            "--board" => board = args.next().ok_or("--board requires a slug")?,
            "--view" => {
                lanes = match args.next().as_deref() {
                    Some("lanes") => true,
                    Some("graph") => false,
                    _ => return Err("--view requires graph or lanes".into()),
                }
            }
            "--snapshot" | "--render" => mode = arg,
            "--help" | "-h" => {
                println!(
                    "hermes-kanban-tui [--root PATH] [--db PATH] [--board SLUG] [--view graph|lanes] [--snapshot | --render]\nNative read-only Hermes board graph. Requires python3.\nHERMES_KANBAN_HOME / HERMES_HOME select root; HERMES_KANBAN_DB pins one DB.\n--snapshot prints JSON; --render prints a terminal frame. Neither saves selection."
                );
                return Ok(());
            }
            _ => return Err(format!("Unknown argument: {arg}").into()),
        }
    }
    let mut snapshot = source.fetch(&board)?;
    if mode == "--snapshot" {
        println!("{}", serde_json::to_string_pretty(&snapshot)?);
        if let Some(error) = snapshot.error {
            return Err(error.into());
        }
        return Ok(());
    }
    let state = if mode.is_empty() { state_path() } else { None };
    let mut state_warning = None;
    if board.is_empty()
        && let Some(path) = &state
    {
        match read_selections(path) {
            Ok(saved) => {
                if let Some(slug) = saved.get(&snapshot.scope)
                    && *slug != snapshot.board
                {
                    snapshot = source.fetch(slug)?;
                }
            }
            Err(error) => state_warning = Some(format!("Saved selection unreadable: {error}")),
        }
    }
    let mut app = App::new(snapshot, state);
    app.lanes = lanes;
    if state_warning.is_some() {
        app.notice = state_warning;
    }
    if mode == "--render" {
        let mut terminal = ratatui::Terminal::new(ratatui::backend::TestBackend::new(160, 45))?;
        terminal.draw(|f| app.draw(f))?;
        terminal.draw(|f| app.draw(f))?;
        for y in 0..45 {
            let line: String = (0..160)
                .map(|x| terminal.backend().buffer()[(x, y)].symbol())
                .collect();
            println!("{}", line.trim_end());
        }
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err("Run inside a terminal, or use --snapshot / --render.".into());
    }
    run(&mut app, source)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> Snapshot {
        Snapshot {
            scope: "test-root".into(),
            board: "default".into(),
            boards: vec![
                Board {
                    slug: "default".into(),
                    name: "Default".into(),
                },
                Board {
                    slug: "other".into(),
                    name: "Other".into(),
                },
            ],
            tasks: vec![
                Task {
                    id: "a".into(),
                    title: "Review release".into(),
                    status: "review".into(),
                    ..Task::default()
                },
                Task {
                    id: "b".into(),
                    title: "Build API".into(),
                    status: "running".into(),
                    ..Task::default()
                },
            ],
            links: vec![["a".into(), "b".into()]],
            error: None,
        }
    }

    #[test]
    fn refresh_keeps_selection_and_camera_and_updates_content() {
        let mut app = App::new(fixture(), None);
        app.graph.clear_selection();
        app.graph.select_node("b");
        app.graph.pan(20.0, 10.0);
        let viewport = app.graph.viewport;
        let position = app.graph.nodes().find(|n| n.id == "b").unwrap().position;
        let mut next = fixture();
        next.tasks[1].status = "blocked".into();
        app.accept(next);
        assert_eq!(app.graph.first_selected_node_id().as_deref(), Some("b"));
        assert_eq!(app.graph.viewport, viewport);
        assert_eq!(
            app.graph.nodes().find(|n| n.id == "b").unwrap().position,
            position
        );
        assert_eq!(app.task().unwrap().status, "blocked");
        assert!(
            app.graph
                .nodes()
                .all(|n| !n.deletable && !n.connectable && !n.draggable)
        );
    }

    #[test]
    fn failed_reads_keep_snapshot_but_switch_never_shows_previous_board() {
        let mut app = App::new(fixture(), None);
        let mut failed = fixture();
        failed.error = Some("locked".into());
        failed.tasks.clear();
        app.accept(failed.clone());
        assert_eq!(app.snapshot.tasks.len(), 2);
        assert!(app.error.is_some());
        app.select_board("other".into());
        app.accept(fixture());
        assert!(app.snapshot.tasks.is_empty());
        failed.board = "other".into();
        app.accept(failed);
        assert!(app.snapshot.tasks.is_empty());
        assert!(app.updated.is_none());
    }

    #[test]
    fn render_details_and_small_terminal_without_panics() {
        let mut app = App::new(fixture(), None);
        let mut terminal =
            ratatui::Terminal::new(ratatui::backend::TestBackend::new(160, 45)).unwrap();
        terminal.draw(|f| app.draw(f)).unwrap();
        assert!(app.graph.viewport.zoom <= 1.0);
        assert!(
            app.graph
                .nodes()
                .all(|n| n.width == 30.0 && n.height == 4.0)
        );
        app.details = true;
        for (width, height) in [(160, 45), (60, 18), (20, 8)] {
            let mut terminal =
                ratatui::Terminal::new(ratatui::backend::TestBackend::new(width, height)).unwrap();
            terminal.draw(|f| app.draw(f)).unwrap();
            if width >= 45 {
                let text: String = terminal
                    .backend()
                    .buffer()
                    .content
                    .iter()
                    .map(|c| c.symbol())
                    .collect();
                assert!(text.contains("Review release"));
                assert!(text.contains("Review requested"));
            }
        }
    }

    #[test]
    fn unknown_states_and_extreme_priorities_are_preserved() {
        let mut next = fixture();
        next.tasks[0].status = "custom-state".into();
        next.tasks[0].priority = i64::MIN;
        let app = App::new(next, None);
        assert!(
            app.snapshot
                .tasks
                .iter()
                .any(|t| t.status == "custom-state")
        );
        let done = Task {
            status: "done".into(),
            consecutive_failures: 2,
            ..Task::default()
        };
        assert!(!done.attention());
        assert_eq!(clean("title\x1b[31m\r\nnext"), "title[31m\nnext");
    }

    #[test]
    fn combined_filters_hide_done_and_keep_stale_timestamp() {
        let mut data = fixture();
        data.tasks[0].assignee = "alice".into();
        data.tasks[1].assignee = "bob".into();
        data.tasks.push(Task {
            id: "done".into(),
            title: "Released".into(),
            status: "done".into(),
            ..Task::default()
        });
        data.links.push(["b".into(), "done".into()]);
        let mut app = App::new(data.clone(), None);
        assert_eq!(app.graph.nodes().count(), 2);
        assert_eq!(app.graph.edges().len(), 1);
        app.filters.show_done = true;
        app.apply_filters();
        assert_eq!(app.graph.nodes().count(), 3);
        assert_eq!(app.graph.edges().len(), 2);
        app.filters
            .statuses
            .extend(["review".into(), "running".into()]);
        app.filters.assignees.insert("alice".into());
        app.filters.attention = true;
        app.filters.query = "RELEASE".into();
        let updated = app.updated;
        app.error = Some("locked".into());
        app.apply_filters();
        assert_eq!(app.graph.nodes().count(), 1);
        assert_eq!(app.task().unwrap().id, "a");
        assert_eq!(app.updated, updated);
        assert_eq!(app.error.as_deref(), Some("locked"));
        app.accept(data);
        assert_eq!(app.graph.nodes().count(), 1);
        assert_eq!(app.filters.query, "RELEASE");
        app.filters.query = "no match".into();
        app.apply_filters();
        assert!(app.task().is_none());
        app.next_attention();
        assert!(app.task().is_none());
        for lanes in [false, true] {
            app.lanes = lanes;
            let mut terminal =
                ratatui::Terminal::new(ratatui::backend::TestBackend::new(80, 20)).unwrap();
            terminal.draw(|f| app.draw(f)).unwrap();
            let text: String = terminal
                .backend()
                .buffer()
                .content
                .iter()
                .map(|c| c.symbol())
                .collect();
            assert!(text.contains("No matching cards"));
        }
    }

    #[test]
    fn lanes_scroll_to_selection_and_preserve_unknown_status() {
        let mut data = fixture();
        for i in 0..12 {
            data.tasks.push(Task {
                id: format!("custom-{i:02}"),
                title: format!("Custom card {i}"),
                status: "custom".into(),
                ..Task::default()
            });
        }
        let mut app = App::new(data.clone(), None);
        app.lanes = true;
        assert_eq!(
            app.lane_groups()
                .iter()
                .map(|(s, _)| s.as_str())
                .collect::<Vec<_>>(),
            ["running", "review", "custom"]
        );
        app.lane_move(KeyCode::Right);
        for _ in 0..11 {
            app.lane_move(KeyCode::Down);
        }
        assert_eq!(app.task().unwrap().id, "custom-11");
        for (width, height) in [(160, 45), (60, 18), (45, 12)] {
            let mut terminal =
                ratatui::Terminal::new(ratatui::backend::TestBackend::new(width, height)).unwrap();
            terminal.draw(|f| app.draw(f)).unwrap();
            assert!(app.lane_hits.iter().any(|(_, id)| id == "custom-11"));
            assert!(
                app.lane_hits
                    .iter()
                    .all(|(r, _)| r.right() <= width && r.bottom() <= height - 2)
            );
        }
        app.lanes = false;
        app.accept(data);
        assert_eq!(app.task().unwrap().id, "custom-11");
        app.lanes = true;
        app.lane_move(KeyCode::Tab);
        assert_eq!(app.task().unwrap().id, "b");
        app.lane_move(KeyCode::BackTab);
        assert_eq!(app.task().unwrap().id, "custom-11");
    }

    #[test]
    fn search_accepts_q_unicode_and_escape_restores_query() {
        let mut app = App::new(fixture(), None);
        app.search = Some(String::new());
        for c in ['q', 'é'] {
            app.search_key(event::KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE));
        }
        assert_eq!(app.filters.query, "qé");
        app.search_key(event::KeyEvent::new(KeyCode::Backspace, KeyModifiers::NONE));
        assert_eq!(app.filters.query, "q");
        app.search_key(event::KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        assert!(app.filters.query.is_empty());
        assert_eq!(app.graph.nodes().count(), 2);
        app.open_filters();
        app.filter_options.push(FilterOption::Status("done".into()));
        app.toggle_filter(app.filter_options.len() - 1);
        assert!(app.filters.show_done);
        assert!(app.filters.statuses.contains("done"));
    }

    #[test]
    fn invalid_graph_does_not_replace_last_success() {
        let mut app = App::new(fixture(), None);
        let updated = app.updated;
        let mut invalid = fixture();
        invalid.tasks.push(invalid.tasks[0].clone());
        app.accept(invalid);
        assert!(app.error.is_some());
        assert_eq!(app.snapshot.tasks.len(), 2);
        assert_eq!(app.updated, updated);
    }

    #[test]
    fn state_is_scoped_and_corruption_is_not_overwritten() {
        let dir = env::temp_dir().join(format!("hermes-kanban-state-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join("boards.json");
        remember(&path, "root-a", "board-a").unwrap();
        remember(&path, "root-b", "board-b").unwrap();
        let state = read_selections(&path).unwrap();
        assert_eq!(state["root-a"], "board-a");
        assert_eq!(state["root-b"], "board-b");
        fs::write(&path, "invalid-json").unwrap();
        assert!(remember(&path, "root-a", "other").is_err());
        assert_eq!(fs::read_to_string(&path).unwrap(), "invalid-json");
        fs::remove_dir_all(&dir).unwrap();
    }
}
