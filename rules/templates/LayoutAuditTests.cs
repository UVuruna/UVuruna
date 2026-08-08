// Guard test - THE SPACE & LEGIBILITY LAW, runtime half, WPF (rules/GUI.md).
//
// TEMPLATE for C# + WPF projects (the default front stack - rules/START.md).
// Copy into the project's test assembly and fill in the Windows registry;
// nothing else should need editing (ALG-8 below is the one exception: a project
// with a real settings file overrides LiveProfileSource()).
//
// It builds every window on an STA thread, measures and arranges it at its
// declared minimum size and at a larger size, walks the visual tree, and fails
// on the same three defects as the Qt audit:
//
//   A. CLIPPED      - an element got less room than its DesiredSize
//   B. ELIDED       - text does not fit its own element
//   C. SCROLL+SLACK - a ScrollViewer scrolls while the window still has unused
//                     space in that axis (measured against what the content
//                     wants under infinite height/width)
//
// plus the precondition: every Window declares MinWidth and MinHeight.
//
// ZUBI v2 - the algorithmic teeth (rules/GUI.md -> "Zubi v2"). No AI in the
// loop; every one of these is measured by plain code:
//
//   ALG-1 EXTREME STATE MATRIX  every slider/selector/toggle is driven through
//                               min / current / max (or every option) and the
//                               layout must still paint inside the window
//   ALG-2 CONTRAST              text vs the background actually PAINTED behind
//                               it (sampled from the offscreen render),
//                               >= 4.5:1, or 3:1 for large text
//   ALG-3 HOVER GEOMETRY        a long plain-string ToolTip that nothing makes
//                               wrap renders as one endless line
//   ALG-4 SPACE CEILING         1600 logical px working width; 2560x1440 is the
//                               ABSOLUTE ceiling; horizontal scroll fails
//   ALG-5 UNIFORM SIBLINGS      same-type buttons in one panel share size +-2px
//   ALG-6 RADIUS BY ASPECT      corner radius bounded by the element's aspect
//                               ratio (a squarish element may not be an egg)
//   ALG-7 ROW OCCUPANCY         at minimum size, rows whose right half stands
//                               empty while content stacks below them
//   ALG-8 LIVE PROFILE          every window is ALSO built from a read-only
//                               COPY of the owner's real settings file
//   ALG-9 SECTION TAXONOMY      helper only (CheckSectionTaxonomy) - a concept
//                               word outside the section named for it
//
// SILENT AUDITS (rules/GUI.md, owner decree 2026-08-06): nothing here ever
// calls Show(). Every pixel this file needs comes from RenderTargetBitmap.
//
// Requires: xunit, and <UseWPF>true</UseWPF> in the test project. Each test
// runs on its own STA thread - WPF refuses to build visuals otherwise.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Xunit;

namespace Project.Tests.Layout;

public static class LayoutAuditRegistry
{
    // Every top-level window and dialog, built in its FULLEST realistic state
    // (longest real strings, most rows) - an empty window proves nothing.
    // A window missing here is a hole in the guard; keep it complete.
    //
    // A factory MUST honour ActiveProfilePath (ALG-8): when it is not null the
    // window is built from THAT settings file instead of the pristine default.
    public static readonly (string Name, Func<Window> Factory)[] Windows =
    {
        // ("SetsDialog", () => new SetsDialog(DemoConfig.Load(ActiveProfilePath))),
    };

    // ALG-8. Set by the audit before the live-profile pass and cleared after:
    // the path of a READ-ONLY COPY of the owner's real settings file. Null for
    // the pristine-default pass. Factories read it; nothing else writes it.
    public static string? ActiveProfilePath;

    public const double SlackTolerance = 24;   // px before free space counts
    public const double TextPadding = 8;       // px assumed frame-to-text

    // The screen every window must survive. A declared minimum bigger than
    // this is the absurd-minimum bug (a two-item menu demanding 6000px):
    // REFLOW, never widen. Raising it needs .claude/layout-frame.json with a
    // stated reason.
    public const double FloorWidth = 1280;
    public const double FloorHeight = 720;

    // --- Zubi v2 thresholds (rules/GUI.md -> "Zubi v2"). Every number here is
    // the rulebook's, not a taste. Do not soften one without changing the LAW.

    // ALG-1: how far outside the window an element may reach before it counts
    // as painting outside it. Rounding slack only.
    public const double BoundsTolerance = 1.0;
    // ALG-1: a Selector with more options than this is a data list, not an
    // enum - the matrix walks enums, not databases.
    public const int MaxAuditedOptions = 12;

    // ALG-2: WCAG contrast. Large text (>= 18px BOLD, or >= 24px at any
    // weight) is allowed the lower bar.
    public const double ContrastMinimum = 4.5;
    public const double ContrastMinimumLarge = 3.0;
    public const double LargeBoldTextSize = 18;
    public const double LargeTextSize = 24;

    // ALG-3: a tooltip line longer than this must be made to wrap.
    public const int ToolTipLineLimit = 72;

    // ALG-4: the ladder in logical px. 1600 is the working width for a desktop
    // settings page; 2560x1440 is the ABSOLUTE ceiling with no exception.
    public const double WorkingWidth = 1600;
    public const double CeilingWidth = 2560;
    public const double CeilingHeight = 1440;

    // ALG-5: same-type siblings may differ by this much and no more.
    public const double SiblingTolerance = 2;

    // ALG-7: band height in px, how empty a band's right half may be, how many
    // such bands in a row convict, and how far a pixel must sit from the
    // background colour before it counts as content.
    public const int BandHeight = 48;
    public const double SparseRightHalf = 0.55;
    public const int SparseBandRun = 2;
    public const int BackgroundDelta = 12;

    // ALG-9: the concept words that own a section. Extend per project - the
    // owner's vocabulary is the one that counts.
    public static readonly string[] ConceptWords =
        { "size", "width", "height", "color", "colour", "opacity", "font" };

    // Screenshots the agent must OPEN and grade (>= 8/10) before the session
    // may end - the Stop half of rules/hooks/layout_guard.py checks both.
    public static readonly string ShotDir =
        Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..",
                     ".claude", "shots");
}

public class LayoutAuditTests
{
    public static IEnumerable<object[]> AllWindows() =>
        LayoutAuditRegistry.Windows.Select(w => new object[] { w.Name });

    /// ALG-8 LIVE PROFILE. Return the path of the OWNER'S REAL settings file
    /// and every window is audited a SECOND time, built from a read-only copy
    /// of it. Null (the default) means only the pristine default is audited -
    /// which is exactly the hole ALG-8 was written to close, so a project that
    /// HAS a settings file must fill this in.
    ///
    /// The template is copied into the project, so the normal path is to edit
    /// this method here. Overriding it in a subclass also works, but note that
    /// xunit then discovers the [Theory] twice (base + derived).
    protected virtual string? LiveProfileSource() => null;

    [Theory]
    [MemberData(nameof(AllWindows))]
    public void Layout_Audit(string name)
    {
        var problems = RunSta(() => AuditAllProfiles(name));
        Assert.True(problems.Count == 0,
            "THE SPACE & LEGIBILITY LAW (rules/GUI.md) - runtime audit failed:\n  "
            + string.Join("\n  ", problems)
            + "\nLadder: (1) the starving element takes the free space, "
            + "(2) reflow into more rows, (3) raise the window minimum, "
            + "(4) scroll only when the window is genuinely full."
            + "\nALG-* failures are Zubi v2 (rules/GUI.md -> Zubi v2) - each "
            + "message names its rule and what to change.");
    }

