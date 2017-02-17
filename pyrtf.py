"""
Rich Text Format Parser
"""

import os
import sys
import string


class RTFFile:

    def __init__(self, filename, debug=False):

        self.debug = debug
        self.filename = filename
        self.entities = list()

        self.__debug_print('[*] File: ' + filename)
        if os.path.isfile(filename) == False:
            raise Exception('Invalid File')

        self.__parse_rtf()


    def __parse_rtf(self):
        """parse RTF file"""

        content = open(self.filename, 'rb').read()

        if content[0:4] != '{\\rt':
            raise Exception('Invalid RTF Format')
        
        index = 0
        end_index = len(content)
        group_level = -1
        is_objdata = False
        
        while index < end_index:
            entity = dict()
            entity['offset'] = index

            if content[index] == '\\' and is_objdata == False:
                control_type, control_name, control_parameter, control_length = self.__analyze_control(content[index:])
                if control_name not in ['\'']:
                    entity['type'] = control_type
                    entity['content'] = content[index:index+control_length]
                    entity['name'] = control_name
                    entity['parameter'] = control_parameter
                    self.entities.append(entity)
                    self.__print_entity(index, entity)
                    index += control_length
                    if control_name == 'objdata':
                        is_objdata = True
                    continue

            if content[index] == '{' and is_objdata == False:
                group_level += 1
                entity['type'] = 'GroupBegin'
                entity['content'] = content[index]
                entity['level'] = group_level
                self.entities.append(entity)
                self.__print_entity(index, entity)
                index += 1
                continue 

            if content[index] == '}':
                entity['type'] = 'GroupEnd'
                entity['content'] = content[index]
                entity['level'] = group_level
                index += 1
                if index < end_index and content[index] == ' ':
                    index += 1
                elif index+1 < end_index and content[index:index+2] == '\x0d\x0a':
                    index += 2
                self.entities.append(entity)
                self.__print_entity(index, entity)
                group_level -= 1
                continue

            if group_level == -1 and index < end_index:
                entity['type'] = 'AppendData'
                entity['content'] = content[index:]
                self.entities.append(entity)
                self.__print_entity(index, entity)
                break

            i = 0
            entity['type'] = 'Data'
            entity['content'] = ''

            if is_objdata:
                while index+i < end_index:
                    if content[index+i] in '0123456789abcdefABCDEF':
                        entity['content'] += content[index+i]
                    elif content[index+i] == '}':
                        break
                    i += 1
                        
                is_objdata = False
            else:
                while index+i < end_index:
                    if content[index+i] == '\\':
                        if content[index+i+1] in ['{', '}', '\\']:
                            entity['content'] += content[index+i+1]
                            i += 2
                        elif content[index+i+1] == '\'':
                            entity['content'] += content[index+i+2:index+i+4].decode('hex')
                            i += 4
                        else:
                            break
                    elif content[index+i] in ['{', '}']:
                        break
                    else:
                        entity['content'] += content[index+i]
                        i += 1
            
            self.entities.append(entity)
            self.__print_entity(index, entity)
            index += i


    def __analyze_control(self, control):
        """analyze control entity"""

        control_type = 'Unknown'
        control_name = ''
        control_parameter = ''
        control_length = 1
        
        if control[1] in string.ascii_letters:
            control_type = 'ControlWord'
            control_name += control[1]
            i = 2
            while True:
                if control[i] in string.ascii_letters:
                    control_name += control[i]
                    i += 1
                else:
                    break

            if control[i] == '-':
                control_parameter = '-'
                i += 1

            while True:
                if control[i] in string.digits:
                    control_parameter += control[i]
                    i += 1
                else:
                    break

            if control[i] == ' ':
                i += 1
            elif control[i:i+2] == '\x0d\x0a':
                i += 2
            
            control_length = i
            
        elif control[1] not in string.ascii_letters + string.digits:
            control_type = 'ControlSymbol'
            control_name = control[1]
            control_length = 2

        return control_type, control_name, control_parameter, control_length



    def __print_entity(self, index, entity):
        """print entity information"""

        self.__debug_print('[*] Index: ' + str(index))
        for key, value in entity.items():
            self.__debug_print('  [+] ' + key + ': ' + str(value))


    def __debug_print(self, message):
        """print debug information"""

        if self.debug:
            print message


if __name__ == '__main__':

    if len(sys.argv) == 2:
        rtffile = RTFFile(sys.argv[1], debug=True)
        for entity in rtffile.entities:
            print entity
    else:
        print 'Usage: ' + os.path.basename(sys.argv[0]) + ' file.rtf'
        