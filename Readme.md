### **Git Diff Tool Instructions**

**Purpose:** 
A Python-based utility to display unified diffs of modified, staged, unstaged, untracked, renamed, and copied files in a Git repository. 
It supports filtering by file extensions (case-insensitive) and excludes binary files for cleaner output.

---

#### **Key Features:**
- Unified diff view grouped alphabetically.
- Filter outputs using `--extensions` or `-e`.
- Omit non-text diffs with `-b`/`--ignore-binary`.
- Verbose logging (`-v`/`--verbose`) for debugging Git commands.

---

#### **Usage Instructions**

**1. Prerequisites:**  
Ensure you have Python 3.x installed and the script is executable (e.g., run `chmod +x git_diff_tool.py`).  

**2. Basic Usage:**  
Display all diffs in your repository:  
```mbash
python git_diff_tool.py /path/to/your/repo
```

---

#### **Command-Line Options**

- `-v` or `--verbose`:  
  Enable detailed logging of Git commands and internal tool processes.

- `-e <EXTENSIONS>` or `--extensions <EXTENSIONS>` (multiple allowed):  
  Filter results to include only files with specified extensions. Extensions should be provided in lowercase, but the tool handles case insensitivity automatically. For example:  
  - Include `.py` and `.md`: `-e py md`  
  - Include files ending with `.txt` or `.js`: `-e txt js`

- `-b` or `--ignore-binary`:  
  Exclude binary files (images, executables) from the output.

**Note:** Use **one flag at a time** to avoid conflicts. For example:  
```mbash
# Correct usage with combined options:
python git_diff_tool.py /path/to/repo -v -b -e py css

# Incorrect (ambiguous): Conflicts between `-v` and `-b`
```

---

#### **Examples**

1. Show diffs for Python and Markdown files:  
```mbash
python git_diff_tool.py /your/repo -e .py .md
```

2. Display only text-based files (`.txt`, `.js`) in verbose mode, ignoring binaries:  
```mbash
python git_diff_tool.py /your/repo -v -b -e txt js
```

3. Omit binary files and display all diffs (use sparingly on large repos):  
```mbash
python git_diff_tool.py -b /path/to/your/repo
```

---

#### **Combined Options Example**  
```mbash
# Show verbose output, exclude binaries, filter to JavaScript and CSS:
python git_diff_tool.py /path/to/repo -v -b -e js css
```

---

### **Troubleshooting**
- **Conflicting Flags:** Avoid using both `-v` (verbose) and `-b` (`--ignore-binary`) together.
- **Binary Files:** If you see unclear "Binary files differ" messages, use the `-b` flag to clean up output.

---