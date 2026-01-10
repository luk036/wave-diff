import sys
import argparse
from enum import Enum


class EditOperation(Enum):
    """Enum for edit operations in Levenshtein distance"""

    MATCH = 0
    INSERT = 1
    DELETE = 2
    REPLACE = 3


def levenshtein_distance(str1, str2):
    """
    Calculate Levenshtein distance between two strings.
    Returns the distance and the edit operations matrix.
    """
    m, n = len(str1), len(str2)

    # Create distance matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # deletion
                    dp[i][j - 1] + 1,  # insertion
                    dp[i - 1][j - 1] + 1,  # substitution
                )

    return dp[m][n], dp


def levenshtein_distance_with_path(str1, str2):
    """
    Calculate Levenshtein distance and return the edit path.
    """
    m, n = len(str1), len(str2)

    # Create distance matrix and operation matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    ops = [[EditOperation.MATCH] * (n + 1) for _ in range(m + 1)]

    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = i
        ops[i][0] = EditOperation.DELETE
    for j in range(n + 1):
        dp[0][j] = j
        ops[0][j] = EditOperation.INSERT

    ops[0][0] = EditOperation.MATCH

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                ops[i][j] = EditOperation.MATCH
            else:
                # Check all possible operations
                delete_cost = dp[i - 1][j] + 1
                insert_cost = dp[i][j - 1] + 1
                replace_cost = dp[i - 1][j - 1] + 1

                min_cost = min(delete_cost, insert_cost, replace_cost)
                dp[i][j] = min_cost

                if min_cost == delete_cost:
                    ops[i][j] = EditOperation.DELETE
                elif min_cost == insert_cost:
                    ops[i][j] = EditOperation.INSERT
                else:
                    ops[i][j] = EditOperation.REPLACE

    # Backtrack to get edit path
    i, j = m, n
    path = []

    while i > 0 or j > 0:
        operation = ops[i][j]
        path.append((operation, i, j))

        if operation == EditOperation.MATCH or operation == EditOperation.REPLACE:
            i -= 1
            j -= 1
        elif operation == EditOperation.INSERT:
            j -= 1
        elif operation == EditOperation.DELETE:
            i -= 1

    path.reverse()
    return dp[m][n], dp, ops, path


def diff_lines(lines1, lines2):
    """
    Perform diff between two lists of lines.
    Returns edit distance and diff output.
    """
    m, n = len(lines1), len(lines2)

    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if lines1[i - 1] == lines2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    # Backtrack to create diff output
    diff_output = []
    i, j = m, n

    while i > 0 or j > 0:
        if i > 0 and j > 0 and lines1[i - 1] == lines2[j - 1]:
            diff_output.append(f"  {lines1[i - 1].rstrip()}")
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or dp[i][j] == dp[i - 1][j] + 1):
            diff_output.append(f"- {lines1[i - 1].rstrip()}")
            i -= 1
        elif j > 0 and (i == 0 or dp[i][j] == dp[i][j - 1] + 1):
            diff_output.append(f"+ {lines2[j - 1].rstrip()}")
            j -= 1
        else:
            diff_output.append(f"- {lines1[i - 1].rstrip()}")
            diff_output.append(f"+ {lines2[j - 1].rstrip()}")
            i -= 1
            j -= 1

    diff_output.reverse()
    return dp[m][n], "\n".join(diff_output)


def compute_file_similarity(file1_content, file2_content):
    """Compute similarity metrics between two files"""
    # Character-level Levenshtein distance
    char_distance, char_dp = levenshtein_distance(file1_content, file2_content)

    # Line-level Levenshtein distance
    lines1 = file1_content.splitlines()
    lines2 = file2_content.splitlines()
    line_distance, diff_output = diff_lines(lines1, lines2)

    # Calculate similarity percentage
    max_len = max(len(file1_content), len(file2_content))
    if max_len > 0:
        char_similarity = (1 - char_distance / max_len) * 100
    else:
        char_similarity = 100.0 if file1_content == file2_content else 0.0

    # Word-level comparison (simplified)
    words1 = file1_content.split()
    words2 = file2_content.split()
    word_distance, _ = levenshtein_distance(words1, words2)
    max_words = max(len(words1), len(words2))
    if max_words > 0:
        word_similarity = (1 - word_distance / max_words) * 100
    else:
        word_similarity = 100.0 if file1_content == file2_content else 0.0

    return {
        "char_distance": char_distance,
        "line_distance": line_distance,
        "word_distance": word_distance,
        "char_similarity": char_similarity,
        "word_similarity": word_similarity,
        "diff_output": diff_output,
        "lines1_count": len(lines1),
        "lines2_count": len(lines2),
        "chars1_count": len(file1_content),
        "chars2_count": len(file2_content),
    }


