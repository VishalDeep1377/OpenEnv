import re

def test_regex():
    params_str = " email_id='e1' label='URGENT'"
    regex = r"(\w+)=(['\"]?)(.*?)\2(?=\s|$)"
    params = {}
    param_matches = re.finditer(regex, params_str)
    for m in param_matches:
        params[m.group(1)] = m.group(3)
    print(f"Quoted: {params}")

    params_str_no_quotes = " email_id=e1 label=URGENT"
    params = {}
    param_matches = re.finditer(regex, params_str_no_quotes)
    for m in param_matches:
        params[m.group(1)] = m.group(3)
    print(f"Unquoted: {params}")

    params_str_mixed = " email_id=e1 label='SPAM'"
    params = {}
    param_matches = re.finditer(regex, params_str_mixed)
    for m in param_matches:
        params[m.group(1)] = m.group(3)
    print(f"Mixed: {params}")

if __name__ == "__main__":
    test_regex()
