import subprocess
import os
import sys
import argparse
import re
import json # Import the json module

# Declare global variables at the top of the module scope.
# This ensures that any assignment to these variables throughout the script
# (including the initial False values and later from argparse)
# correctly modifies the global variable.
global _verbose, _ignore_binaries, _output_json

_verbose = False
_ignore_binaries = False
_output_json = False # New global flag for JSON output

def _log_message(message, level='normal'):
    """
    Internal logging function for the script.
    Only prints messages if verbose is enabled or if it's an error/warning.
    When JSON output is enabled, regular and debug messages are suppressed
    to keep stdout clean for JSON, but errors/warnings still go to stderr.
    """
    if level == 'error':
        sys.stderr.write(f"Error: {message}\n")
    elif level == 'warning':
        sys.stderr.write(f"Warning: {message}\n")
    elif _verbose and not _output_json: # Only print verbose messages if not outputting JSON
        sys.stdout.write(f"{message}\n")
    elif not _output_json and level == 'info': # Info messages only if not outputting JSON
        sys.stdout.write(f"{message}\n")


def _execute_git_command(command_parts, cwd):
    """
    Executes a Git command and returns its stdout and a success boolean.
    Special handling for 'git diff' where exit code 1 means differences found (not an error).
    """
    cmd_str = "git " + " ".join(command_parts)
    _log_message(f"Executing Git command: '{cmd_str}' in '{cwd}'", level='debug')

    is_diff_command = command_parts[0] == 'diff'

    try:
        result = subprocess.run(
            ['git'] + command_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout and _verbose and not _output_json: # Only log stdout if verbose and not JSON
            _log_message(f"  Git STDOUT: {result.stdout.strip()}", level='debug')
        if result.stderr:
            _log_message(f"  Git STDERR: {result.stderr.strip()}", level='debug')

        if is_diff_command and result.returncode == 1:
            _log_message(f"Git diff finished with exit code 1 (differences found).", level='debug')
            return result.stdout.strip(), True
        
        if result.returncode != 0:
            _log_message(f"Git command '{cmd_str}' failed with exit code {result.returncode}", level='error')
            return result.stdout.strip(), False
        
        return result.stdout.strip(), True

    except FileNotFoundError:
        _log_message("Git command not found. Ensure Git is installed and in your system's PATH.", level='error')
        return "", False
    except Exception as e:
        _log_message(f"An unexpected error occurred while running Git command '{cmd_str}': {e}", level='error')
        return "", False

def _is_binary_file(file_path, repo_path):
    """
    Checks if a file is considered binary by Git.
    Returns True if binary, False otherwise.
    """
    _log_message(f"Checking if '{file_path}' is binary...", level='debug')
    
    temp_diff_output, success = _execute_git_command(['diff', 'HEAD', '--', file_path], cwd=repo_path)
    if not success and 'unknown revision or path not in the working tree' in temp_diff_output:
        # If it's not a tracked file (e.g., untracked), try --no-index
        temp_diff_output, success = _execute_git_command(['diff', '--no-index', '/dev/null', file_path], cwd=repo_path)
    
    if success and "Binary files " in temp_diff_output and " differ" in temp_diff_output:
        _log_message(f"'{file_path}' identified as binary.", level='debug')
        return True
    
    _log_message(f"'{file_path}' not identified as binary.", level='debug')
    return False

def _split_diff_into_hunks(diff_content):
    """
    Splits a full Git diff string into an array of blocks,
    where each block is either the initial header or a diff hunk.
    """
    if not diff_content:
        return []

    lines = diff_content.splitlines()
    hunk_blocks = []
    current_block_lines = []
    
    # Flag to detect if we've passed the initial header (diff --git, index, ---, +++)
    # and are now looking for hunk headers (@@)
    in_hunk_section = False 

    for line in lines:
        # Check for start of a new file diff or a new hunk
        if line.startswith('diff --git '):
            # If we've accumulated lines for a previous block, add it
            if current_block_lines:
                hunk_blocks.append('\n'.join(current_block_lines))
            current_block_lines = [line]
            in_hunk_section = False # Reset for new file header
        elif line.startswith('@@ '):
            # If we've accumulated lines for a previous block (header or hunk), add it
            if current_block_lines:
                hunk_blocks.append('\n'.join(current_block_lines))
            current_block_lines = [line]
            in_hunk_section = True
        else:
            current_block_lines.append(line)
    
    # Add the last accumulated block if any
    if current_block_lines:
        hunk_blocks.append('\n'.join(current_block_lines))

    return hunk_blocks


def run_diff_logic(repo_path, file_extensions=None):
    """
    Displays the differences for all changed files (staged, unstaged, and untracked)
    in the specified Git repository, optionally filtered by file extensions,
    and organized by file. Can also ignore binary files.
    
    If _output_json is True, prints a JSON object; otherwise, prints human-readable diffs.
    
    Args:
        repo_path (str): The path to the Git repository.
        file_extensions (list, optional): A list of file extensions (e.g., ['.py', '.js'])
                                          to filter the diff output. If None, no filtering.
    """
    _log_message(f"--- Analyzing differences in repository: {repo_path} ---", level='info')

    if not os.path.exists(repo_path):
        _log_message(f"Repository path '{repo_path}' not found.", level='error')
        return 1

    if not os.path.isdir(os.path.join(repo_path, '.git')):
        _log_message(f"'{repo_path}' is not a Git repository (missing .git directory).", level='error')
        return 1

    stdout_status, success_status = _execute_git_command(['status', '--porcelain'], cwd=repo_path)
    if not success_status:
        _log_message("Failed to get Git status. Exiting.", level='error')
        return 1

    changed_files_info = []
    for line in stdout_status.strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) < 2:
            _log_message(f"Skipping malformed status line: '{line}'", level='debug')
            continue

        status_code = parts[0]
        file_path_raw = parts[1]

        if ' -> ' in file_path_raw and (status_code.startswith('R') or status_code.startswith('C')):
            file_path = file_path_raw.split(' -> ')[1].strip()
        else:
            file_path = file_path_raw.strip()
        
        changed_files_info.append({'status': status_code, 'path': file_path})

    if not changed_files_info:
        if not _output_json:
            print("No changes detected.")
        else:
            print(json.dumps([])) # Print empty JSON array if no changes
        return 0

    all_file_diffs = {} # Dictionary to store diffs for JSON output

    for file_info in changed_files_info:
        fpath = file_info['path']
        status = file_info['status']

        if file_extensions:
            _, ext = os.path.splitext(fpath)
            if ext.lower() not in file_extensions:
                _log_message(f"Skipping '{fpath}' due to extension filter.", level='debug')
                continue
        
        # New check for binary files
        if _ignore_binaries and _is_binary_file(fpath, repo_path):
            _log_message(f"Ignoring binary file: '{fpath}'", level='info')
            continue # Skip this file

        stdout_diff = ""
        success_diff = False

        if status == '??':
            full_path = os.path.join(repo_path, fpath)
            if os.path.isdir(full_path):
                _log_message(f"\n--- Untracked Directory: {fpath} ---", level='info')
                dir_had_content_diff = False
                for root, _, files in os.walk(full_path):
                    for file in files:
                        sub_file_path_relative = os.path.relpath(os.path.join(root, file), repo_path)
                        
                        if file_extensions:
                            _, sub_ext = os.path.splitext(sub_file_path_relative)
                            if sub_ext.lower() not in file_extensions:
                                _log_message(f"Skipping untracked sub-file '{sub_file_path_relative}' due to extension filter.", level='debug')
                                continue
                        
                        # Apply binary ignore for sub-files too
                        if _ignore_binaries and _is_binary_file(sub_file_path_relative, repo_path):
                            _log_message(f"Ignoring binary file: '{sub_file_path_relative}'", level='info')
                            continue

                        stdout_diff_sub, success_diff_sub = _execute_git_command(['diff', '--no-index', '/dev/null', sub_file_path_relative], cwd=repo_path)
                        if success_diff_sub and stdout_diff_sub.strip():
                            all_file_diffs[sub_file_path_relative] = {
                                'status': 'Untracked',
                                'diff': stdout_diff_sub.strip()
                            }
                            dir_had_content_diff = True
                        elif not success_diff_sub:
                            _log_message(f"Could not get diff for untracked file {sub_file_path_relative}. Skipping.", level='warning')
                if not dir_had_content_diff and _verbose and not _output_json:
                     _log_message(f"(No untracked files with content found in {fpath})", level='info')
                _log_message(f"----- End Untracked Directory: {fpath} -----", level='info')
            else:
                stdout_diff, success_diff = _execute_git_command(['diff', '--no-index', '/dev/null', fpath], cwd=repo_path)
                if success_diff and stdout_diff.strip():
                    all_file_diffs[fpath] = {
                        'status': 'Untracked',
                        'diff': stdout_diff.strip()
                    }
                elif not success_diff:
                    _log_message(f"Could not get diff for untracked file {fpath}. Skipping.", level='warning')
        else:
            stdout_diff, success_diff = _execute_git_command(['diff', 'HEAD', '--', fpath], cwd=repo_path)
            
            if success_diff and stdout_diff.strip():
                all_file_diffs[fpath] = {
                    'status': status,
                    'diff': stdout_diff.strip()
                }
            elif not success_diff:
                _log_message(f"Could not get diff for {fpath}. Skipping.", level='warning')

    if not all_file_diffs:
        if not _output_json:
            if file_extensions:
                print(f"No changes detected or all changed files were filtered by extensions: {', '.join(file_extensions)}")
            elif _ignore_binaries:
                print("No changes detected or all changed files were binary and ignored.")
            else:
                print("No changes detected.")
        else:
            print(json.dumps([])) # Print empty JSON array
    else:
        if _output_json:
            # Prepare the list of dictionaries for JSON output
            json_output_data = []
            for fpath in sorted(all_file_diffs.keys()): # Sort for consistent output
                diff_info = all_file_diffs[fpath]
                filename_base, ext = os.path.splitext(fpath) # Get filename base and extension
                
                # Get the full raw diff text
                full_raw_diff_text = diff_info['diff']
                
                # Split the full diff into an array of hunk blocks
                diff_hunk_blocks = _split_diff_into_hunks(full_raw_diff_text)

                json_output_data.append({
                    "filename": fpath, # Use full path as filename
                    "ext": ext,
                    "all_diffs_as_text": full_raw_diff_text, # Full diff as single string
                    "diff_blocks": diff_hunk_blocks # Diff split into an array of hunk strings
                })
            
            # Print the JSON array to stdout
            print(json.dumps(json_output_data, indent=2))
        else:
            # Existing human-readable output
            sorted_files = sorted(all_file_diffs.keys())

            for fpath in sorted_files:
                diff_info = all_file_diffs[fpath]
                status_display = diff_info['status']
                diff_content = diff_info['diff']
                
                print(f"\n--- {fpath} ({status_display}) ---")
                print(diff_content)
                print("-----")

        _log_message(f"--- Diff analysis completed for {repo_path} ---", level='info')

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Displays all changed files (staged, unstaged, and untracked) in a Git repository."
    )
    parser.add_argument(
        "repo_path",
        help="The path to the Git repository."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output for detailed logging."
    )
    parser.add_argument(
        "-e", "--extensions",
        nargs='+',
        help="Filter diffs by file extension (e.g., .py .js .txt). Include the leading dot."
    )
    parser.add_argument(
        "-b", "--ignore-binaries",
        action="store_true",
        help="Do not display diffs for binary files."
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output the diffs in JSON format."
    )

    args = parser.parse_args()

    # The 'global' keyword must be used within a function to indicate that
    # assignments to variables should modify the global variable rather than
    # creating a new local one. When used at the module level (like here),
    # variables are already global by default, so 'global' is not strictly
    # necessary *for declaration*, but it doesn't hurt.
    # The crucial part for your error was that any assignment *before*
    # `global` in a function (or the __main__ block acting like one)
    # would make it local. By putting it at the very top, all subsequent
    # uses and assignments refer to the intended global variables.
    
    _verbose = args.verbose
    _ignore_binaries = args.ignore_binaries
    _output_json = args.json # Set the new global flag

    normalized_extensions = None
    if args.extensions:
        normalized_extensions = []
        for ext in args.extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_extensions.append(ext.lower())

    exit_code = run_diff_logic(args.repo_path, normalized_extensions)
    sys.exit(exit_code)