def show_edit_operations(str1, str2):
    """Show detailed edit operations between two strings"""
    distance, dp, ops, path = levenshtein_distance_with_path(str1, str2)

    print(f"Levenshtein Distance: {distance}")
    print("\nEdit Operations:")
    print("-" * 60)

    i_idx, j_idx = 0, 0
    step = 1

    for operation, i, j in path:
        if operation == EditOperation.MATCH:
            char1 = str1[i - 1] if i > 0 else ""
            char2 = str2[j - 1] if j > 0 else ""
            print(f"Step {step:2d}: Match      '{char1}' -> '{char2}'")
            i_idx += 1
            j_idx += 1
        elif operation == EditOperation.INSERT:
            char = str2[j - 1] if j > 0 else ""
            print(f"Step {step:2d}: Insert     '{char}' at position {i_idx}")
            j_idx += 1
        elif operation == EditOperation.DELETE:
            char = str1[i - 1] if i > 0 else ""
            print(f"Step {step:2d}: Delete     '{char}' at position {i_idx}")
            i_idx += 1
        elif operation == EditOperation.REPLACE:
            char1 = str1[i - 1] if i > 0 else ""
            char2 = str2[j - 1] if j > 0 else ""
            print(
                f"Step {step:2d}: Replace    '{char1}' -> '{char2}' at position {i_idx}"
            )
            i_idx += 1
            j_idx += 1
        step += 1

    return distance, dp, ops, path


def main():
    parser = argparse.ArgumentParser(
        description="Compare two text files and show edit distance (Levenshtein Distance)"
    )
    parser.add_argument("file1", help="First file to compare")
    parser.add_argument("file2", help="Second file to compare")
    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Show detailed edit operations for first differing line",
    )
    parser.add_argument(
        "-m",
        "--matrix",
        action="store_true",
        help="Show DP matrix for first 10x10 chars",
    )
    parser.add_argument(
        "-s", "--summary", action="store_true", help="Show only summary statistics"
    )

    args = parser.parse_args()

    try:
        # Read files
        with open(args.file1, "r", encoding="utf-8") as f1:
            content1 = f1.read()

        with open(args.file2, "r", encoding="utf-8") as f2:
            content2 = f2.read()

        # Compute similarities
        results = compute_file_similarity(content1, content2)

        if not args.summary:
            print(f"Comparing '{args.file1}' and '{args.file2}':")
            print("=" * 60)

            if not args.detailed:
                print(results["diff_output"])
                print("=" * 60)

        # Display summary
        print("\nEDIT DISTANCE SUMMARY:")
        print("-" * 60)
        print(f"Line-level edit distance: {results['line_distance']} operations")
        print(
            f"  (File 1: {results['lines1_count']} lines, File 2: {results['lines2_count']} lines)"
        )
        print()
        print(
            f"Character-level Levenshtein distance: {results['char_distance']} operations"
        )
        print(
            f"  (File 1: {results['chars1_count']} chars, File 2: {results['chars2_count']} chars)"
        )
        print(f"  Similarity: {results['char_similarity']:.2f}%")
        print()
        print(f"Word-level edit distance: {results['word_distance']} operations")
        print(f"  Similarity: {results['word_similarity']:.2f}%")

        # Show detailed operations for first differing line
        if args.detailed:
            lines1 = content1.splitlines()
            lines2 = content2.splitlines()

            for i in range(min(len(lines1), len(lines2))):
                if lines1[i] != lines2[i]:
                    print("\n" + "=" * 60)
                    print(f"DETAILED EDIT OPERATIONS FOR LINE {i + 1}:")
                    print(f"File 1: '{lines1[i]}'")
                    print(f"File 2: '{lines2[i]}'")
                    print()
                    show_edit_operations(lines1[i], lines2[i])
                    break
            else:
                if len(lines1) != len(lines2):
                    print("\n" + "=" * 60)
                    print("FILES HAVE DIFFERENT NUMBER OF LINES")

        # Show DP matrix sample
        if args.matrix:
            print("\n" + "=" * 60)
            print("DP MATRIX (first 10x10 characters):")
            print("-" * 60)

            sample1 = content1[:10]
            sample2 = content2[:10]
            distance, dp = levenshtein_distance(sample1, sample2)

            print("    ε  " + "  ".join(f"'{c}'" for c in sample2))
            for i in range(len(sample1) + 1):
                if i == 0:
                    row_label = "ε"
                else:
                    row_label = f"'{sample1[i - 1]}'"
                row_str = f"{row_label:4s} " + " ".join(
                    f"{dp[i][j]:2d}" for j in range(len(sample2) + 1)
                )
                print(row_str)

        # Final verdict
        print("\n" + "=" * 60)
        if results["char_distance"] == 0:
            print("FILES ARE IDENTICAL")
        elif results["char_similarity"] > 90:
            print("FILES ARE VERY SIMILAR")
        elif results["char_similarity"] > 70:
            print("FILES ARE MODERATELY SIMILAR")
        elif results["char_similarity"] > 30:
            print("FILES ARE SOMEWHAT DIFFERENT")
        else:
            print("FILES ARE VERY DIFFERENT")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
