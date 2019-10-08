# CSCI 360 - Project 1
# Author: Emanuel Aracena
# Created on September 28, 2019

##
# Using code from file 'project_source_code_analyzer.py' given by Professor Xiaojie Zhang
##

import sys
import json


# Global declaration count to keep track of all declarations across functions
declaration = 1

# Keep track of labels made to presever unique names
label_count = 0

# int total(int num)


def read_head(line):
    words = [""]
    i = 0
    for char in line:
        if char != ' ' and char != '(' and char != ')' and char != ',':
            words[i] = words[i] + str(char)
            # print(words)
        else:
            words = words + [""]
            i = i + 1
            if char == ")":
                break
    return words


# int sum=0;
def read_declaration(line):
    global declaration
    words = ["", "", ""]
    i = 0
    for char in line:
        if char != ' ' and char != '=' and char != ';':
            words[i] = words[i] + str(char)
        else:
            i = i + 1
    declaration = declaration + 1
    obj = {
        "codeType": "declaration",
        "dataType": words[0],
        "dataName": words[1],
        "dataValue": words[2],
        "address": -(declaration * 4)
    }

    return obj


# sum=sum+num;
def read_logic(line):
    words = ["", "", "", ""]
    i = 0
    for char in line:
        if char == '+' or char == '-' or char == '/':
            i = i + 1
            words[i] = str(char)
            i = i + 1
        elif char != '=' and char != ';':
            words[i] = words[i] + str(char)
        else:
            i = i + 1
    obj = {
        "codeType": "logicOperation",
        "destination": words[0],
        "operand1": words[1],
        "operator": words[2],
        "operand2": words[3]
    }
    return obj


# read instructions recursively
def read_instruction(i, segment):
    instruction = []
    #print(segment)
    while i < len(segment):
        line = segment[i]
        if line == "}":
            break
        if line.startswith("int"):
            instruction.append(read_declaration(line))
            i = i + 1
        elif line.startswith("for"):
            result = read_for_loop(i, segment)
            instruction.append(result["for"])
            i = result["i"]
        elif line.startswith("if"):
            result = read_if(i, segment)
            instruction.append(result["if"])
            i = result["i"]
        elif line.startswith("else"):
            result = read_else(i, segment)
            instruction.append(result["else"])
            i = result["i"]
        elif line.startswith("return"):
            instruction.append(line)
            i = i + 1
        else:
            instruction.append(read_logic(line))
            i = i + 1
    return {"i": i + 1, "statement": instruction}

# if(num>10) {
# else {
def read_if(i, segment):
    line = segment[i]
    header = line[3:-2]

    obj = {
       "codeType": "if",
       "conditional": header,
       "statement": [],
    }
    i = i + 1
    result = read_instruction(i, segment)
    obj["statement"] = result["statement"]
    return {"i": result["i"], "if": obj}


# else
def read_else(i, segment):
    line = segment[i]
    obj = {
      "codeType": "else",
      "statement": []
    }
    i = i + 1
    result = read_instruction(i, segment)
    obj["statement"] = result["statement"]

    return {"i": result["i"], "else": obj}

   
# for(int i=0;i<num;i=i+1)
def read_for_loop(i, segment):
    line = segment[i]
    header = line[4:-2].split(';')
    obj = {"codeType": "for",
           "initialization": read_declaration(header[0]+";"),
           "termination": header[1],
           "increment": read_logic(header[2]+";"),
           "statement": []
           }
    i = i + 1
    result = read_instruction(i, segment)
    obj["statement"] = result["statement"]
    return {"i": result["i"], "for": obj}


# Read from file into line seperated strings in list called source
def read_source(filename):
  with open(filename) as file:
    source = file.readlines()
  
  # remove trailing whitespace and newlines
  source = [x.rstrip('\n') for x in source]
  source = [x.rstrip('\t') for x in source]
  source = [x.rstrip(' ') for x in source]  
  source = [x.lstrip('\t') for x in source]
  source = [x.lstrip(' ') for x in source]
  
  # remove all empty items
  source = [x for x in source if x != '']  

  # print(source)
  return source


