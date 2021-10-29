from lexer_ttc import *
from codegen_ttc import *
from parser_ttc import *
import sys


def main():
    print("TUP Tiny Compiler")

    if len(sys.argv) != 2:
        sys.exit("Error: Compiler needs source file as argument.")
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    # Initialize the lexer, codegen, and parser.
    lexer = Lexer(input)
    codegen = CodeGen("TTC_Output/ttc_out.c")
    parser = Parser(lexer, codegen)

    parser.program()  # Start the parser.
    codegen.writeFile()  # Write the output to file.
    print("Compiling completed.")


main()
