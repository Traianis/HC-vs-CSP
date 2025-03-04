import sys
from CSP import start_csp
from HillClimbing import start_hc
if __name__ == '__main__':
    algoritm = sys.argv[1]
    input_file = sys.argv[2]
    if algoritm == "csp":
        start_csp(input_file)
    else:
        start_hc(input_file)