# Main translation function
def translate(functions):
  
    print("")
    print("")

    for function in functions:
        # print seperator
        print("___________________________________________________")
        # Print function name
        print(function["functionName"] + ": ")
        
        # Declaration check
        num_of_declared = 0
        for instr in function["instruction"]:
            #print(instr)
            if "return" in instr:
                continue
            elif instr["codeType"] == "Declaration":
                num_of_declared = num_of_declared + 1
     
        # default prereserved space is 16 bytes
        if num_of_declared > 4:
            print("\tpush\trbp")
            print("\tsub\trsp, " + str((num_of_declared+2)*4))
        else:
            print("\tpush\trbp")
            print("\tmov\trbp, rsp") 
 
        # Create scope hash table to keep track of all declared variables/parameters
        scope = {}
    
        # Add parameters to scope
        for parameter in function["parameter"]:
            scope[parameter["dataName"]] =   "+" + str(-1*parameter["address"])
        
        #print(function["instruction"])
        # translate instructions
        for instruction in function["instruction"]:
            #print(instruction)
            if "return" in instruction:
                value = instruction.split(" ")[1].strip(";")
                if value in scope:
                    print("\tmov\teax, DWORD PTR[rbp" + str(scope[value]) + "]")
                    print("\tpop rbp")
                    print("\tret")
                else:
                    print("\tmov\teax, " + str(value))
                    print("\tpop rbp")
                    print("\tret")
                print("")
                break
    
            if instruction["codeType"] == "declaration":
                scope = translate_declaration(instruction, scope)
     
            if instruction["codeType"] == "logicOperation":
                translate_logic(instruction, scope) 
                  
            if instruction["codeType"] == "for":
                translate_for(instruction, scope)
                
            if instruction["codeType"] == "if":
                translate_if(instruction, scope)
    
            if instruction["codeType"] == "else":
                translate_else(instruction, scope) 



def translate_declaration(instruction, scope):
    # print(instruction)
    
    # add declaration to the scope
    scope[ instruction[ "dataName" ] ] = instruction["address"] 
    # print(scope)
    
    # if declaration instantly assigns value, translate immediately
    if instruction["dataValue"] != "":
        print("\tmov\tDWORD PTR [rbp" + str(instruction["address"]) + "], " + instruction["dataValue"] )

    return scope


def translate_logic(instruction, scope):
    # Set the assembly operator
    operator = ""
    # print(instruction)
    if instruction["operator"] == "+":
        operator = "add"
        
    if instruction["operator"] == "-":
        operator = "sub"
  
    if instruction["operator"] == "":
      if "(" in instruction["operand1"]:
          operator = "call"
      else:
          operator = "mov"
  
    # Print the assembly instruction 
    if operator == "add" or operator == "sub":
        if instruction["operand1"].strip(' ') in scope and instruction["operand2"].strip(' ') in scope:
            # mov eax, mem[operand2]
            # op mem[dest], eax
            print("\tmov\teax, DWORD PTR[rbp"+ str(scope[instruction["operand2"].strip(" ")]) + "]")
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], eax" )
        elif instruction["operand1"].strip(' ') in scope and instruction["operand2"].strip(' ') not in scope:
            # op mem[dest], num
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], " + instruction["operand2"].strip(" "))
              
    if operator == "mov":
        if instruction["operand1"].strip(" ") in scope: 
            print("\tmov\teax, DWORD PTR[rbp"+ str(scope[instruction["operand1"].strip(" ")]) + "]")
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], eax" )

        elif instruction["operand1"].strip(" ") not in scope:
            print("\t" + operator + "\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(' ')]) + "], " + instruction["operand1"] )
              
    if operator == "call":
        translate_call(instruction, scope)          
              



def translate_call(instruction, scope):
    # count number of arguments
    function_call = instruction["operand1"].strip(" ")
  
    # Split into substrings, until arguments seperated by commas remain,
    # then find the length of the list when split by commas
    # for example: f1(a, b, c) turns into a| b | c which has length 3
    num_of_args = len(function_call.split("(")[1].strip(")").split())
    arguments = function_call.split("(")[1].strip(")").split()
  
    # Theres only six registers for argument calling:
    # rdi, rsi, rdx, rcx, r8, r9
    # the rest are pushed to stack
    registers = ["rsi", "rdx", "rcx", "r8", "r9"]
  
    num_of_args = num_of_args - 1
    while num_of_args >= 0:
        if num_of_args > 4:
            # Push onto stack
            print("\tmov\tedi, DWORD PTR[rbp" + scope[arguments[num_of_args].strip(" ")] + "]") 
            print("\tpush\trdi")
        else:
            # Use registers
            print("\tmov\t"+ registers[num_of_args] + ", DWORD PTR[rbp" + str(scope[ arguments[num_of_args].strip(" ").strip(",")]) + "]")
                
        num_of_args = num_of_args - 1
         
    # make the call
    print("\tmov\trdi, eax")
    print("\tcall\t" + function_call)

    # move result to specified place
    print("\tmov\tDWORD PTR[rbp" + str(scope[instruction["destination"].strip(" ")]) + "], eax")


