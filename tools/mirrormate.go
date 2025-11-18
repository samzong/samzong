package main

import (
    "bufio"
    "errors"
    "flag"
    "fmt"
    "io"
    "os"
    "path/filepath"
    "regexp"
    "strings"
    "syscall"
    "time"
    "os/signal"
)

// Prefix mappings
var mappings = [][2]string{
    {"docker.io", "m.daocloud.io/docker.io"},
    {"gcr.io", "m.daocloud.io/gcr.io"},
    {"ghcr.io", "m.daocloud.io/ghcr.io"},
    {"registry.k8s.io", "m.daocloud.io/registry.k8s.io"},
    {"nvcr.io", "m.daocloud.io/nvcr.io"},
    {"quay.io", "m.daocloud.io/quay.io"},
}

// Image regex: match either long form with path or short form with mandatory tag/digest
var imageRe = regexp.MustCompile(`([a-zA-Z0-9.-]+(:[0-9]+)?(/[a-zA-Z0-9._-]+)+(@sha256:[0-9a-fA-F]{64}|:[a-zA-Z0-9._-]+)?|[a-zA-Z0-9._-]+(@sha256:[0-9a-fA-F]{64}|:[a-zA-Z0-9._-]+))`)

var (
    autoApply   bool
    dryRun      bool
    quiet       bool
    showHelp    bool
    applyAll    bool
    currentTmp  string
    tipPrinted  bool
)

func usage() {
    fmt.Println("Usage: mirrormate [OPTIONS] [DIRECTORY]")
    fmt.Println()
    fmt.Println("Options:")
    fmt.Println("  -y, --yes       Auto-apply all changes")
    fmt.Println("  -n, --dry-run   Preview diff only; no write, no backup")
    fmt.Println("  -q, --quiet     Quiet mode; minimal output")
    fmt.Println("  -h, --help      Show help")
    fmt.Println()
    fmt.Println("Notes:")
    fmt.Println("  - Interactive by default: show diff per file, then ask to apply")
    fmt.Println("  - Backups in /tmp as mirrormate.<path with slashes -> underscores>.bak")
    fmt.Println("  - Directory defaults to current '.'")
    fmt.Println()
    fmt.Println("Image rewrites powered by: https://github.com/daocloud/public-image-mirror")
}

func main() {
    // Strict failure strategy
    // Note: Go returns errors; we exit non-zero on any fatal error.
    dir := "."

    // Support long flags manually alongside flag package
    // We parse os.Args to handle --yes/--dry-run/--quiet/--help
    fs := flag.NewFlagSet("mirrormate", flag.ContinueOnError)
    fs.BoolVar(&autoApply, "y", false, "auto apply")
    fs.BoolVar(&dryRun, "n", false, "dry run")
    fs.BoolVar(&quiet, "q", false, "quiet")
    fs.BoolVar(&showHelp, "h", false, "help")
    fs.Usage = usage

    // Translate long flags to short ones for the parser
    args := make([]string, 0, len(os.Args)-1)
    for _, a := range os.Args[1:] {
        switch a {
        case "--yes":
            args = append(args, "-y")
        case "--dry-run":
            args = append(args, "-n")
        case "--quiet":
            args = append(args, "-q")
        case "--help":
            args = append(args, "-h")
        default:
            args = append(args, a)
        }
    }
    if err := fs.Parse(args); err != nil {
        os.Exit(2)
    }
    rest := fs.Args()
    if len(rest) > 0 {
        dir = rest[0]
    }
    if showHelp {
        usage()
        return
    }
    if dryRun {
        autoApply = false // dry-run wins
    }

    // Cleanup trap
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    go func() {
        <-sigCh
        cleanup()
        os.Exit(1)
    }()
    defer cleanup()

    // Optional one-time tip (TTY only, non-quiet)
    if !quiet && isTTY() && !tipPrinted {
        fmt.Println("Tip: use -n to preview, -h for help; image rewrites use https://github.com/daocloud/public-image-mirror")
        tipPrinted = true
    }

    // Walk files
    var files []string
    err := filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
        if err != nil {
            return err
        }
        if d.IsDir() {
            return nil
        }
        lower := strings.ToLower(path)
        if strings.HasSuffix(lower, ".yaml") || strings.HasSuffix(lower, ".yml") {
            files = append(files, path)
        }
        return nil
    })
    if err != nil {
        fail(err)
    }

    for _, f := range files {
        if err := processFile(f); err != nil {
            fail(err)
        }
    }
}