    // --- the run: pristine default first, the owner's real profile second ----

    private List<string> AuditAllProfiles(string name)
    {
        var problems = Audit(name, "default profile", saveShot: true);

        var source = LiveProfileSource();
        if (string.IsNullOrWhiteSpace(source))
        {
            Console.WriteLine("ALG-8 LIVE PROFILE: no source declared - only "
                + "the pristine default was audited. A project with a settings "
                + "file MUST override LiveProfileSource().");
            return problems;
        }

        if (!File.Exists(source))
        {
            problems.Add("ALG-8 LIVE PROFILE (rules/GUI.md -> Zubi v2): "
                + $"LiveProfileSource() points at '{source}', which does not "
                + "exist - either fix the path or return null and say so. A "
                + "silently skipped live-profile pass is the hole ALG-8 closes");
            return problems;
        }

        var copy = ReadOnlyCopyOf(source);
        var before = problems.Count;
        try
        {
            LayoutAuditRegistry.ActiveProfilePath = copy;
            problems.AddRange(Audit(name, "live profile", saveShot: false));
        }
        finally
        {
            LayoutAuditRegistry.ActiveProfilePath = null;
            TryDelete(copy);
        }

        if (problems.Count > before)
            problems.Add("ALG-8 LIVE PROFILE (rules/GUI.md -> Zubi v2): the "
                + "failures tagged 'live profile' came from a READ-ONLY COPY of "
                + $"the owner's real settings ({source}). They are this "
                + "session's to fix - \"that is the environment, not this "
                + "change\" is not a legal sentence in any proof file");

        return problems;
    }

    private static List<string> Audit(string name, string profile, bool saveShot)
    {
        var entry = LayoutAuditRegistry.Windows.First(w => w.Name == name);
        var window = entry.Factory();
        var problems = new List<string>();

        if (double.IsNaN(window.MinWidth) || window.MinWidth <= 0 ||
            double.IsNaN(window.MinHeight) || window.MinHeight <= 0)
        {
            problems.Add($"[{name}] no declared minimum size - the law requires "
                + "MinWidth/MinHeight, COMPUTED from the longest real content");
            return problems;
        }

        if (window.MinWidth > LayoutAuditRegistry.FloorWidth ||
            window.MinHeight > LayoutAuditRegistry.FloorHeight)
        {
            problems.Add($"[{name}] ABSURD MINIMUM {window.MinWidth:0}x"
                + $"{window.MinHeight:0} - it does not fit the screen floor "
                + $"{LayoutAuditRegistry.FloorWidth:0}x"
                + $"{LayoutAuditRegistry.FloorHeight:0}, so the window demands "
                + "a screen the user does not have. REFLOW it (ladder step 2); "
                + "widening your way out is the bug itself");
            return problems;
        }

        foreach (var (label, width, height) in new[]
        {
            ("minimum", window.MinWidth, window.MinHeight),
            ("minimum+50%", window.MinWidth * 1.5, window.MinHeight * 1.5),
        })
        {
            Relayout(window, width, height);

            var tag = $"[{name} @ {profile} @ {label} {width:0}x{height:0}]";

            // Geometry checks first: they need a layout nobody has dirtied.
            problems.AddRange(Clipped(window).Select(p => $"{tag} {p}"));
            problems.AddRange(Elided(window).Select(p => $"{tag} {p}"));
            problems.AddRange(UniformSiblings(window).Select(p => $"{tag} {p}"));
            problems.AddRange(RadiusByAspect(window).Select(p => $"{tag} {p}"));

            if (label == "minimum")
                problems.AddRange(HoverGeometry(window, width)
                    .Select(p => $"{tag} {p}"));

            // These two re-measure the content under an infinite constraint,
            // which leaves the layout dirty - hence the Relayout after them.
            problems.AddRange(ScrollWithSlack(window, width, height)
                .Select(p => $"{tag} {p}"));
            problems.AddRange(SpaceCeiling(window, width, height)
                .Select(p => $"{tag} {p}"));
            Relayout(window, width, height);

            // Pixel checks: one offscreen render feeds ALG-2, ALG-7 and (at the
            // minimum size, on the default profile) the screenshot to grade.
            var bitmap = TryRender(window, width, height, out var renderFailure);
            if (bitmap == null)
            {
                problems.Add($"{tag} ALG-2 CONTRAST / ALG-7 ROW OCCUPANCY "
                    + "(rules/GUI.md -> Zubi v2): the window could not be "
                    + $"rendered offscreen ({renderFailure}), so neither rule "
                    + "could be proven. An audit that cannot see the pixels "
                    + "proves nothing - fix the offscreen render path");
            }
            else
            {
                var pixels = new Pixels(bitmap, OpaqueBackdrop(window));

                if (pixels.IsBlank())
                {
                    // Reported, never judged: sampling a transparent render
                    // would grade the assumed backdrop against itself and
                    // invent contrast failures out of nothing.
                    problems.Add($"{tag} ALG-2 CONTRAST / ALG-7 ROW OCCUPANCY "
                        + "(rules/GUI.md -> Zubi v2): the offscreen render came "
                        + "out completely transparent - the window painted "
                        + "nothing. Measure/Arrange/UpdateLayout ran, so the "
                        + "cause is in the window itself (no Background, or a "
                        + "template that needs a shown window). Neither pixel "
                        + "rule could be proven until that is fixed");
                }
                else
                {
                    problems.AddRange(Contrast(window, pixels)
                        .Select(p => $"{tag} {p}"));

                    if (label == "minimum")
                        problems.AddRange(RowOccupancy(pixels)
                            .Select(p => $"{tag} {p}"));
                }

                if (label == "minimum" && saveShot)
                {
                    var shot = Save(bitmap, name);
                    Console.WriteLine($"SHOT {shot} - MIN {width:0}x{height:0}"
                        + " - now OPEN it and GRADE it (>= 8/10) in "
                        + ".claude/layout-proof.md");
                }
            }

            // Last, because it drives controls through their extremes and then
            // restores them - anything measured after it would race the restore.
            problems.AddRange(ExtremeStates(window, width, height)
                .Select(p => $"{tag} {p}"));
        }

        return problems;
    }

    /// One full layout pass at a given size. The dispatcher is drained first so
    /// that bindings queued by a state change (ALG-1) have actually reached the
    /// controls before anything is measured - without a message pump a WPF test
    /// measures the layout of one frame ago.
    private static void Relayout(Window window, double width, double height)
    {
        DrainDispatcher();
        window.Width = width;
        window.Height = height;
        window.Measure(new Size(width, height));
        window.Arrange(new Rect(0, 0, width, height));
        window.UpdateLayout();
    }

    /// Pumps the STA thread's dispatcher until it is idle, with a hard stop so
    /// a window that keeps posting work (an animation, a timer) can never hang
    /// the test run.
    private static void DrainDispatcher()
    {
        var dispatcher = Dispatcher.CurrentDispatcher;
        var frame = new DispatcherFrame();
        dispatcher.BeginInvoke(DispatcherPriority.Background,
            new Action(() => frame.Continue = false));
        var stop = new DispatcherTimer(TimeSpan.FromSeconds(2),
            DispatcherPriority.Send, (_, _) => frame.Continue = false,
            dispatcher);
        try { Dispatcher.PushFrame(frame); }
        finally { stop.Stop(); }
    }