def translate_if(instruction, scope):
    global label_count
    jump_cmd = ""
    delimiter = ""
    # check the conditional
    if "==" in instruction["conditional"]:
        jump_cmd = "jne"
        delimiter = "=="
  
    if "<=" in instruction["conditional"]:
        jump_cmd = "jg"
        delimiter = "<="
  
    if ">=" in instruction["conditional"]:
        jump_cmd = "jl"
        delimiter = ">="
  
    if "<>" in instruction["conditional"]:
        jump_cmd = "je"
        delimiter = "<>"
  
    if "<" in instruction["conditional"]:
        jump_cmd = "jge"
        delimiter = "<"
  
    if ">" in instruction["conditional"]:
        jump_cmd = "jle"
        delimiter = ">"
  
    # Do the initial compare
    arguments = instruction["conditional"].strip("(").strip(")").split(delimiter)
    print("\tmov\teax, DWORD PTR[rbp" + str(scope[ arguments[0] ]) + "]")
    print("\tcmp\teax, DWORD PTR[rbp" + str(scope[arguments[1]]) + "]")
    print("\t" + jump_cmd + "\t.L" + str(label_count))
    
    # translate the instructions in the if statement

    for statement in instruction["statement"]:
        if "return" in statement:
            value = statement.split(" ")[1].strip(";")
            if value in scope:
                print("\tmov\teax, DWORD PTR[rbp" + str(scope[value]) + "]")
            else:
                print("\tmov\teax, " + str(value))
                print("\tpop rbp")
                print("\tret")
            break
    
    
        if statement["codeType"] == "declaration":
            scope = translate_declaration(statement, scope)
    
        if statement["codeType"] == "logicOperation":
            translate_logic(statement, scope) 
              
        if statement["codeType"] == "for":
            translate_for(statement, scope)
            
        if statement["codeType"] == "if":
            translate_if(statement, scope)

        if statement["codeType"] == "else":
            translate_else(statement, scope)

    # Print the unconditional jump
    print("\tjmp\t.L" + str(label_count+1))
    # Check if there is an else statement, and translate
    # the slice method prevents "else {" from getting treated like a logic operation
    # print(instruction["else"])
    print(".L" + str(label_count)+ ": ")
    label_count = label_count + 1
          
  
def translate_else(instruction, scope):
    global label_count
    for statement in instruction["statement"]:
        if "return" in statement:
            value = statement.split(" ")[1].strip(";")
            if value in scope:
                print("\tmov\teax, DWORD PTR[rbp" + str(scope[value]) + "]")
            else:
                print("\tmov\teax, " + str(value))
                print("\tpop rbp")
                print("\tret")
            break
    
    
        if statement["codeType"] == "declaration":
            scope = translate_declaration(statement, scope)
    
        if statement["codeType"] == "logicOperation":
            translate_logic(statement, scope) 
              
        if statement["codeType"] == "for":
            translate_for(statement, scope)
            
        if statement["codeType"] == "if":
            translate_if(statement, scope)

        if statement["codeType"] == "else":
            translate_else(statement, scope)

    # Print the unconditional jump
    #print("\tjmp\t.L" + str(label_count+1))
    # Check if there is an else statement, and translate
    # the slice method prevents "else {" from getting treated like a logic operation
    # print(instruction["else"])
    print(".L" + str(label_count)+ ":")
    label_count = label_count + 1



def translate_for(instruction, scope):
    global label_count
    scope = translate_declaration(instruction["initialization"], scope)
    operator = ""

    if "==" in instruction["termination"]:
        jump_cmd = "jne"
        delimiter = "=="
  
    if "<=" in instruction["termination"]:
        jump_cmd = "jg"
        delimiter = "<="
  
    if ">=" in instruction["termination"]:
        jump_cmd = "jl"
        delimiter = ">="
  
    if "<>" in instruction["termination"]:
        jump_cmd = "je"
        delimiter = "<>"
  
    if "<" in instruction["termination"]:
        jump_cmd = "jge"
        delimiter = "<"
  
    if ">" in instruction["termination"]:
        jump_cmd = "jle"
        delimiter = ">"

    print(".L" + str(label_count+1) + ":")
    arguments = instruction["termination"].split(delimiter)
    
    if arguments[0] in scope and arguments[1] in scope:
        print("\tmov\teax, DWORD PTR[rbp" + str(scope[arguments[0]]) + "]")
        print("\tcmp\teax, DWORD PTR[rbp" + str(scope[arguments[1]]) + "]")
    elif arguments[0] in scope and arguments[1] not in scope:
        print("\tcmp\tDWORD PTR[rbp" + str(scope[arguments[0]]) + "], " + str(arguments[1]))
    
    # print jump command
    print("\t" + jump_cmd + "\t.L" + str(label_count) )

    for statement in instruction["statement"]:
        if "return" in statement:
            value = statement.split(" ")[1].strip(";")
            if value in scope:
                print("\tmov\teax, DWORD PTR[rbp" + str(scope[value]) + "]")
            else:
                print("\tmov\teax, " + str(value))
                print("\tpop rbp")
                print("\tret")
            break
    
    
        if statement["codeType"] == "declaration":
            scope = translate_declaration(statement, scope)
    
        if statement["codeType"] == "logicOperation":
            translate_logic(statement, scope) 
              
        if statement["codeType"] == "for":
            translate_for(statement, scope)
            
        if statement["codeType"] == "if":
            translate_if(statement, scope)

        if statement["codeType"] == "else":
            translate_else(statement, scope)
    
    print("\tjmp\t.L" + str(label_count+1))
    print(".L" + str(label_count) + ":")
    label_count = label_count + 2


