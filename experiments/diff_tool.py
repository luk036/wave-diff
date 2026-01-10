import difflib
import sys
import argparse


def simple_diff(file1_content, file2_content, file1_name="file1", file2_name="file2"):
    """Simple character-by-character diff showing differences with markers"""
    lines1 = file1_content.splitlines(keepends=True)
    lines2 = file2_content.splitlines(keepends=True)

    result = []
    i, j = 0, 0

    while i < len(lines1) or j < len(lines2):
        if i < len(lines1) and j < len(lines2):
            if lines1[i] == lines2[j]:
                result.append(f"  {lines1[i].rstrip()}")
                i += 1
                j += 1
            else:
                result.append(f"- {lines1[i].rstrip()}")
                result.append(f"+ {lines2[j].rstrip()}")
                i += 1
                j += 1
        elif i < len(lines1):
            result.append(f"- {lines1[i].rstrip()}")
            i += 1
        else:
            result.append(f"+ {lines2[j].rstrip()}")
            j += 1

    return "\n".join(result)


def unified_diff(
    file1_content, file2_content, file1_name="file1", file2_name="file2", n=3
):
    """Unified diff format (similar to git diff)"""
    lines1 = file1_content.splitlines(keepends=True)
    lines2 = file2_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        lines1, lines2, fromfile=file1_name, tofile=file2_name, n=n, lineterm=""
    )

    return "\n".join(diff)


def context_diff(file1_content, file2_content, file1_name="file1", file2_name="file2"):
    """Context diff format"""
    lines1 = file1_content.splitlines(keepends=True)
    lines2 = file2_content.splitlines(keepends=True)

    diff = difflib.context_diff(
        lines1, lines2, fromfile=file1_name, tofile=file2_name, lineterm=""
    )

    return "\n".join(diff)


def html_diff(file1_content, file2_content, file1_name="file1", file2_name="file2"):
    """HTML formatted diff with color coding"""
    diff = difflib.HtmlDiff(wrapcolumn=80)

    lines1 = file1_content.splitlines()
    lines2 = file2_content.splitlines()

    html_result = diff.make_file(
        lines1, lines2, file1_name, file2_name, context=True, numlines=3
    )

    return html_result


def main():
    parser = argparse.ArgumentParser(
        description="Compare two text files and show differences"
    )
    parser.add_argument("file1", help="First file to compare")
    parser.add_argument("file2", help="Second file to compare")
    parser.add_argument(
        "-f",
        "--format",
        choices=["simple", "unified", "context", "html"],
        default="unified",
        help="Diff format (default: unified)",
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "-n",
        "--context-lines",
        type=int,
        default=3,
        help="Number of context lines for unified diff (default: 3)",
    )

    args = parser.parse_args()

    try:
        # Read file contents
        with open(args.file1, "r", encoding="utf-8") as f1:
            content1 = f1.read()

        with open(args.file2, "r", encoding="utf-8") as f2:
            content2 = f2.read()

        # Generate diff based on format
        if args.format == "simple":
            diff_output = simple_diff(content1, content2, args.file1, args.file2)
        elif args.format == "unified":
            diff_output = unified_diff(
                content1, content2, args.file1, args.file2, args.context_lines
            )
        elif args.format == "context":
            diff_output = context_diff(content1, content2, args.file1, args.file2)
        elif args.format == "html":
            diff_output = html_diff(content1, content2, args.file1, args.file2)
            # For HTML output, default to file output
            if not args.output:
                args.output = "diff_output.html"

        # Output the result
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_file:
                out_file.write(diff_output)
            print(f"Diff saved to {args.output}")
        else:
            print(diff_output)

        # Show summary
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        print(
            f"\nSummary: {args.file1}: {len(lines1)} lines, {args.file2}: {len(lines2)} lines"
        )

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