    /// The offscreen render every pixel check and the screenshot come from.
    /// 96 DPI is deliberate: it makes one bitmap pixel one LOGICAL pixel, so
    /// every threshold in this file stays in the units the layout uses.
    private static RenderTargetBitmap? TryRender(Window window, double width,
                                                 double height,
                                                 out string? failure)
    {
        failure = null;
        var pixelWidth = (int)Math.Round(width);
        var pixelHeight = (int)Math.Round(height);
        if (pixelWidth <= 0 || pixelHeight <= 0)
        {
            failure = $"the window measures {pixelWidth}x{pixelHeight}";
            return null;
        }

        try
        {
            var bitmap = new RenderTargetBitmap(
                pixelWidth, pixelHeight, 96, 96, PixelFormats.Pbgra32);
            bitmap.Render(window);
            return bitmap;
        }
        catch (Exception exception)
        {
            // Reported as a failure, never swallowed - see the caller.
            failure = $"{exception.GetType().Name}: {exception.Message}";
            return null;
        }
    }

    /// The screenshot the agent must OPEN and grade. A GUI nobody looked at is
    /// a GUI nobody checked.
    private static string Save(RenderTargetBitmap bitmap, string name)
    {
        Directory.CreateDirectory(LayoutAuditRegistry.ShotDir);
        var path = Path.GetFullPath(
            Path.Combine(LayoutAuditRegistry.ShotDir, $"{name}.png"));
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = File.Create(path);
        encoder.Save(stream);
        return path;
    }

    // --- the three original checks -----------------------------------------

    private static IEnumerable<string> Clipped(DependencyObject root) =>
        Descendants(root).OfType<FrameworkElement>()
            .Where(e => IsRenderVisible(e))
            .Where(e => e.DesiredSize.Width > e.ActualWidth + 0.5
                     || e.DesiredSize.Height > e.ActualHeight + 0.5)
            .Select(e => $"CLIPPED {e.GetType().Name} '{e.Name}': has "
                + $"{e.ActualWidth:0}x{e.ActualHeight:0}, wants "
                + $"{e.DesiredSize.Width:0}x{e.DesiredSize.Height:0}");

    private static IEnumerable<string> Elided(DependencyObject root)
    {
        foreach (var element in Descendants(root).OfType<FrameworkElement>()
                     .Where(e => IsRenderVisible(e)))
        {
            var text = TextOf(element);
            if (string.IsNullOrEmpty(text)) continue;
            if (element is TextBlock { TextWrapping: not TextWrapping.NoWrap })
                continue;   // wrapped text is judged by the CLIPPED check

            var needed = MeasureText(element, text);
            var available = element.ActualWidth - LayoutAuditRegistry.TextPadding;
            if (needed > available)
                yield return $"ELIDED {element.GetType().Name} "
                    + $"'{Truncate(text)}': text needs {needed:0}px, element "
                    + $"offers {available:0}px";
        }
    }

    private static IEnumerable<string> ScrollWithSlack(
        Window window, double width, double height)
    {
        // What the content genuinely wants when nothing constrains it. If the
        // window is TALLER than that and something still scrolls, the free
        // space went to a filler instead of to the starving element.
        var root = (FrameworkElement)window.Content;
        root.Measure(new Size(width, double.PositiveInfinity));
        var wantedHeight = root.DesiredSize.Height;
        root.Measure(new Size(double.PositiveInfinity, height));
        var wantedWidth = root.DesiredSize.Width;

        var freeVertical = height - wantedHeight;
        var freeHorizontal = width - wantedWidth;

        foreach (var viewer in Descendants(window).OfType<ScrollViewer>()
                     .Where(v => IsRenderVisible(v)))
        {
            if (viewer.ScrollableHeight > 0
                && freeVertical > LayoutAuditRegistry.SlackTolerance)
                yield return $"SCROLL+SLACK ScrollViewer '{viewer.Name}' "
                    + $"scrolls vertically ({viewer.ScrollableHeight:0}px "
                    + $"hidden) while the window holds {freeVertical:0}px of "
                    + "unused height - ladder step 1: the starving element "
                    + "takes the free space before any scrollbar appears";

            if (viewer.ScrollableWidth > 0
                && freeHorizontal > LayoutAuditRegistry.SlackTolerance)
                yield return $"SCROLL+SLACK ScrollViewer '{viewer.Name}' "
                    + $"scrolls horizontally ({viewer.ScrollableWidth:0}px "
                    + $"hidden) while the window holds {freeHorizontal:0}px of "
                    + "unused width - ladder step 1 applies the same way";
        }
    }

    // --- ALG-1 EXTREME STATE MATRIX ----------------------------------------
    //
    // "Tested" without extremes is not tested. Every slider goes to its minimum
    // and its maximum, every enum-sized selector through all of its options,
    // every toggle through both (three, if it is three-state) - and after each
    // change the whole tree is re-measured and nothing may paint outside the
    // window.
    //
    // Read-only ranges (ProgressBar, ScrollBar) are skipped: they display state,
    // they do not hold it. Elements a ScrollViewer or a ClipToBounds ancestor
    // clips are skipped too - their box may reach past the window, their PAINT
    // cannot. Every value is restored from a snapshot taken BEFORE any change,
    // because checking one radio button silently unchecks its whole group.
    //
    // Two limits worth knowing. The control list is taken ONCE, before the first
    // change: controls that only come into existence in another tab (a
    // TabControl realises one tab at a time) are never driven through their own
    // extremes - register that tab's content as its own entry in the Windows
    // registry if it matters. And an element parked outside the window by
    // design (a slide-out panel at rest) is reported once, as the default
    // state, then excluded from the per-state reports.

    private static List<string> ExtremeStates(Window window, double width,
                                              double height)
    {
        var problems = new List<string>();
        var controls = Descendants(window).OfType<Control>()
                           .Where(c => IsRenderVisible(c)).ToList();
        var restore = new List<Action>();

        foreach (var control in controls)
        {
            if (control is RangeBase range && !IsReadOnlyRange(range))
            {
                var original = range.Value;
                restore.Add(() => range.Value = original);
            }
            else if (control is Selector selector && IsAuditableSelector(selector))
            {
                var original = selector.SelectedIndex;
                restore.Add(() => selector.SelectedIndex = original);
            }
            else if (control is ToggleButton toggle)
            {
                var original = toggle.IsChecked;
                restore.Add(() => toggle.IsChecked = original);
            }
        }

        // Anything already outside the window in the DEFAULT state is reported
        // once, here, and then excluded - otherwise a single permanent offender
        // would repeat itself once per state and bury the real findings.
        var baseline = new HashSet<FrameworkElement>();
        foreach (var (element, bounds) in OutOfBounds(window, width, height))
        {
            baseline.Add(element);
            problems.Add(Outside(element, bounds, width, height,
                                 "the window's default state"));
        }

        try
        {
            foreach (var control in controls)
            {
                if (control is RangeBase range && !IsReadOnlyRange(range))
                {
                    var states = new[]
                    {
                        ("minimum", range.Minimum),
                        ("current", range.Value),
                        ("maximum", range.Maximum),
                    };
                    foreach (var (state, value) in states)
                    {
                        if (double.IsNaN(value) || double.IsInfinity(value))
                            continue;
                        range.Value = value;
                        problems.AddRange(StateProblems(window, width, height,
                            baseline,
                            $"{Describe(range)} at {state} (Value={value:0.###})"));
                    }
                }
                else if (control is Selector selector
                         && IsAuditableSelector(selector))
                {
                    var options = selector.Items.Count;
                    for (var index = 0; index < options; index++)
                    {
                        selector.SelectedIndex = index;
                        problems.AddRange(StateProblems(window, width, height,
                            baseline,
                            $"{Describe(selector)} showing option "
                            + $"{index + 1} of {options}"));
                    }
                }
                else if (control is ToggleButton toggle)
                {
                    var states = toggle.IsThreeState
                        ? new bool?[] { false, true, null }
                        : new bool?[] { false, true };
                    foreach (var state in states)
                    {
                        toggle.IsChecked = state;
                        problems.AddRange(StateProblems(window, width, height,
                            baseline,
                            $"{Describe(toggle)} with IsChecked="
                            + $"{(state.HasValue ? state.Value.ToString() : "null")}"));
                    }
                }
            }
        }
        finally
        {
            for (var i = restore.Count - 1; i >= 0; i--) restore[i]();
            Relayout(window, width, height);
        }

        return problems;
    }

