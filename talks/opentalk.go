package main

import (
    "errors"
    "flag"
    "fmt"
    "os"
    "path/filepath"
    "regexp"
    "time"
)

var rx = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-(en|zh)-(online|offline)$`)

func main() {
    if len(os.Args) < 2 {
        fmt.Println("usage: opentalk <init|check> [options]")
        os.Exit(1)
    }
    switch os.Args[1] {
    case "init":
        runInit()
    case "check":
        runCheck()
    default:
        fmt.Println("usage: opentalk <init|check> [options]")
        os.Exit(1)
    }
}

func runInit() {
    fsInit := flag.NewFlagSet("init", flag.ExitOnError)
    date := fsInit.String("date", "", "YYYY-MM-DD")
    title := fsInit.String("title", "", "slug")
    lang := fsInit.String("lang", "", "en|zh")
    venue := fsInit.String("venue", "", "online|offline")
    root := fsInit.String("root", "talks", "root directory")
    fsInit.Parse(os.Args[2:])

    if err := validateInitInputs(*date, *title, *lang, *venue); err != nil {
        fmt.Println(err.Error())
        os.Exit(1)
    }

    name := generateName(*date, *title, *lang, *venue)
    if err := validateName(name); err != nil {
        fmt.Println(err.Error())
        os.Exit(1)
    }

    target := filepath.Join(*root, name)
    if err := initSkeleton(target); err != nil {
        fmt.Println(err.Error())
        os.Exit(1)
    }
    fmt.Println(target)
}

func runCheck() {
    fsCheck := flag.NewFlagSet("check", flag.ExitOnError)
    root := fsCheck.String("root", "talks", "root directory")
    fsCheck.Parse(os.Args[2:])

    dirs, err := listEventDirs(*root)
    if err != nil {
        fmt.Println(err.Error())
        os.Exit(1)
    }
    hasError := false
    for _, d := range dirs {
        base := filepath.Base(d)
        if err := validateName(base); err != nil {
            fmt.Printf("ERROR %s: %s\n", base, err.Error())
            hasError = true
            continue
        }
        outline := filepath.Join(d, "outline.md")
        if ok, _ := exists(outline); !ok {
            fmt.Printf("ERROR %s: missing outline.md\n", base)
            hasError = true
            continue
        }
        fmt.Printf("OK %s\n", base)
    }
    if hasError {
        os.Exit(1)
    }
}

func validateInitInputs(date, title, lang, venue string) error {
    if date == "" || title == "" || lang == "" || venue == "" {
        return errors.New("missing required flags: --date --title --lang --venue")
    }
    if _, err := time.Parse("2006-01-02", date); err != nil {
        return errors.New("invalid date: expected YYYY-MM-DD")
    }
    r := regexp.MustCompile(`^[a-z0-9]+(?:-[a-z0-9]+)*$`)
    if !r.MatchString(title) {
        return errors.New("invalid title: ascii lowercase kebab-case required")
    }
    if lang != "en" && lang != "zh" {
        return errors.New("invalid lang: en or zh")
    }
    if venue != "online" && venue != "offline" {
        return errors.New("invalid venue: online or offline")
    }
    return nil
}

func generateName(date, title, lang, venue string) string {
    return fmt.Sprintf("%s-%s-%s-%s", date, title, lang, venue)
}

func validateName(name string) error {
    if !rx.MatchString(name) {
        return errors.New("invalid directory name")
    }
    return nil
}

func ensureDir(path string) error {
    return os.MkdirAll(path, 0o755)
}

func createFile(path string) error {
    if ok, _ := exists(path); ok {
        return nil
    }
    f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0o644)
    if err != nil {
        return err
    }
    return f.Close()
}

func exists(path string) (bool, error) {
    _, err := os.Stat(path)
    if err == nil {
        return true, nil
    }
    if os.IsNotExist(err) {
        return false, nil
    }
    return false, err
}

func listEventDirs(root string) ([]string, error) {
    ents, err := os.ReadDir(root)
    if err != nil {
        if os.IsNotExist(err) {
            return []string{}, nil
        }
        return nil, err
    }
    res := []string{}
    for _, e := range ents {
        if e.IsDir() {
            res = append(res, filepath.Join(root, e.Name()))
        }
    }
    return res, nil
}

func initSkeleton(target string) error {
    if err := ensureDir(target); err != nil {
        return err
    }
    if err := createFile(filepath.Join(target, "outline.md")); err != nil {
        return err
    }
    sub := []string{"slides", "assets", "demo", "scripts", "notes"}
    for _, s := range sub {
        if err := ensureDir(filepath.Join(target, s)); err != nil {
            return err
        }
    }
    return nil
}