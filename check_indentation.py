import tokenize
import sys

def check_indentation(filename):
    try:
        with tokenize.open(filename) as f:
            tokenize.generate_tokens(f.readline)
    except tokenize.TokenError as e:
        print(f"IndentationError in {filename}: {e}")
        return False
    except IndentationError as e:
        print(f"IndentationError in {filename} at line {e.lineno}: {e.msg}")
        return False
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if check_indentation(filename):
            print(f"No indentation errors found in {filename}.")
    else:
        print("Please provide a filename to check.")