    private static IEnumerable<string> StateProblems(
        Window window, double width, double height,
        HashSet<FrameworkElement> baseline, string state)
    {
        Relayout(window, width, height);
        return OutOfBounds(window, width, height)
            .Where(hit => !baseline.Contains(hit.Element))
            .Select(hit => Outside(hit.Element, hit.Bounds, width, height, state));
    }

    private static string Outside(FrameworkElement element, Rect bounds,
                                  double width, double height, string state)
        => "ALG-1 EXTREME STATE MATRIX (rules/GUI.md -> Zubi v2): with "
         + $"{state}, {Describe(element)} paints outside the window - its box "
         + $"is {bounds.X:0},{bounds.Y:0} {bounds.Width:0}x{bounds.Height:0} "
         + $"inside a {width:0}x{height:0} window. Every state the user can "
         + "reach must hold: bound the element (MaxWidth/MaxHeight), reflow the "
         + "row, or let the container scroll - never let a value push content "
         + "off the window";

    private static List<(FrameworkElement Element, Rect Bounds)> OutOfBounds(
        Window window, double width, double height)
    {
        var hits = new List<(FrameworkElement, Rect)>();
        var slack = LayoutAuditRegistry.BoundsTolerance;

        foreach (var element in Descendants(window).OfType<FrameworkElement>()
                     .Where(e => IsRenderVisible(e)))
        {
            if (element.ActualWidth <= 0 || element.ActualHeight <= 0) continue;
            if (IsClippedByAncestor(element, window)) continue;

            var bounds = BoundsIn(window, element);
            if (bounds == null) continue;

            var box = bounds.Value;
            if (box.Left < -slack || box.Top < -slack
                || box.Right > width + slack || box.Bottom > height + slack)
                hits.Add((element, box));
        }

        return hits;
    }

    private static bool IsReadOnlyRange(RangeBase range) =>
        range is ProgressBar || range is ScrollBar;

    private static bool IsAuditableSelector(Selector selector) =>
        selector.Items.Count > 0
        && selector.Items.Count <= LayoutAuditRegistry.MaxAuditedOptions;

    // --- ALG-2 CONTRAST -----------------------------------------------------
    //
    // Text against the background ACTUALLY PAINTED behind it, not against the
    // background someone declared. The element's foreground brush is composed
    // over the colour sampled from the offscreen render inside the element's
    // own box - the mode (most common colour) of that box, because glyphs are
    // always the minority of the pixels a text element covers.
    //
    // Heuristic, stated plainly:
    //   * only SolidColorBrush foregrounds are judged (a gradient or an image
    //     brush has no single colour; those need the human grader);
    //   * the mode of the element's box is taken as its background - correct
    //     for a label on a panel and for a filled button alike, wrong for text
    //     laid over a photograph or a gradient, where it picks the dominant
    //     tone rather than the worst one;
    //   * a ContentControl whose generated TextBlock carries the same string is
    //     skipped, so a Button and its inner TextBlock do not both report;
    //   * the element's own Opacity and the brush's Opacity are folded in;
    //     an ANCESTOR's Opacity is not.

    private static IEnumerable<string> Contrast(Window window, Pixels pixels)
    {
        foreach (var element in Descendants(window).OfType<FrameworkElement>()
                     .Where(e => IsRenderVisible(e)))
        {
            var text = TextOf(element);
            if (string.IsNullOrWhiteSpace(text)) continue;
            if (element.ActualWidth < 2 || element.ActualHeight < 2) continue;

            // The presenter's generated TextBlock is the thing that paints.
            if (element is not TextBlock
                && Descendants(element).OfType<TextBlock>()
                       .Any(inner => inner.Text == text))
                continue;

            var brush = ForegroundOf(element) as SolidColorBrush;
            if (brush == null) continue;

            var bounds = BoundsIn(window, element);
            if (bounds == null) continue;

            var background = pixels.Mode(bounds.Value);
            var foreground = Over(brush.Color, brush.Opacity * element.Opacity,
                                  background);

            var large = IsLargeText(element);
            var required = large
                ? LayoutAuditRegistry.ContrastMinimumLarge
                : LayoutAuditRegistry.ContrastMinimum;
            var ratio = ContrastRatio(foreground, background);

            if (ratio < required - 0.05)
                yield return "ALG-2 CONTRAST (rules/GUI.md -> Zubi v2): "
                    + $"{Describe(element)} paints {Hex(foreground)} on "
                    + $"{Hex(background)} - {ratio:0.0}:1, below the "
                    + $"{required:0.0}:1 required for "
                    + (large ? "large text" : "body text")
                    + ". Darken the text or lighten the surface until the ratio "
                    + "is met (background sampled from the offscreen render, "
                    + "most common colour inside the element's box)";
        }
    }

    /// The effective foreground: TextBlock and Control expose the same
    /// inherited TextElement.Foreground property, and anything else is asked
    /// for that property directly so inheritance still answers.
    private static Brush? ForegroundOf(FrameworkElement element) => element switch
    {
        TextBlock t => t.Foreground,
        Control c => c.Foreground,
        _ => element.GetValue(
                 System.Windows.Documents.TextElement.ForegroundProperty) as Brush,
    };

    /// WCAG "large text": >= 18px BOLD (the task's threshold) or >= 24px at any
    /// weight (WCAG's 18pt). Anything else is body text at 4.5:1.
    private static bool IsLargeText(FrameworkElement element)
    {
        double size;
        FontWeight weight;

        if (element is TextBlock textBlock)
        {
            size = textBlock.FontSize;
            weight = textBlock.FontWeight;
        }
        else if (element is Control control)
        {
            size = control.FontSize;
            weight = control.FontWeight;
        }
        else
        {
            // Safety net for a custom FrameworkElement that carries text: ask
            // the inherited properties, and fall back to the system font rather
            // than unbox a value that may not be there.
            size = element.GetValue(
                       System.Windows.Documents.TextElement.FontSizeProperty)
                   is double inherited ? inherited : SystemFonts.MessageFontSize;
            weight = element.GetValue(
                         System.Windows.Documents.TextElement.FontWeightProperty)
                     is FontWeight inheritedWeight
                         ? inheritedWeight : FontWeights.Normal;
        }

        var bold = weight.ToOpenTypeWeight()
                   >= FontWeights.Bold.ToOpenTypeWeight();
        return (bold && size >= LayoutAuditRegistry.LargeBoldTextSize)
            || size >= LayoutAuditRegistry.LargeTextSize;
    }