func cleanup() {
    if currentTmp != "" {
        _ = os.Remove(currentTmp)
        currentTmp = ""
    }
}

func fail(err error) {
    fmt.Fprintln(os.Stderr, err.Error())
    os.Exit(1)
}

func processFile(path string) error {
    oldBytes, err := os.ReadFile(path)
    if err != nil {
        return err
    }
    oldText := string(oldBytes)
    eol, oldHasTrailingNewline := detectEOL(oldText)
    oldLines := splitLinesPreserve(oldText)

    // Rewrite
    newLines := make([]string, len(oldLines))
    for i, line := range oldLines {
        newLines[i] = rewriteLine(line)
    }

    // Detect changes
    changed := false
    if len(oldLines) != len(newLines) {
        changed = true
    } else {
        for i := range oldLines {
            if oldLines[i] != newLines[i] {
                changed = true
                break
            }
        }
    }
    if !changed {
        return nil
    }

    // Prepare tmp
    dir := filepath.Dir(path)
    base := filepath.Base(path)
    tmp, err := os.CreateTemp(dir, base+".tmp.")
    if err != nil {
        return err
    }
    currentTmp = tmp.Name()
    defer tmp.Close()

    // Write new content
    joined := strings.Join(newLines, eol)
    if oldHasTrailingNewline && !strings.HasSuffix(joined, eol) {
        joined += eol
    }
    if _, err := io.WriteString(tmp, joined); err != nil {
        return err
    }
    if err := tmp.Sync(); err != nil {
        return err
    }

    // Preview / apply
    if !quiet {
        fmt.Printf("==> File: %s\n", path)
        previewDiff(oldLines, newLines)
    }

    if dryRun {
        _ = os.Remove(tmp.Name())
        currentTmp = ""
        if !quiet {
            fmt.Println("Dry run: no changes applied")
        }
        return nil
    }

    if autoApply || applyAll {
        return apply(path, tmp.Name())
    }

    // Interactive prompt
    dec, err := promptApply(quiet)
    if err != nil {
        // treat as default N
        _ = os.Remove(tmp.Name())
        currentTmp = ""
        return nil
    }
    switch dec {
    case decisionYes:
        return apply(path, tmp.Name())
    case decisionAll:
        applyAll = true
        return apply(path, tmp.Name())
    default:
        _ = os.Remove(tmp.Name())
        currentTmp = ""
        if !quiet {
            fmt.Println("Skipped")
        }
        return nil
    }
}

func splitLinesPreserve(s string) []string {
    s = strings.ReplaceAll(s, "\r\n", "\n")
    s = strings.ReplaceAll(s, "\r", "\n")
    lines := strings.Split(s, "\n")
    // If trailing newline, last split is empty; preserve as empty line marker
    if len(lines) > 0 && lines[len(lines)-1] == "" {
        return lines[:len(lines)-1]
    }
    return lines
}

func detectEOL(s string) (string, bool) {
    if strings.Contains(s, "\r\n") {
        return "\r\n", strings.HasSuffix(s, "\r\n")
    }
    if strings.Contains(s, "\r") {
        return "\r", strings.HasSuffix(s, "\r")
    }
    return "\n", strings.HasSuffix(s, "\n")
}

