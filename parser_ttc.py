import sys
from lexer_ttc import *

# Parser object keeps track of current token, checks if the code matches the grammar, and emits code along the way.


class Parser:
    def __init__(self, lexer, codegen):
        self.lexer = lexer
        self.codegen = codegen

        self.symbols = set()    # All variables we have declared so far.
        self.labelsDeclared = set()  # Keep track of all labels declared
        # All labels goto'ed, so we know if they exist or not.
        self.labelsGotoed = set()

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()    # Call this twice to initialize current and peek.

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name +
                       ", got " + self.curToken.kind.name)
        self.nextToken()

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # No need to worry about passing the EOF, lexer handles that.

    # Return true if the current token is a comparison operator.
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

    def abort(self, message):
        sys.exit("Error! " + message)

    # Production rules.

    # program ::= {statement}

    def program(self):
        self.codegen.headerLine("#include <stdio.h>")
        self.codegen.headerLine("int main(void){")

        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program.
        while not self.checkToken(TokenType.EOF):
            self.statement()

        # Wrap things up.
        self.codegen.genLine("return 0;")
        self.codegen.genLine("}")

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    # One of the following statements...

    def statement(self):
        # Check the first token to see what kind of statement this is.

        # "PRINT" (expression | string)
        if self.checkToken(TokenType.PRINT):
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                # Simple string, so print it.
                self.codegen.genLine(
                    "printf(\"" + self.curToken.text + "\\n\");")
                self.nextToken()

            else:
                # Expect an expression and print the result as a float.
                self.codegen.generatec("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                self.codegen.genLine("));")

        # "IF" comparison "THEN" block "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.codegen.generatec("if(")
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()
            self.codegen.genLine("){")

            # Zero or more statements in the body.
            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.codegen.genLine("}")

        # "WHILE" comparison "REPEAT" block "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.codegen.generatec("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()
            self.codegen.genLine("){")

            # Zero or more statements in the loop body.
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.codegen.genLine("}")

        # "LABEL" ident
        elif self.checkToken(TokenType.LABEL):
            self.nextToken()

            # Make sure this label doesn't already exist.
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.codegen.genLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.codegen.genLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)

        # "LET" ident = expression
        elif self.checkToken(TokenType.LET):
            self.nextToken()

            #  Check if ident exists in symbol table. If not, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.codegen.headerLine("float " + self.curToken.text + ";")

            self.codegen.generatec(self.curToken.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()
            self.codegen.genLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            # If variable doesn't already exist, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.codegen.headerLine("float " + self.curToken.text + ";")

            # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            self.codegen.genLine(
                "if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
            self.codegen.genLine(self.curToken.text + " = 0;")
            self.codegen.generatec("scanf(\"%")
            self.codegen.genLine("*s\");")
            self.codegen.genLine("}")
            self.match(TokenType.IDENT)

        # This is not a valid statement. Error!
        else:
            self.abort("Invalid statement at " + self.curToken.text +
                       " (" + self.curToken.kind.name + ")")

        # Newline.
        self.nl()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+

    def comparison(self):
        self.expression()
        # Must be at least one comparison operator and another expression.
        if self.isComparisonOperator():
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
            self.expression()
        # Can have 0 or more comparison operator and expressions.
        while self.isComparisonOperator():
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
            self.expression()

    # expression ::= term {( "-" | "+" ) term}

    def expression(self):
        self.term()
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
            self.term()

    # term ::= unary {( "/" | "*" ) unary}

    def term(self):
        self.unary()
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
            self.unary()

    # unary ::= ["+" | "-"] primary

    def unary(self):
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
        self.primary()

    # primary ::= number | ident

    def primary(self):
        if self.checkToken(TokenType.NUMBER):
            self.codegen.generatec(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.symbols:
                self.abort(
                    "Referencing variable before assignment: " + self.curToken.text)

            self.codegen.generatec(self.curToken.text)
            self.nextToken()
        else:
            # Error!
            self.abort("Unexpected token at " + self.curToken.text)

    # nl ::= '\n'+
    def nl(self):
        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()