    /// Source over destination, straight (non-premultiplied) alpha.
    private static Color Over(Color source, double opacity, Color under)
    {
        var alpha = Math.Clamp(source.A / 255.0 * opacity, 0.0, 1.0);
        return Color.FromRgb(
            (byte)Math.Round(source.R * alpha + under.R * (1 - alpha)),
            (byte)Math.Round(source.G * alpha + under.G * (1 - alpha)),
            (byte)Math.Round(source.B * alpha + under.B * (1 - alpha)));
    }

    private static double ContrastRatio(Color first, Color second)
    {
        var one = RelativeLuminance(first);
        var two = RelativeLuminance(second);
        var lighter = Math.Max(one, two);
        var darker = Math.Min(one, two);
        return (lighter + 0.05) / (darker + 0.05);
    }

    private static double RelativeLuminance(Color color) =>
        0.2126 * SrgbChannel(color.R)
        + 0.7152 * SrgbChannel(color.G)
        + 0.0722 * SrgbChannel(color.B);

    private static double SrgbChannel(byte value)
    {
        var channel = value / 255.0;
        return channel <= 0.03928
            ? channel / 12.92
            : Math.Pow((channel + 0.055) / 1.055, 2.4);
    }

    private static string Hex(Color color) =>
        $"#{color.R:X2}{color.G:X2}{color.B:X2}";

    /// What the render is composed over: Pbgra32 starts fully transparent, so
    /// a window with a see-through background needs a stated backdrop. Its own
    /// Background is the honest one; white is the fallback.
    private static Color OpaqueBackdrop(Window window)
    {
        if (window.Background is SolidColorBrush brush)
            return Color.FromRgb(brush.Color.R, brush.Color.G, brush.Color.B);
        return Colors.White;
    }

    // --- ALG-3 HOVER GEOMETRY -----------------------------------------------
    //
    // A tooltip is invisible to a widget-tree walk until it opens, and opening
    // one would put a window on the owner's screen (Silent Audits). So this is
    // a STATIC check of what the tooltip WOULD render, and its heuristic is
    // stated openly:
    //
    //   a plain string handed to the default ToolTip template renders on ONE
    //   line, as wide as the string. Longer than 72 characters (or wider than
    //   the window) it must therefore be made to wrap, and the only wrapping
    //   this check can SEE is (a) a TextBlock with TextWrapping != NoWrap used
    //   as the tooltip content, or (b) an implicit ToolTip style in the
    //   element's resource chain that sets Template or ContentTemplate - which
    //   is taken at its word, because a template's wrapping cannot be measured
    //   without instantiating it.
    //
    // A tooltip whose content is a composed visual (a Grid, a UserControl) is
    // skipped: register it in the Windows list if it deserves auditing.
    // The single-line width is measured with the HOST element's font, not the
    // tooltip's - an approximation, and always the cheaper of the two errors.
    // Visibility is deliberately NOT filtered here: a tooltip on a panel that
    // is collapsed right now is still text the user will meet later.

    private static IEnumerable<string> HoverGeometry(Window window, double width)
    {
        foreach (var element in Descendants(window).OfType<FrameworkElement>())
        {
            var tip = element.ToolTip;
            if (tip == null) continue;

            string? text = null;
            var wraps = false;

            if (tip is string plain)
            {
                text = plain;
            }
            else if (tip is TextBlock block)
            {
                text = block.Text;
                wraps = block.TextWrapping != TextWrapping.NoWrap;
            }
            else if (tip is ToolTip tooltip)
            {
                if (tooltip.Content is string inner)
                {
                    text = inner;
                }
                else if (tooltip.Content is TextBlock innerBlock)
                {
                    text = innerBlock.Text;
                    wraps = innerBlock.TextWrapping != TextWrapping.NoWrap;
                }
            }

            if (string.IsNullOrEmpty(text)) continue;
            if (wraps) continue;
            if (ToolTipWrapDiscoverable(element)) continue;

            var singleLine = MeasureText(element, text);
            if (text.Length <= LayoutAuditRegistry.ToolTipLineLimit
                && singleLine <= width)
                continue;

            yield return "ALG-3 HOVER GEOMETRY (rules/GUI.md -> Zubi v2): "
                + $"{Describe(element)} carries a plain-string ToolTip of "
                + $"{text.Length} characters (~{singleLine:0}px on one line, "
                + $"the window is {width:0}px wide) and nothing in scope makes "
                + "it wrap. Give it a TextBlock with TextWrapping='Wrap' and a "
                + "MaxWidth as the ToolTip content, or an implicit ToolTip "
                + $"style whose ContentTemplate wraps. Text: '{Truncate(text)}'";
        }
    }

    private static bool ToolTipWrapDiscoverable(FrameworkElement element)
    {
        var style = element.TryFindResource(typeof(ToolTip)) as Style;
        if (style == null) return false;

        foreach (var setter in style.Setters.OfType<Setter>())
        {
            if (setter.Property == Control.TemplateProperty
                || setter.Property == ContentControl.ContentTemplateProperty
                || setter.Property == TextBlock.TextWrappingProperty)
                return true;
        }
        return false;
    }

    // --- ALG-4 SPACE CEILING -------------------------------------------------
    //
    // Logical pixels, because those are the units a layout is written in.
    // 1600 is the working width of a desktop settings page; 2560x1440 is the
    // ABSOLUTE ceiling - a window that wants more is demanding the user's whole
    // screen. Horizontal scrolling on a settings page fails at every step.
    //
    // What the window WANTS is measured the way SCROLL+SLACK measures it: the
    // content under an infinite constraint in one axis at a time. One
    // deliberate exception on the height: when a vertical ScrollViewer governs
    // the content, the page bounds itself by scrolling and its unconstrained
    // height is the length of a list, not a demand for a taller screen - that
    // case is SCROLL+SLACK's to judge, not this one's.

    private static List<string> SpaceCeiling(Window window, double width,
                                             double height)
    {
        var problems = new List<string>();

        // Read the scroll state BEFORE the infinite measures dirty the layout.
        foreach (var viewer in Descendants(window).OfType<ScrollViewer>()
                     .Where(v => IsRenderVisible(v)))
        {
            if (viewer.ScrollableWidth > 0.5)
                problems.Add("ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): "
                    + $"ScrollViewer '{viewer.Name}' scrolls HORIZONTALLY "
                    + $"({viewer.ScrollableWidth:0}px hidden). A settings page "
                    + "that scrolls sideways fails regardless of its size - "
                    + "reflow into rows, or narrow the widest child");
        }

        if (window.MinWidth > LayoutAuditRegistry.CeilingWidth
            || window.MinHeight > LayoutAuditRegistry.CeilingHeight)
            problems.Add("ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): "
                + $"declared minimum {window.MinWidth:0}x{window.MinHeight:0} "
                + $"passes {LayoutAuditRegistry.CeilingWidth:0}x"
                + $"{LayoutAuditRegistry.CeilingHeight:0} - ABSOLUTE ceiling, "
                + "no exception, no written excuse. That is a fullscreen demand");

        var root = window.Content as FrameworkElement;
        if (root == null) return problems;

        root.Measure(new Size(double.PositiveInfinity, height));
        var wantedWidth = root.DesiredSize.Width;
        root.Measure(new Size(width, double.PositiveInfinity));
        var wantedHeight = root.DesiredSize.Height;

        if (wantedWidth > LayoutAuditRegistry.CeilingWidth)
            problems.Add("ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): the "
                + $"content wants {wantedWidth:0} logical px of width - past "
                + $"the {LayoutAuditRegistry.CeilingWidth:0}x"
                + $"{LayoutAuditRegistry.CeilingHeight:0} ABSOLUTE ceiling, no "
                + "exception, no written excuse. Reflow into rows");
        else if (wantedWidth > LayoutAuditRegistry.WorkingWidth)
            problems.Add("ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): the "
                + $"content wants {wantedWidth:0} logical px of width, past the "
                + $"{LayoutAuditRegistry.WorkingWidth:0}px working width for a "
                + "desktop page. Exhaust reflow first; a step up the ladder is "
                + "legal only with the reason written down");

        var scrolls = Descendants(window).OfType<ScrollViewer>()
            .Any(v => IsRenderVisible(v)
                   && v.VerticalScrollBarVisibility != ScrollBarVisibility.Disabled);

        if (!scrolls && wantedHeight > LayoutAuditRegistry.CeilingHeight)
            problems.Add("ALG-4 SPACE CEILING (rules/GUI.md -> Zubi v2): the "
                + $"content wants {wantedHeight:0} logical px of height with "
                + "nothing scrolling - past the "
                + $"{LayoutAuditRegistry.CeilingHeight:0}px ABSOLUTE ceiling, "
                + "no exception. Reflow into columns, or let the page scroll");

        return problems;
    }