func rewriteLine(line string) string {
    remaining := line
    rebuilt := strings.Builder{}
    for {
        loc := imageRe.FindStringIndex(remaining)
        if loc == nil {
            break
        }
        before := remaining[:loc[0]]
        match := remaining[loc[0]:loc[1]]
        rebuilt.WriteString(before)
        remaining = remaining[loc[1]:]
        // replacement
        replacement := match
        mapped := false
        for _, m := range mappings {
            oldp, newp := m[0], m[1]
            if strings.HasPrefix(match, oldp) {
                replacement = newp + match[len(oldp):]
                mapped = true
                break
            }
        }
        if !mapped {
            // treat as docker hub implicit registry
            repo, suffix := splitRepoSuffix(match)
            first := repo
            if idx := strings.Index(first, "/"); idx >= 0 {
                first = first[:idx]
            }
            isRegistry := strings.Contains(first, ".") || strings.Contains(first, ":") || first == "localhost"
            if !isRegistry {
                // no explicit registry -> docker.io
                if !strings.Contains(repo, "/") {
                    // short name -> library/<name>
                    replacement = "m.daocloud.io/docker.io/library/" + repo + suffix
                } else {
                    replacement = "m.daocloud.io/docker.io/" + repo + suffix
                }
            }
        }
        rebuilt.WriteString(replacement)
    }
    rebuilt.WriteString(remaining)
    return rebuilt.String()
}

func splitRepoSuffix(s string) (string, string) {
    // digest
    if i := strings.Index(s, "@sha256:"); i >= 0 {
        return s[:i], s[i:]
    }
    // tag: colon after last slash is tag separator; colon before last slash may be registry port
    lastSlash := strings.LastIndex(s, "/")
    lastColon := strings.LastIndex(s, ":")
    if lastColon > lastSlash && lastColon >= 0 {
        return s[:lastColon], s[lastColon:]
    }
    return s, ""
}

func isTTY() bool {
    fi, err := os.Stdout.Stat()
    if err != nil {
        return false
    }
    return (fi.Mode() & os.ModeCharDevice) != 0
}

func previewDiff(oldLines, newLines []string) {
    color := isTTY()
    red := "\x1b[31m"
    green := "\x1b[32m"
    reset := "\x1b[0m"
    max := len(oldLines)
    if len(newLines) > max {
        max = len(newLines)
    }
    for i := 0; i < max; i++ {
        var old, new string
        if i < len(oldLines) {
            old = oldLines[i]
        }
        if i < len(newLines) {
            new = newLines[i]
        }
        if old != new {
            if old != "" {
                if color {
                    fmt.Printf("%s-%s%s\n", red, old, reset)
                } else {
                    fmt.Printf("-%s\n", old)
                }
            }
            if new != "" {
                if color {
                    fmt.Printf("%s+%s%s\n", green, new, reset)
                } else {
                    fmt.Printf("+%s\n", new)
                }
            }
        }
    }
}

type decision int

const (
    decisionNo decision = iota
    decisionYes
    decisionAll
)

func promptApply(quiet bool) (decision, error) {
    fmt.Print("Apply changes? [y/N/all] ")
    // Read from /dev/tty to avoid stdin being used by pipelines
    tty, err := os.OpenFile("/dev/tty", os.O_RDWR, 0)
    if err != nil {
        return decisionNo, err
    }
    defer tty.Close()
    r := bufio.NewReader(tty)
    tty.SetReadDeadline(time.Now().Add(5 * time.Minute))
    s, err := r.ReadString('\n')
    if err != nil {
        return decisionNo, err
    }
    s = strings.TrimSpace(s)
    switch strings.ToLower(s) {
    case "y":
        return decisionYes, nil
    case "all":
        return decisionAll, nil
    case "", "n":
        return decisionNo, nil
    default:
        return decisionNo, nil
    }
}

func apply(path, tmp string) error {
    // Backup
    abs, err := filepath.Abs(path)
    if err != nil {
        return err
    }
    underscored := strings.ReplaceAll(abs, string(filepath.Separator), "_")
    backup := filepath.Join(os.TempDir(), "mirrormate."+underscored+".bak")
    if _, err := os.Stat(backup); err != nil {
        if !errors.Is(err, os.ErrNotExist) {
            return err
        }
        // create backup
        if err := copyFile(path, backup); err != nil {
            return err
        }
    }
    // Replace original
    if err := os.Rename(tmp, path); err != nil {
        return err
    }
    currentTmp = ""
    return nil
}

func copyFile(src, dst string) error {
    in, err := os.Open(src)
    if err != nil {
        return err
    }
    defer in.Close()
    out, err := os.Create(dst)
    if err != nil {
        return err
    }
    defer func() {
        _ = out.Close()
    }()
    if _, err := io.Copy(out, in); err != nil {
        return err
    }
    return out.Sync()
}