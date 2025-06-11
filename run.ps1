#!/bin/bash

PYTHON_SCRIPT_PATH="$(dirname "$0")/git_diff_script.py"

QUIET=false
OUTPUT_FILE_PATH=""
REPO_PATH=""
PYTHON_VERBOSE_FLAG=""
SHELL_VERBOSE=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --quiet)
            QUIET=true
            shift
            ;;
        -o|--output)
            if [ -z "$2" ]; then
                echo "Error: Option '$1' requires a filename argument." >&2
                exit 1
            fi
            OUTPUT_FILE_PATH="$2"
            shift 2
            ;;
        -v|--verbose)
            SHELL_VERBOSE=true
            PYTHON_VERBOSE_FLAG="--verbose"
            shift
            ;;
        *)
            if [ -z "$REPO_PATH" ]; then
                REPO_PATH="$1"
            else
                if [ "$SHELL_VERBOSE" = true ]; then
                    echo "Warning: Ignoring extra argument '$1'. Only one repository path is supported." >&2
                fi
            fi
            shift
            ;;
    esac
done

if [ -z "$REPO_PATH" ]; then
  echo "Usage: $0 <path_to_git_repository> [-o <filename>] [--quiet] [-v]"
  echo "  <path_to_git_repository> : Path to your Git repository."
  echo "  -o, --output <filename>  : Save output to the specified file."
  echo "  --quiet                  : Suppress all console output."
  echo "  -v, --verbose            : Enable verbose output."
  exit 1
fi

SHOULD_SAVE_TO_FILE=false
if [ -n "$OUTPUT_FILE_PATH" ]; then
  SHOULD_SAVE_TO_FILE=true
fi

if [ "$SHELL_VERBOSE" = true ]; then
  echo "Generating Git diff report for: ${REPO_PATH}"
  if [ "$SHOULD_SAVE_TO_FILE" = true ]; then
    echo "Saving output to: ${OUTPUT_FILE_PATH}"
  fi
  echo "----------------------------------------------------"
fi

if [ "$SHOULD_SAVE_TO_FILE" = true ]; then
  OUTPUT_DIR=$(dirname "${OUTPUT_FILE_PATH}")
  if [ -n "$OUTPUT_DIR" ] && [ "$OUTPUT_DIR" != "." ]; then
    mkdir -p "${OUTPUT_DIR}"
  fi
fi

if [ "$SHOULD_SAVE_TO_FILE" = true ]; then
  if [ "$QUIET" = true ]; then
    python3 "${PYTHON_SCRIPT_PATH}" "${REPO_PATH}" ${PYTHON_VERBOSE_FLAG} > "${OUTPUT_FILE_PATH}" 2>&1
  else
    python3 "${PYTHON_SCRIPT_PATH}" "${REPO_PATH}" ${PYTHON_VERBOSE_FLAG} 2>&1 | tee "${OUTPUT_FILE_PATH}"
  fi
else
  if [ "$QUIET" = true ]; then
    python3 "${PYTHON_SCRIPT_PATH}" "${REPO_PATH}" ${PYTHON_VERBOSE_FLAG} > /dev/null 2>&1
  else
    python3 "${PYTHON_SCRIPT_PATH}" "${REPO_PATH}" ${PYTHON_VERBOSE_FLAG}
  fi
fi

LAST_COMMAND_EXIT_CODE=$?

if [ "$LAST_COMMAND_EXIT_CODE" -eq 0 ]; then
  if [ "$SHELL_VERBOSE" = true ]; then
    if [ "$SHOULD_SAVE_TO_FILE" = true ]; then
      echo "----------------------------------------------------"
      echo "Report successfully saved to ${OUTPUT_FILE_PATH}"
    else
      echo "----------------------------------------------------"
      echo "Report completed."
    fi
  elif [ "$SHOULD_SAVE_TO_FILE" = true ]; then
    echo "----------------------------------------------------"
    echo "Report successfully saved to ${OUTPUT_FILE_PATH}"
  fi
else
  if [ "$QUIET" = false ] || [ "$SHOULD_SAVE_TO_FILE" = true ]; then
    echo "----------------------------------------------------" >&2
    echo "An error occurred (Exit Code: $LAST_COMMAND_EXIT_CODE)." >&2
    if [ "$SHOULD_SAVE_TO_FILE" = true ]; then
      echo "Check ${OUTPUT_FILE_PATH} for details." >&2
    else
      echo "Output was displayed to console above." >&2
    fi
  fi
fi