    // --- ALG-5 UNIFORM SIBLINGS ---------------------------------------------
    //
    // A control's size never depends on the length of its own text: the widest
    // content decides, and every same-kind sibling in the same container takes
    // that size (+-2px). Only direct children of one Panel are compared, and
    // only button-shaped ones, grouped by exact type - a Button and a
    // ToggleButton beside each other are two families, not one.
    //
    // Known false positive: a Grid where one button deliberately spans more
    // columns than its neighbours (a numpad's wide zero, a "Apply to all"
    // beside OK/Cancel). Such a layout should put the odd one in its own
    // container, which is also what makes the intent readable.

    private static IEnumerable<string> UniformSiblings(Window window)
    {
        foreach (var panel in Descendants(window).OfType<Panel>())
        {
            var families = panel.Children.OfType<ButtonBase>()
                .Where(b => IsRenderVisible(b)
                         && b.ActualWidth > 0 && b.ActualHeight > 0)
                .GroupBy(b => b.GetType());

            foreach (var family in families)
            {
                var members = family.ToList();
                if (members.Count < 2) continue;

                foreach (var vertical in new[] { false, true })
                {
                    var sizes = members
                        .Select(m => vertical ? m.ActualHeight : m.ActualWidth)
                        .ToList();
                    var spread = sizes.Max() - sizes.Min();
                    if (spread <= LayoutAuditRegistry.SiblingTolerance) continue;

                    var narrowest = members[sizes.IndexOf(sizes.Min())];
                    var widest = members[sizes.IndexOf(sizes.Max())];
                    var axis = vertical ? "height" : "width";

                    yield return "ALG-5 UNIFORM SIBLINGS (rules/GUI.md -> "
                        + $"Zubi v2): {members.Count} {family.Key.Name} children "
                        + $"of {Describe(panel)} differ in {axis} by "
                        + $"{spread:0}px (tolerance "
                        + $"{LayoutAuditRegistry.SiblingTolerance:0}px): "
                        + $"{Describe(narrowest)} is {sizes.Min():0}, "
                        + $"{Describe(widest)} is {sizes.Max():0}. The widest "
                        + $"content decides - give the family one {axis} "
                        + "(a UniformGrid, a shared style, or equal Grid "
                        + "columns), so no control is sized by its own text";
                }
            }
        }
    }

    // --- ALG-6 RADIUS BY ASPECT RATIO ---------------------------------------
    //
    // AR = width / height.
    //   AR >= 2   : up to 50% of the height (a pill is legitimate when wide)
    //   1.4 - 2   : up to 30% of the height
    //   AR < 1.4  : up to 15% of the SHORTER side - squarish and portrait boxes
    //               are where circles and eggs are born
    //
    // Borders inside control templates are walked too, so a rounded Button is
    // judged by the Border its template draws. True-circle content (a colour
    // swatch, an avatar) is exempt through Tag="radius-ok:<reason>" on the
    // element or on any ancestor up to the window - the reason is written down,
    // never assumed.
    //
    // Not implemented here: the "inner content inset >= 0.3*r" half of ALG-6.
    // It needs the content's box relative to the rounded corner and is left to
    // the human grader for now.

    private static IEnumerable<string> RadiusByAspect(Window window)
    {
        foreach (var border in Descendants(window).OfType<Border>()
                     .Where(b => IsRenderVisible(b)))
        {
            var width = border.ActualWidth;
            var height = border.ActualHeight;
            if (width < 1 || height < 1) continue;

            var corners = border.CornerRadius;
            var largest = Math.Max(
                Math.Max(corners.TopLeft, corners.TopRight),
                Math.Max(corners.BottomLeft, corners.BottomRight));
            if (largest <= 0.5) continue;
            if (HasExemption(border, window, "radius-ok")) continue;

            var ratio = width / height;
            double allowed;
            string band;

            if (ratio >= 2)
            {
                allowed = 0.50 * height;
                band = "AR >= 2 allows up to 50% of the height";
            }
            else if (ratio >= 1.4)
            {
                allowed = 0.30 * height;
                band = "1.4 <= AR < 2 allows up to 30% of the height";
            }
            else
            {
                allowed = 0.15 * Math.Min(width, height);
                band = "AR < 1.4 allows up to 15% of the shorter side";
            }

            if (largest <= allowed + 0.5) continue;

            // A Border drawn by a control template belongs to that control in
            // every message - "Border '-'" tells a developer nothing.
            var owner = border.TemplatedParent as FrameworkElement;
            var subject = owner == null
                ? Describe(border)
                : $"{Describe(border)} in the template of {Describe(owner)}";

            yield return "ALG-6 RADIUS BY ASPECT RATIO (rules/GUI.md -> "
                    + $"Zubi v2): {subject} is {width:0}x"
                    + $"{height:0} (AR {ratio:0.00}) with a corner radius of "
                    + $"{largest:0.#} - {band}, i.e. at most {allowed:0.#}. "
                    + "Lower the radius, or widen the element until the shape "
                    + "earns it. A true circle (colour swatch, avatar) is exempt "
                    + "with Tag=\"radius-ok:<reason>\" on it or on an ancestor";
        }
    }

    // --- ALG-7 ROW OCCUPANCY -------------------------------------------------
    //
    // The measurable form of "nothing starves beside empty space". At the
    // MINIMUM size the render is cut into ~48px horizontal bands; a band that
    // carries content on its left half while more than 55% of its right half's
    // COLUMNS stand empty is sparse. Two sparse bands in a row, with content
    // still stacking below them, fail: reflow into columns before stacking into
    // height.
    //
    // Background heuristic, stated plainly: the background colour is the most
    // common colour on the render's one-pixel edge ring. That is right for a
    // window with a flat surface behind its controls and wrong for one whose
    // edge is a gradient or an image - such a window will report every band as
    // full (harmless) or every band as sparse (obvious, and a sign to grade it
    // by eye instead). A pixel counts as content when any channel differs from
    // that background by more than 12.

