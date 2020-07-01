import argparse
import os
from string import Template

sPushConstant = Template('@$number \n'
                         'D=A      \n'
                         '@SP      \n'
                         'AM=M+1   \n'
                         'A=A-1    \n'
                         'M=D      \n')

sPush = Template('@$base \n'
                 'D=${fixed_A_or_M} \n'
                 '@$index           \n'
                 'A=A+D             \n'
                 'D=M               \n'
                 '@SP               \n'
                 'AM=M+1            \n'
                 'A=A-1             \n'
                 'M=D               \n')

sPop = Template('@$base\n'
                'D=${fixed_A_or_M} \n'
                '@$index           \n'
                'D=D+A             \n'
                '@R13              \n'
                'M=D               \n'
                '@SP               \n'
                'AM=M-1            \n'
                'D=M               \n'
                '@R13              \n'
                'A=M               \n'
                'M=D               \n')

sEqGtLt = Template('@SP                 \n'
                   'AM=M-1                         \n'
                   'D=M                            \n'
                   'A=A-1                          \n'
                   'D=D-M                          \n'
                   'M=-1                           \n'
                   '@END$$${command}$$${uniquify}  \n'
                   'D;J${command}                  \n'
                   '@SP                            \n'
                   'A=M-1                          \n'
                   'M=0                            \n'
                   '(END$$${command}$$${uniquify}) \n')

memsegment2reg = {'constant': 'SP',
                  'local': 'LCL',
                  'argument': 'ARG',
                  'this': 'THIS',
                  'that': 'THAT',
                  'temp': 'R5',
                  'pointer': 'THIS',
                  'static': '16'}

vm2asm = {'add': '@SP \nAM=M-1 \nD=M \nA=A-1 \nM=D+M \n',
          'sub': '@SP \nAM=M-1 \nD=M \nA=A-1 \nM=M-D \n',
          'neg': '@SP \nA=M-1 \nM=-M \n',
          'and': '@SP \nAM=M-1 \nD=M \nA=A-1 \nM=D&M \n',
          'or': '@SP \nAM=M-1 \nD=M \nA=A-1 \nM=D|M \n',
                'not': '@SP \nA=M-1 \nM=!M \n',
                'push': sPush,
                'pop': sPop, }


class Parser:

    def __init__(self, fin):
        self.lines = open(fin).read().splitlines()
        self.lines = [line for line in self.lines
                      if len(line.strip())
                      and not line.startswith(('//', '/*'))]
        self.current_command = ''

    def hasMoreCommands(self):
        return len(self.lines) > 0

    def advance(self):
        self.current_command = self.lines.pop(0)

    def commandType(self):
        return self.current_command.split()[0]

    def arg1(self):
        return self.current_command.split()[1]

    def arg2(self):
        return self.current_command.split()[2]

    def commandTypeHasArg1(self, command_type):
        if command_type in ('push', 'pop'):
            return True

    def commandTypeHasArg2(self, command_type):
        if command_type in ('push', 'pop'):
            return True


class CodeWriter:

    def __init__(self, fou):
        self.fou = open(fou, 'w')
        self.cur_filename = ''
        self.label_uniques = {'eq': 0, 'gt': 0, 'lt': 0}

    def setFilename(self, filename, debug):
        """Inform the codewriter that a translation of
        a new VM file has started.
        """
        self.cur_filename = filename
        if debug:
            self.fou.write('/// ' + filename + '\n')
            self.cur_line = 0

    def writeComment(self, comment):
        self.fou.write('// ' + comment + '\n' +
                       '@'+str(self.cur_line) +
                       '\n@7777\nM=0\nM=1\n')
        self.cur_line += 1

    def writeArithmetic(self, command):
        if command in ('eq', 'gt', 'lt'):
            unique = self.label_uniques[command]
            self.label_uniques[command] += 1
        if command == 'gt':
            command = 'lt'  # 'gt' needs 'JLT' in .asm
        elif command == 'lt':
            command = 'gt'
            asm = sEqGtLt.substitute(command=command.upper(),
                                     uniquify=unique)
        else:
            asm = vm2asm[command]

        self.fou.write(asm)

    def writePushPop(self, command, segment, index):
        if segment == 'constant':
            asm = sPushConstant.substitute(number=index)
        else:
            asm = vm2asm[command]
            register = memsegment2reg[segment]
            fixed_A_or_M = 'A' if segment in ('temp', 'pointer') else 'M'
            asm = asm.substitute(base=register,
                                 index=index,
                                 fixed_A_or_M=fixed_A_or_M)
        self.fou.write(asm)

    def close(self):
        self.fou.close()


def main():
    argparser = argparse.ArgumentParser(description='VM translator')
    argparser.add_argument('filepath', help='(dir of) .vm file(s)')
    argparser.add_argument('-d', '--debug', action='store_true',
                           help='interleave .asm listing with comments')
    args = argparser.parse_args()
    fin = args.filepath

    if os.path.isdir(fin):
        vms = [file for file in os.listdir(
            fin) if os.path.splitext(file)[1] == '.vm']
        files = [(fin + file) for file in vms]
        fou = os.path.join(fin, 'out.asm')
    elif os.path.isfile(fin) and os.path.splitext(fin)[1] == '.vm':
        files = [fin]
        fou = os.path.splitext(fin)[0] + '.asm'
    else:
        print('Invalid filepath and/or not a .vm file')
        import sys
        sys.exit()

    writer = CodeWriter(fou)
    for file in files:
        writer.setFilename(os.path.basename(file), args.debug)
        parser = Parser(file)
        while parser.hasMoreCommands():
            parser.advance()
            if args.debug:
                writer.writeComment(parser.current_command)
            command_type = parser.commandType()

            arg1, arg2 = '', ''
            if parser.commandTypeHasArg1(command_type):
                arg1 = parser.arg1()
            if parser.commandTypeHasArg2(command_type):
                arg2 = parser.arg2()

            if command_type in ('push', 'pop'):
                writer.writePushPop(command_type, arg1, arg2)
            elif command_type in ('add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not'):
                writer.writeArithmetic(command_type)
    writer.close()


if __name__ == '__main__':
    main()
