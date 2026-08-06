// Guard test - THE SPACE & LEGIBILITY LAW, runtime half, WPF (rules/GUI.md).
//
// TEMPLATE for C# + WPF projects (the default front stack - rules/START.md).
// Copy into the project's test assembly and fill in the Windows registry;
// nothing else should need editing.
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
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Xunit;

namespace Project.Tests.Layout;

public static class LayoutAuditRegistry
{
    // Every top-level window and dialog, built in its FULLEST realistic state
    // (longest real strings, most rows) - an empty window proves nothing.
    // A window missing here is a hole in the guard; keep it complete.
    public static readonly (string Name, Func<Window> Factory)[] Windows =
    {
        // ("SetsDialog", () => new SetsDialog(DemoConfig.Full())),
    };

    public const double SlackTolerance = 24;   // px before free space counts
    public const double TextPadding = 8;       // px assumed frame-to-text

    // The screen every window must survive. A declared minimum bigger than
    // this is the absurd-minimum bug (a two-item menu demanding 6000px):
    // REFLOW, never widen. Raising it needs .claude/layout-frame.json with a
    // stated reason.
    public const double FloorWidth = 1280;
    public const double FloorHeight = 720;

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

    [Theory]
    [MemberData(nameof(AllWindows))]
    public void Layout_Audit(string name)
    {
        var problems = RunSta(() => Audit(name));
        Assert.True(problems.Count == 0,
            "THE SPACE & LEGIBILITY LAW (rules/GUI.md) - runtime audit failed:\n  "
            + string.Join("\n  ", problems)
            + "\nLadder: (1) the starving element takes the free space, "
            + "(2) reflow into more rows, (3) raise the window minimum, "
            + "(4) scroll only when the window is genuinely full.");
    }

    private static List<string> Audit(string name)
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
            window.Width = width;
            window.Height = height;
            window.Measure(new Size(width, height));
            window.Arrange(new Rect(0, 0, width, height));
            window.UpdateLayout();

            var tag = $"[{name} @ {label} {width:0}x{height:0}]";
            problems.AddRange(Clipped(window).Select(p => $"{tag} {p}"));
            problems.AddRange(Elided(window).Select(p => $"{tag} {p}"));
            problems.AddRange(ScrollWithSlack(window, width, height)
                .Select(p => $"{tag} {p}"));

            if (label == "minimum")
            {
                var shot = Capture(window, name, width, height);
                Console.WriteLine($"SHOT {shot} - MIN {width:0}x{height:0} - "
                    + "now OPEN it and GRADE it (>= 8/10) in "
                    + ".claude/layout-proof.md");
            }
        }

        return problems;
    }

    /// The screenshot the agent must OPEN and grade. A GUI nobody looked at is
    /// a GUI nobody checked.
    private static string Capture(Window window, string name,
                                  double width, double height)
    {
        Directory.CreateDirectory(LayoutAuditRegistry.ShotDir);
        var path = Path.GetFullPath(
            Path.Combine(LayoutAuditRegistry.ShotDir, $"{name}.png"));
        var bitmap = new RenderTargetBitmap(
            (int)width, (int)height, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(window);
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = File.Create(path);
        encoder.Save(stream);
        return path;
    }

    // --- the three checks --------------------------------------------------

    private static IEnumerable<string> Clipped(DependencyObject root) =>
        Descendants(root).OfType<FrameworkElement>()
            .Where(e => e.IsVisible)
            .Where(e => e.DesiredSize.Width > e.ActualWidth + 0.5
                     || e.DesiredSize.Height > e.ActualHeight + 0.5)
            .Select(e => $"CLIPPED {e.GetType().Name} '{e.Name}': has "
                + $"{e.ActualWidth:0}x{e.ActualHeight:0}, wants "
                + $"{e.DesiredSize.Width:0}x{e.DesiredSize.Height:0}");

    private static IEnumerable<string> Elided(DependencyObject root)
    {
        foreach (var element in Descendants(root).OfType<FrameworkElement>()
                     .Where(e => e.IsVisible))
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
                     .Where(v => v.IsVisible))
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