    private static IEnumerable<string> RowOccupancy(Pixels pixels)
    {
        if (pixels.Width < 8 || pixels.Height < LayoutAuditRegistry.BandHeight)
            yield break;

        var background = pixels.EdgeMode();
        var middle = pixels.Width / 2;

        var bands = new List<(int Top, int Bottom, bool Left, bool Right,
                              double RightEmpty)>();

        for (var top = 0; top < pixels.Height;
             top += LayoutAuditRegistry.BandHeight)
        {
            var bottom = Math.Min(pixels.Height,
                                  top + LayoutAuditRegistry.BandHeight);

            var left = false;
            for (var x = 0; x < middle && !left; x++)
                left = pixels.ColumnHasContent(x, top, bottom, background);

            var emptyColumns = 0;
            var columns = pixels.Width - middle;
            for (var x = middle; x < pixels.Width; x++)
                if (!pixels.ColumnHasContent(x, top, bottom, background))
                    emptyColumns++;

            var emptyShare = columns > 0 ? (double)emptyColumns / columns : 1.0;
            bands.Add((top, bottom, left, emptyColumns < columns, emptyShare));
        }

        // Nothing painted at all: an empty window is another check's problem.
        if (!bands.Any(b => b.Left || b.Right)) yield break;

        // A band convicts only if content still stacks BELOW it - the last rows
        // of a page are allowed to end wherever they end.
        var sparse = new bool[bands.Count];
        for (var index = 0; index < bands.Count; index++)
        {
            var contentBelow = false;
            for (var below = index + 1; below < bands.Count; below++)
            {
                if (!bands[below].Left && !bands[below].Right) continue;
                contentBelow = true;
                break;
            }

            sparse[index] = bands[index].Left
                && bands[index].RightEmpty > LayoutAuditRegistry.SparseRightHalf
                && contentBelow;
        }

        // Report one message per RUN of consecutive sparse bands. The loop runs
        // one past the end so a run that reaches the last band still closes.
        var start = -1;
        for (var index = 0; index <= bands.Count; index++)
        {
            if (index < bands.Count && sparse[index])
            {
                if (start < 0) start = index;
                continue;
            }

            var length = index - start;
            if (start >= 0 && length >= LayoutAuditRegistry.SparseBandRun)
            {
                var share = bands.Skip(start).Take(length)
                                 .Average(b => b.RightEmpty);
                yield return "ALG-7 ROW OCCUPANCY (rules/GUI.md -> Zubi v2): "
                    + $"rows y={bands[start].Top}..{bands[index - 1].Bottom} "
                    + "keep their content in the left half while "
                    + $"{share * 100:0}% of the right half stands empty, and "
                    + "content still stacks BELOW them. Reflow those rows into "
                    + "columns before stacking into height - that empty right "
                    + "half is the space the rows below are starving for "
                    + $"(background taken as {Hex(background)}, the most common "
                    + "edge pixel)";
            }

            start = -1;
        }
    }

    // --- ALG-9 SECTION TAXONOMY ----------------------------------------------
    //
    // NOT wired into the visual-tree walk: a "section" is a human grouping, and
    // no walk can tell a heading from a label. A project calls this from its own
    // test with the map it already knows - keys are section titles in the order
    // they appear, values are the labels inside each:
    //
    //   [Fact]
    //   public void Settings_Taxonomy()
    //   {
    //       var sections = new Dictionary<string, IEnumerable<string>>
    //       {
    //           ["Size"]   = new[] { "Window width", "Window height" },
    //           ["Colors"] = new[] { "Accent color", "Background color" },
    //           ["Misc"]   = new[] { "Grid opacity" },   // ALG-9 fails this one
    //       };
    //       Assert.Empty(LayoutAuditTests.CheckSectionTaxonomy(sections));
    //   }
    //
    // A concept word (LayoutAuditRegistry.ConceptWords) that titles a section
    // owns it: the same word in a label anywhere else fails. Matching is by
    // word start, case-insensitive, so "Colors" owns "color" and "Sizes" owns
    // "size"; a single-token label like "FontSize" is NOT split and will be
    // missed. When two sections claim one concept the FIRST is treated as its
    // home and the second's labels fail - rename one of them.

    public static IReadOnlyList<string> CheckSectionTaxonomy(
        IDictionary<string, IEnumerable<string>> sections)
    {
        var problems = new List<string>();
        if (sections == null || sections.Count == 0) return problems;

        foreach (var concept in LayoutAuditRegistry.ConceptWords)
        {
            var home = sections.Keys
                .FirstOrDefault(title => MentionsConcept(title, concept));
            if (home == null) continue;

            foreach (var section in sections)
            {
                if (string.Equals(section.Key, home,
                                  StringComparison.OrdinalIgnoreCase))
                    continue;

                foreach (var label in section.Value ?? Enumerable.Empty<string>())
                {
                    if (!MentionsConcept(label, concept)) continue;

                    problems.Add("ALG-9 SECTION TAXONOMY (rules/GUI.md -> "
                        + $"Zubi v2): '{label}' sits in section "
                        + $"'{section.Key}' while '{home}' is the section named "
                        + $"for the concept '{concept}'. Move the control into "
                        + $"'{home}', or write the reason it must live where it "
                        + "is beside it - a user who found one Size setting "
                        + "expects the rest in the same place");
                }
            }
        }

        return problems;
    }

    private static readonly char[] WordSeparators =
        { ' ', '\t', '\n', '\r', '-', '_', '/', ':', '(', ')', ',', '.', '&',
          '+', '\'', '"' };

    private static bool MentionsConcept(string text, string concept)
    {
        if (string.IsNullOrEmpty(text)) return false;
        foreach (var token in text.Split(WordSeparators,
                                         StringSplitOptions.RemoveEmptyEntries))
            if (token.StartsWith(concept, StringComparison.OrdinalIgnoreCase))
                return true;
        return false;
    }

    // --- the offscreen render, as pixels ------------------------------------

    /// One RenderTargetBitmap copied out once and asked questions many times.
    /// Pbgra32 is PREMULTIPLIED alpha, so composing a pixel over the window's
    /// backdrop is simply source + backdrop * (1 - alpha) - no un-premultiply
    /// step, and no DPI arithmetic either: the bitmap is rendered at 96 DPI, so
    /// one pixel here is one logical pixel there.
    private sealed class Pixels
    {
        private readonly byte[] _bgra;
        private readonly Color _backdrop;

        public int Width { get; }
        public int Height { get; }

        public Pixels(RenderTargetBitmap bitmap, Color backdrop)
        {
            Width = bitmap.PixelWidth;
            Height = bitmap.PixelHeight;
            _backdrop = backdrop;
            _bgra = new byte[Width * Height * 4];
            bitmap.CopyPixels(new Int32Rect(0, 0, Width, Height), _bgra,
                              Width * 4, 0);
        }

        public Color At(int x, int y)
        {
            var index = (y * Width + x) * 4;
            var rest = 255 - _bgra[index + 3];
            return Color.FromRgb(
                (byte)Math.Min(255, _bgra[index + 2] + _backdrop.R * rest / 255),
                (byte)Math.Min(255, _bgra[index + 1] + _backdrop.G * rest / 255),
                (byte)Math.Min(255, _bgra[index] + _backdrop.B * rest / 255));
        }

        /// The most common colour inside a box - the background a text element
        /// actually sits on, since glyphs never own the majority of a box.
        public Color Mode(Rect area)
        {
            var x0 = Math.Max(0, (int)Math.Floor(area.X));
            var y0 = Math.Max(0, (int)Math.Floor(area.Y));
            var x1 = Math.Min(Width, (int)Math.Ceiling(area.Right));
            var y1 = Math.Min(Height, (int)Math.Ceiling(area.Bottom));
            if (x1 <= x0 || y1 <= y0) return _backdrop;

            var stepX = Math.Max(1, (x1 - x0) / 64);
            var stepY = Math.Max(1, (y1 - y0) / 64);

            var counts = new Dictionary<int, int>();
            for (var y = y0; y < y1; y += stepY)
                for (var x = x0; x < x1; x += stepX)
                    Count(counts, At(x, y));

            return Winner(counts, _backdrop);
        }