# Splash screen
def splash_screen():
    print(" _____________________________________________________________")
    print("|            CSCI Project 1 - x86_64 Assembly (Python)        |")
    print("|                   by Emanuel Aracena (solo)                 |")    
    print("|_____________________________________________________________|")
    

# print menu of choices
def print_choices():
    print("\t1. Load source file, and print JSON")
    print("\t2. Load source file, and print Assembly")
    print("\t3. Load source file, and print both JSON and Assembly")
    print("\t0. Quit")
    print("")


# Load file and just print JSON
def choice_1():
    filename = ""
    filename = input("Filename of source code (C++ only): ")
    function_list = ""
    function_list = parse_source(filename)
    print_JSON(function_list) 

# Load file and just print Assembly
def choice_2():
    filename = ""
    filename = input("Filename of source code (C++ only): ")
    function_list = ""
    function_list = parse_source(filename)
    translate(function_list)

# Load file and print JSON and Assembly
def choice_3():
    filename = ""
    filename = input("Filename of source code (C++ only): ")
    function_list = ""
    function_list = parse_source(filename)
    print_JSON(function_list)
    translate(function_list)


# parse source code into function list
def parse_source(filename):
    
    source = read_source(filename)
   
    # Seperate source code into functions
    unparsed_functions = []
    parenthesis_stack = 0
    inside_function = False
    function = []
    for line in source:
        # print(line," :\t\t", function, inside_function, ":\t\t", parenthesis_stack)
        if "{" in line and inside_function:
            parenthesis_stack = parenthesis_stack + 1;
            function.append(line)
          
        elif "{" in line and not inside_function:
            function.append(line)
            parenthesis_stack = parenthesis_stack + 1
            inside_function = True
   
        elif "}" in line:
            parenthesis_stack = parenthesis_stack - 1; 
            function.append(line)
            if parenthesis_stack == 0:
                unparsed_functions.append(function)
                function = []
                inside_function = False
   
        elif inside_function:
            function.append(line)
   
    # print(unparsed_functions)
   
    function_list = []
    for unparsed_function in unparsed_functions:
        function = {
            "returnType": "",
            "functionName": "",
            "parameter": [],
            "instruction": []
        }
   
        head = read_head(unparsed_function[0])
        
        function["returnType"] = head[0]
        function["functionName"] = head[1]
   
        # iterate over pairs parameter keywords
        i = 2
        while i+2 <= len(head)-1:
            global declaration
            param = {
                "type": head[i],
                "dataName": head[i+1],
                "codeType": "declaration",
                "address": -(declaration*4)
            }
            declaration = declaration + 1
            function["parameter"].append(param)
            i = i + 2
        
        # ignore the first line
        function["instruction"] = read_instruction(1, unparsed_function)["statement"]
        function_list.append(function)
        declaration = 1

    return function_list

def print_JSON(function_list):
    # Print the parsed JSON format of all the functions
    for function in function_list:
        # print seperator
        print("__________________________________________________________")
        result = json.dumps(function, indent=4)
        print(result)

# Main menu loop
def menu_loop():
    global label_count
    global declaration
    choice = ""
    while str(choice).strip("\n") != "0":
        # reset globals
        label_count = 0
        declaration = 1
        splash_screen()
        print_choices()
        choice = input("Choice: ")
        if choice == "1":
            choice_1()
        elif choice == "2":
            choice_2()
        elif choice == "3":
            choice_3()
  

# Main routine
def main():
    menu_loop()

main()
