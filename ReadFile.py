# noinspection SpellCheckingInspection
#  Author:  Deanna M. Wilborne
# College:  Berea College
#  Course:  CSC386 Fall 2021
# Purpose:  Read in a file's lines
#
# History:
#           2024-02-05, DMW, updated for CSC420
#           2023-04-13, DMW, updated
#           2021-09-21, DMW, stronger typing hints added where appropriate
#           2021-09-08, DMW, created

class ReadFile:
    raw_data = []
    raw_text = ""
    raw_lines = 0
    error = False
    error_message = ""
    source_file_name = ""

    # this is the class constructor function
    def __init__(self, source_file_name: str = ""):
        # this code was added for REPL support
        if len(source_file_name) == 0:
            return

        self.read_file(source_file_name)

    def read_file(self, source_file_name: str) -> None:
        self.source_file_name = source_file_name
        try:
            source_file = open(source_file_name, "r")
            self.raw_text = source_file.read()
            source_file.close()
            self.raw_data = self.raw_text.splitlines()
            self.raw_lines = len(self.raw_data) # the number of source file lines
        except IOError as ex:
            self.error = True
            self.error_message = str(ex)


if __name__ == "__main__":
    # limited simple testing
    p = ReadFile("test-data.txt")
    print(p.raw_data)
    print(p.error)
    print(p.error_message)