        /// True when the render produced nothing at all - every sampled pixel
        /// fully transparent. A window that was never shown can, in some
        /// templates, render blank; that is a finding to REPORT, never a set of
        /// pixels to judge.
        public bool IsBlank()
        {
            // Alpha lives at byte 3 of each pixel; the stride keeps that
            // alignment while sampling every seventh pixel.
            for (var index = 3; index < _bgra.Length; index += 4 * 7)
                if (_bgra[index] != 0) return false;
            return true;
        }

        /// The most common colour on the one-pixel edge ring: the window's own
        /// surface, as ALG-7 needs it.
        public Color EdgeMode()
        {
            if (Width < 1 || Height < 1) return _backdrop;

            var counts = new Dictionary<int, int>();
            for (var x = 0; x < Width; x++)
            {
                Count(counts, At(x, 0));
                Count(counts, At(x, Height - 1));
            }
            for (var y = 0; y < Height; y++)
            {
                Count(counts, At(0, y));
                Count(counts, At(Width - 1, y));
            }

            return Winner(counts, _backdrop);
        }

        public bool ColumnHasContent(int x, int top, int bottom, Color background)
        {
            for (var y = top; y < bottom; y++)
                if (Distance(At(x, y), background)
                    > LayoutAuditRegistry.BackgroundDelta)
                    return true;
            return false;
        }

        private static int Distance(Color one, Color two) =>
            Math.Max(Math.Abs(one.R - two.R),
                Math.Max(Math.Abs(one.G - two.G), Math.Abs(one.B - two.B)));

        private static void Count(Dictionary<int, int> counts, Color color)
        {
            var key = (color.R << 16) | (color.G << 8) | color.B;
            counts[key] = counts.TryGetValue(key, out var seen) ? seen + 1 : 1;
        }

        private static Color Winner(Dictionary<int, int> counts, Color fallback)
        {
            if (counts.Count == 0) return fallback;
            var best = counts.OrderByDescending(pair => pair.Value).First().Key;
            return Color.FromRgb((byte)(best >> 16), (byte)(best >> 8),
                                 (byte)best);
        }
    }

    // --- helpers -----------------------------------------------------------

    private static string TextOf(FrameworkElement element) => element switch
    {
        TextBlock t => t.Text,
        TextBox t => string.IsNullOrEmpty(t.Text) ? "" : t.Text,
        Label l => l.Content as string ?? "",
        ContentControl c => c.Content as string ?? "",
        _ => "",
    };

    private static double MeasureText(FrameworkElement element, string text)
    {
        var control = element as Control;
        var typeface = new Typeface(
            control?.FontFamily ?? SystemFonts.MessageFontFamily,
            control?.FontStyle ?? FontStyles.Normal,
            control?.FontWeight ?? FontWeights.Normal,
            FontStretches.Normal);
        var size = control?.FontSize ?? SystemFonts.MessageFontSize;
        var formatted = new FormattedText(
            text, CultureInfo.CurrentUICulture, FlowDirection.LeftToRight,
            typeface, size, Brushes.Black,
            VisualTreeHelper.GetDpi(element).PixelsPerDip);
        return formatted.WidthIncludingTrailingWhitespace;
    }

    private static IEnumerable<DependencyObject> Descendants(DependencyObject root)
    {
        var count = VisualTreeHelper.GetChildrenCount(root);
        for (var i = 0; i < count; i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);
            yield return child;
            foreach (var deeper in Descendants(child)) yield return deeper;
        }
    }

    private static string Truncate(string text) =>
        text.Length <= 40 ? text : text[..40];

    /// What to call an element in a failure message: its x:Name if it has one,
    /// otherwise the text it carries.
    private static string NameOrText(FrameworkElement element)
    {
        if (!string.IsNullOrEmpty(element.Name)) return element.Name;
        var text = TextOf(element);
        return string.IsNullOrEmpty(text) ? "-" : Truncate(text);
    }

    private static string Describe(FrameworkElement element) =>
        $"{element.GetType().Name} '{NameOrText(element)}'";

    /// The element's box in the window's own coordinates, or null when the two
    /// are not connected (a popup lives in its own visual tree).
    private static Rect? BoundsIn(Window window, FrameworkElement element)
    {
        try
        {
            return element.TransformToAncestor(window)
                          .TransformBounds(new Rect(element.RenderSize));
        }
        catch (InvalidOperationException)
        {
            return null;
        }
    }

    /// THE TRAP THAT MADE THIS HELPER: UIElement.IsVisible is FALSE for every
    /// element of a window that was never shown. It is computed from the parent
    /// chain up to a root connected to a PresentationSource, and an audit which
    /// never calls Show() (Silent Audits, rules/GUI.md) has no such source - so
    /// `Where(e => e.IsVisible)` silently filters away the ENTIRE window and
    /// every check passes on nothing. The Qt sibling does not have this problem
    /// because it calls show() on an offscreen platform.
    ///
    /// Visibility is what an offscreen tree can honestly answer: the element and
    /// every visual ancestor must be Visibility.Visible.
    private static bool IsRenderVisible(DependencyObject element)
    {
        DependencyObject? node = element;
        while (node != null)
        {
            if (node is UIElement { Visibility: not Visibility.Visible })
                return false;
            node = VisualTreeHelper.GetParent(node);
        }
        return true;
    }

    /// True when something between the element and the window clips it, so an
    /// element whose box reaches past the window does NOT actually paint there
    /// (the classic case: a long list inside a ScrollViewer).
    private static bool IsClippedByAncestor(DependencyObject element,
                                            DependencyObject window)
    {
        var node = VisualTreeHelper.GetParent(element);
        while (node != null && node != window)
        {
            if (node is ScrollViewer) return true;
            if (node is UIElement { ClipToBounds: true }) return true;
            node = VisualTreeHelper.GetParent(node);
        }
        return false;
    }

    /// The written exemption an element (or any ancestor up to the window)
    /// carries in its Tag, e.g. Tag="radius-ok:circle-content".
    private static bool HasExemption(DependencyObject element,
                                     DependencyObject window, string prefix)
    {
        DependencyObject? node = element;
        while (node != null)
        {
            if (node is FrameworkElement framework
                && framework.Tag is string tag
                && tag.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                return true;
            if (node == window) break;
            node = VisualTreeHelper.GetParent(node);
        }
        return false;
    }

    private static string ReadOnlyCopyOf(string source)
    {
        var copy = Path.Combine(Path.GetTempPath(),
            $"layout-audit-profile-{Guid.NewGuid():N}{Path.GetExtension(source)}");
        File.Copy(source, copy, overwrite: true);
        File.SetAttributes(copy, File.GetAttributes(copy) | FileAttributes.ReadOnly);
        return copy;
    }

    private static void TryDelete(string path)
    {
        try
        {
            if (!File.Exists(path)) return;
            File.SetAttributes(path, FileAttributes.Normal);
            File.Delete(path);
        }
        catch (IOException)
        {
            // A temp copy the OS still holds. Nothing is masked: the audit's
            // findings are already in the list, and the temp folder is swept
            // by Windows.
        }
        catch (UnauthorizedAccessException)
        {
            // Same.
        }
    }

    private static T RunSta<T>(Func<T> body)
    {
        T result = default!;
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try { result = body(); }
            catch (Exception exception) { failure = exception; }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure != null) throw failure;
        return result;
    }
}
